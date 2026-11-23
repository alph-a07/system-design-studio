#!/usr/bin/env python3
"""
verify-instance.py
Automated health-check and integrity verification for System Design Studio instances.
Validates manifest schemas, cursor lineage consistency, curriculum checkbox counts,
settings.json configuration, directory preferences (cursorDir, lessonsDir), and HTML lesson artifacts.
"""

import os
import sys
import json
import re

def verify_instance(instance_dir=".system-design"):
    if os.path.isdir(os.path.join(instance_dir, ".system-design")):
        instance_dir = os.path.join(instance_dir, ".system-design")

    errors = []
    warnings = []
    passes = []

    print(f"🔍 Verifying System Design Studio instance at: {instance_dir}")

    # 1. Settings Schema Validation & Path Resolution
    settings_path = os.path.join(instance_dir, "settings.json")
    settings = {}
    if os.path.exists(settings_path):
        passes.append("File exists: settings.json")
        try:
            with open(settings_path) as sf:
                settings = json.load(sf)
            passes.append("settings.json is valid JSON")
            style = settings.get("artifactStyle")
            valid_styles = ["slate-clean", "editorial-paper", "midnight-neon", "nordic-frost", "warm-amber"]
            if style in valid_styles:
                passes.append(f"settings.json defines recognized artifactStyle '{style}'")
            else:
                warnings.append(f"settings.json artifactStyle '{style}' not in standard roster ({valid_styles})")

            out_fmt = settings.get("outputType", "html")
            if out_fmt == "html":
                passes.append("settings.json defines valid outputType 'html'")
            else:
                warnings.append(f"settings.json defines outputType '{out_fmt}' (lessons are strictly rendered as interactive 'html')")

            struct = settings.get("notesStructure", "per-topic")
            valid_structs = ["per-topic", "per-cluster", "per-tier", "single-file"]
            if struct in valid_structs:
                passes.append(f"settings.json defines valid notesStructure '{struct}'")
            else:
                warnings.append(f"settings.json notesStructure '{struct}' not in ({valid_structs})")
        except json.JSONDecodeError as e:
            errors.append(f"settings.json has JSON syntax error: {e}")
    else:
        warnings.append("Optional or legacy instance missing settings.json (defaults will be used)")

    # Resolve project base directory vs instance directory
    abs_inst = os.path.abspath(instance_dir)
    base_dir = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst

    def resolve_configured_dir(configured_val, default_rel):
        if not configured_val:
            return os.path.join(instance_dir, default_rel)
        if os.path.isabs(configured_val):
            return configured_val
        cand_base = os.path.join(base_dir, configured_val)
        if os.path.exists(cand_base):
            return cand_base
        cand_inst = os.path.join(instance_dir, configured_val)
        if os.path.exists(cand_inst):
            return cand_inst
        return cand_base

    paths_cfg = settings.get("paths", {})
    raw_cursor_dir = paths_cfg.get("cursorDir") or settings.get("cursorDir")
    raw_lessons_dir = paths_cfg.get("lessonsDir") or settings.get("lessonsDir")

    cursor_dir = resolve_configured_dir(raw_cursor_dir, "")
    lessons_dir = resolve_configured_dir(raw_lessons_dir, "lessons")

    # 2. Directory Structure & Required Files
    req_files = [
        ("manifest.json", os.path.join(instance_dir, "manifest.json")),
        ("CURSOR.md", os.path.join(cursor_dir, "CURSOR.md")),
        ("CURRICULUM.md", os.path.join(instance_dir, "CURRICULUM.md")),
        ("DECISIONS.md", os.path.join(instance_dir, "DECISIONS.md")),
    ]
    for label, p in req_files:
        if os.path.exists(p):
            passes.append(f"File exists: {label}")
        else:
            errors.append(f"Missing required file: {p}")

    if os.path.isdir(lessons_dir):
        passes.append(f"Directory exists: lessons/ ({lessons_dir})")
    else:
        errors.append(f"Missing lessons directory: {lessons_dir}")

    manifest_path = os.path.join(instance_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print("\n❌ CRITICAL: Cannot continue verification without manifest.json")
        for err in errors:
            print(f"  ❌ {err}")
        sys.exit(1)

    # 3. Manifest Schema Validation
    with open(manifest_path) as mf:
        try:
            m = json.load(mf)
            passes.append("manifest.json is valid JSON")
        except json.JSONDecodeError as e:
            errors.append(f"manifest.json has JSON syntax error: {e}")
            m = {}

    for k in ["instanceName", "curriculum", "cursor", "runningContext", "evidence"]:
        if k in m:
            passes.append(f"manifest root key '{k}' present")
        else:
            errors.append(f"manifest missing required root key '{k}'")

    if "$schemaVersion" in m or "schemaVersion" in m:
        passes.append("manifest schema version present")
    else:
        errors.append("manifest missing schemaVersion key")

    curriculum = m.get("curriculum", {})
    clusters = curriculum.get("clusters", [])
    if clusters:
        passes.append(f"Curriculum contains {len(clusters)} clusters")
    else:
        errors.append("Curriculum has zero clusters")

    total_manifest_topics = sum(len(c.get("topics", [])) for c in clusters)
    completed_manifest_topics = sum(1 for c in clusters for t in c.get("topics", []) if t.get("status") == "completed")
    passes.append(f"Manifest tracks {total_manifest_topics} total topics ({completed_manifest_topics} completed)")

    active_cluster_id = curriculum.get("activeClusterId")
    active_topic_id = curriculum.get("activeTopicId")

    found_cluster = any(c.get("id") == active_cluster_id for c in clusters)
    found_topic = any(t.get("id") == active_topic_id for c in clusters for t in c.get("topics", []))

    if found_cluster:
        passes.append(f"Active cluster '{active_cluster_id}' exists in curriculum")
    else:
        errors.append(f"Active cluster '{active_cluster_id}' not found in curriculum clusters")

    if found_topic:
        passes.append(f"Active topic '{active_topic_id}' exists in curriculum")
    else:
        errors.append(f"Active topic '{active_topic_id}' not found in curriculum topics")

    # 4. Check CURRICULUM.md parity
    curriculum_path = os.path.join(instance_dir, "CURRICULUM.md")
    if os.path.exists(curriculum_path):
        with open(curriculum_path) as cf:
            curr_txt = cf.read()
        checked_boxes = len(re.findall(r"- \[x\]", curr_txt))
        unchecked_boxes = len(re.findall(r"- \[ \]", curr_txt))
        total_boxes = checked_boxes + unchecked_boxes
        passes.append(f"CURRICULUM.md contains {total_boxes} checkboxes ({checked_boxes} checked, {unchecked_boxes} unchecked)")

        if checked_boxes == completed_manifest_topics:
            passes.append("CURRICULUM.md checked count matches manifest completed topic count")
        else:
            warnings.append(f"CURRICULUM.md checked count ({checked_boxes}) != manifest completed count ({completed_manifest_topics})")

    # 5. Check CURSOR.md (located in cursor_dir)
    cursor_path = os.path.join(cursor_dir, "CURSOR.md")
    if os.path.exists(cursor_path):
        with open(cursor_path) as cur_f:
            cur_txt = cur_f.read()
        if active_topic_id in cur_txt:
            passes.append(f"CURSOR.md contains active topic '{active_topic_id}'")
        else:
            warnings.append(f"CURSOR.md does not explicitly mention active topic ID '{active_topic_id}'")

        if "{{LESSON_" in cur_txt or "{{TOPIC_" in cur_txt:
            errors.append("CURSOR.md contains unrendered template placeholders")
        else:
            passes.append("CURSOR.md is free of unrendered template tokens")

    # 6. Check Lessons Directory (located in lessons_dir)
    if os.path.isdir(lessons_dir):
        lesson_files = [f for f in os.listdir(lessons_dir) if f.endswith(".html")]
        passes.append(f"Found {len(lesson_files)} HTML lesson artifacts in lessons/ ({lessons_dir})")
        for lf in lesson_files:
            lfp = os.path.join(lessons_dir, lf)
            with open(lfp) as lff:
                content = lff.read()
            if "<!DOCTYPE html>" in content and "</html>" in content:
                passes.append(f"Artifact {lf} is valid HTML document")
            else:
                errors.append(f"Artifact {lf} appears malformed or missing HTML wrapper")

    # Output Summary
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    for p in passes:
        print(f"  ✅ {p}")
    for w in warnings:
        print(f"  ⚠️  {w}")
    for e in errors:
        print(f"  ❌ {e}")
    print("=" * 60)

    if errors:
        print(f"\n❌ FAILED with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return False
    else:
        print(f"\n✨ PASSED with 0 errors and {len(warnings)} warning(s). Instance is healthy!")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automated health-check and integrity verification for System Design Studio instances.")
    parser.add_argument("pos_instance_dir", nargs="?", default=None, help="Path to .system-design directory (positional)")
    parser.add_argument("--instance-dir", default=None, help="Path to .system-design directory")
    args = parser.parse_args()

    target = args.instance_dir or args.pos_instance_dir or ".system-design"
    success = verify_instance(target)
    sys.exit(0 if success else 1)
