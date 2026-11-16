#!/usr/bin/env python3
"""
sync-status.py
Diagnostic tool for System Design Studio learning instances.
Reads .system-design/manifest.json and .system-design/settings.json,
reporting active focus, running context, artifact style preference, and deferred queue health.
"""

import os
import sys
import json
import argparse

def resolve_instance_dir(raw_path=None):
    if raw_path:
        expanded = os.path.expanduser(raw_path)
        if os.path.isdir(os.path.join(expanded, ".system-design")):
            return os.path.join(expanded, ".system-design")
        return expanded

    cwd_inst = os.path.abspath(".system-design")
    if os.path.isdir(cwd_inst) and os.path.isfile(os.path.join(cwd_inst, "manifest.json")):
        return cwd_inst

    curr = os.getcwd()
    while True:
        candidate = os.path.join(curr, ".system-design")
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "manifest.json")):
            return candidate
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    reg_path = os.path.expanduser("~/.system-design-studio/projects.json")
    if os.path.isfile(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
            active_id = reg.get("activeProjectId")
            for p in reg.get("projects", []):
                if p.get("id") == active_id:
                    cand = os.path.join(os.path.expanduser(p.get("projectPath", "")), ".system-design")
                    if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "manifest.json")):
                        return cand
        except Exception:
            pass

    return ".system-design"

def main():
    parser = argparse.ArgumentParser(description="Diagnostic tool for System Design Studio learning instances.")
    parser.add_argument("pos_instance_dir", nargs="?", default=None, help="Path to .system-design directory (positional)")
    parser.add_argument("--instance-dir", default=None, help="Path to .system-design directory")
    args = parser.parse_args()

    raw_dir = args.instance_dir or args.pos_instance_dir
    instance_dir = resolve_instance_dir(raw_dir)
    manifest_path = os.path.join(instance_dir, "manifest.json")
    settings_path = os.path.join(instance_dir, "settings.json")

    if not os.path.exists(manifest_path):
        print(f"❌ No System Design Studio instance found at '{instance_dir}/'. Run init-learning-instance.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        m = json.load(f)

    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as sf:
                settings = json.load(sf)
        except Exception:
            pass

    curriculum = m.get("curriculum", {})
    cursor = m.get("cursor", {})
    rc = m.get("runningContext", {})

    total_topics = sum(len(c.get("topics", [])) for c in curriculum.get("clusters", []))
    completed_topics = sum(1 for c in curriculum.get("clusters", []) for t in c.get("topics", []) if t.get("status") == "completed")
    pct = (completed_topics / total_topics * 100) if total_topics else 0.0

    active_cluster_id = curriculum.get("activeClusterId", "none")
    active_topic_id = curriculum.get("activeTopicId", "none")

    active_cluster = next((c for c in curriculum.get("clusters", []) if c["id"] == active_cluster_id), None)
    active_topic = next((t for t in active_cluster.get("topics", []) if t["id"] == active_topic_id), None) if active_cluster else None

    print("=" * 60)
    print(f"🧠 SYSTEM DESIGN STUDIO — INSTANCE DIAGNOSTIC")
    print("=" * 60)
    print(f"Instance Name:   {m.get('instanceName', 'Unknown')}")
    print(f"Curriculum Track: {settings.get('track', 'full-mastery')} ({curriculum.get('title', 'Unknown')})")
    print(f"Output Mode:     {settings.get('outputType', 'html')} | Theme: {settings.get('artifactStyle', 'slate-clean')}")
    print(f"Study Notes:     {settings.get('paths', {}).get('notesDir', 'notes')} ({settings.get('notesStructure', 'per-topic')})")
    print(f"Overall Progress: {completed_topics} / {total_topics} Topics ({pct:.1f}%)")
    style_val = settings.get("artifactStyle", "slate-clean")
    abs_inst = os.path.abspath(instance_dir)
    base_dir = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst

    paths_cfg = settings.get("paths", {})
    raw_cursor_dir = paths_cfg.get("cursorDir") or settings.get("cursorDir")
    raw_lessons_dir = paths_cfg.get("lessonsDir") or settings.get("lessonsDir")

    if raw_cursor_dir:
        if os.path.isabs(raw_cursor_dir):
            cursor_path = os.path.join(raw_cursor_dir, "CURSOR.md")
        else:
            cursor_path = os.path.normpath(os.path.join(base_dir, raw_cursor_dir, "CURSOR.md"))
    else:
        cursor_path = os.path.join(instance_dir, "CURSOR.md")

    if raw_lessons_dir:
        if os.path.isabs(raw_lessons_dir):
            lessons_dir = raw_lessons_dir
        else:
            lessons_dir = os.path.normpath(os.path.join(base_dir, raw_lessons_dir))
    else:
        lessons_dir = os.path.join(instance_dir, "lessons")

    print(f"Artifact Style:  {style_val}")
    print(f"Cursor Path:     {cursor_path}")
    print(f"Lessons Dir:     {lessons_dir}/")
    print("-" * 60)
    print(f"Active Cluster:  {active_cluster.get('title', active_cluster_id) if active_cluster else active_cluster_id}")
    print(f"Active Topic:    {active_topic.get('title', active_topic_id) if active_topic else active_topic_id}")
    print(f"Foundation:      {cursor.get('topicFoundationStatus', 'unknown')}")
    print(f"Mechanism Group: {cursor.get('activeMechanismGroupId', 'none')}")
    print("-" * 60)
    print(f"Examples Logged: {len(rc.get('examplesTaken', []))}")
    if rc.get("examplesTaken"):
        last_ex = rc["examplesTaken"][-1]
        print(f"  └─ Latest: [{last_ex.get('domain')}] {last_ex.get('scenario')[:60]}...")
    print(f"Deferred Queue:  {len([d for d in rc.get('deferredQueue', []) if d.get('status') == 'pending'])} pending questions")
    if rc.get("deferredQueue"):
        pending = [d for d in rc["deferredQueue"] if d.get("status") == "pending"]
        if pending:
            print(f"  └─ Next Due: [{pending[0].get('targetClusterId')}] {pending[0].get('topic')[:60]}")
    print("-" * 60)
    print(f"Immediate Next Action:\n  👉 {cursor.get('nextTeachingAction', 'None')}")
    print("=" * 60)

    # Check for available updates (non-blocking, cached)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    check_script = os.path.join(script_dir, "check-updates.py")
    if os.path.exists(check_script):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("check_updates", check_script)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            chk = mod.check_for_updates(force=False, instance_dir=instance_dir)
            if chk.get("updateAvailable"):
                print("")
                print(f"🔔 UPDATE AVAILABLE: System Design Studio v{chk.get('remoteVersion')} is ready (current: v{chk.get('currentVersion')})")
                print("   Run: curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash")
                print("   (Safely preserves all your progress, notes, and custom settings)")
        except Exception:
            pass

if __name__ == "__main__":
    main()
