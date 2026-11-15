#!/usr/bin/env python3
"""
advance-cursor.py
Idempotent state transition helper for System Design Studio.
Atomically updates manifest.json, CURSOR.md, and CURRICULUM.md when a topic is completed,
an example is logged, a question is deferred, or a lesson artifact is generated.
"""

import os
import sys
import json
import re
import argparse
import datetime
import shutil
import tempfile

def atomic_write(filepath, content, is_json=False):
    dirname = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(dirname, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dirname, delete=False, encoding="utf-8") as tf:
        if is_json:
            json.dump(content, tf, indent=2, ensure_ascii=False)
        else:
            tf.write(content)
        temp_name = tf.name
    os.replace(temp_name, filepath)

def extract_cluster_reality_checks(inst_dir, cluster_code):
    curriculum_path = os.path.join(inst_dir, "CURRICULUM.md")
    if os.path.exists(curriculum_path):
        try:
            with open(curriculum_path, "r", encoding="utf-8") as f:
                content = f.read()
            pat = r"##\s+(?:🔁\s*)?\d+\.\s*\[" + re.escape(cluster_code) + r"\][\s\S]*?### Reality Check[^\n]*\n+([\s\S]*?)(?:\n---|\n##\s|\Z)"
            m = re.search(pat, content)
            if m:
                block = m.group(1)
                items = re.findall(r"-\s*\[\s*\]\s*(.*?)(?:\s*—\s*\*Tick off when:|\n|$)", block)
                clean_items = [it.strip() for it in items if it.strip()]
                if clean_items:
                    return [f'{i+1}. *"{q}"*' for i, q in enumerate(clean_items[:2])]
        except Exception:
            pass
    return [
        '1. *"Explain the core invariant and causal failure boundary cold without notes."*',
        '2. *"Derive the quantitative trade-off or latency impact when the primary assumption fails."*'
    ]

def main():
    parser = argparse.ArgumentParser(description="Advance System Design Studio cursor state")
    parser.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")
    parser.add_argument("--complete-topic", help="Topic ID to mark completed (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--evidence", help="Evidence text demonstrating mastery")
    parser.add_argument("--log-example-domain", help="Example domain name (e.g. Financial Ledger)")
    parser.add_argument("--log-example-scenario", help="Concrete scenario description")
    parser.add_argument("--log-example-tradeoffs", nargs="*", default=[], help="Tradeoffs exposed by this example")
    parser.add_argument("--defer-topic", help="Topic description to defer")
    parser.add_argument("--defer-target-cluster", help="Target cluster ID for deferred topic")
    parser.add_argument("--defer-anchor-note", help="Note explaining why deferred and what unlocks it")
    parser.add_argument("--resolve-defer-id", help="Deferred topic ID to mark resolved")
    parser.add_argument("--next-topic-id", help="Next active topic ID")
    parser.add_argument("--next-action", help="Next teaching action description")
    parser.add_argument("--backward-anchor", help="Updated backward anchor description")
    parser.add_argument("--forward-hook", help="Updated forward hook description")
    parser.add_argument("--lesson-artifact", help="Path to generated interactive HTML lesson artifact")

    args = parser.parse_args()
    inst_dir = args.instance_dir

    # Resolve cursor and lessons directory preferences from settings.json if present
    abs_inst = os.path.abspath(inst_dir)
    base_dir = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst

    raw_cursor_dir = None
    raw_lessons_dir = None
    settings_path = os.path.join(inst_dir, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as sf:
                s = json.load(sf)
                paths_cfg = s.get("paths", {})
                raw_cursor_dir = paths_cfg.get("cursorDir") or s.get("cursorDir")
                raw_lessons_dir = paths_cfg.get("lessonsDir") or s.get("lessonsDir")
        except Exception:
            pass

    if raw_cursor_dir:
        if os.path.isabs(raw_cursor_dir):
            cursor_dir = raw_cursor_dir
        else:
            cursor_dir = os.path.normpath(os.path.join(base_dir, raw_cursor_dir))
    else:
        cursor_dir = inst_dir

    if raw_lessons_dir:
        if os.path.isabs(raw_lessons_dir):
            lessons_dir = raw_lessons_dir
        else:
            lessons_dir = os.path.normpath(os.path.join(base_dir, raw_lessons_dir))
    else:
        lessons_dir = os.path.join(inst_dir, "lessons")

    manifest_path = os.path.join(inst_dir, "manifest.json")
    cursor_path = os.path.join(cursor_dir, "CURSOR.md")
    curriculum_path = os.path.join(inst_dir, "CURRICULUM.md")

    if not os.path.exists(manifest_path):
        print(f"Error: manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = datetime.date.today().isoformat()
    manifest["lastUpdated"] = now_iso

    # 1. Complete topic
    completed_topic_title = None
    if args.complete_topic:
        for cluster in manifest["curriculum"]["clusters"]:
            for topic in cluster["topics"]:
                if topic["id"] == args.complete_topic:
                    topic["status"] = "completed"
                    completed_topic_title = topic["title"]
                    concept_id = f"concept.{args.complete_topic.replace('topic.', '')}"
                    if concept_id not in manifest["runningContext"]["coveredConcepts"]:
                        manifest["runningContext"]["coveredConcepts"].append(concept_id)
                    if args.lesson_artifact:
                        topic["lessonArtifact"] = f"lessons/{os.path.basename(args.lesson_artifact)}"

        if args.evidence:
            ev_id = f"evidence.{args.complete_topic.replace('topic.', '')}.{today_str}"
            manifest["evidence"].append({
                "id": ev_id,
                "topicId": args.complete_topic,
                "type": "verified-explanation",
                "demonstratedClaim": args.evidence,
                "date": today_str
            })

    # Copy lesson artifact if supplied
    if args.lesson_artifact and os.path.exists(args.lesson_artifact):
        os.makedirs(lessons_dir, exist_ok=True)
        dest_filename = os.path.basename(args.lesson_artifact)
        dest_path = os.path.join(lessons_dir, dest_filename)
        if os.path.abspath(args.lesson_artifact) != os.path.abspath(dest_path):
            shutil.copy2(args.lesson_artifact, dest_path)

    # 2. Log example
    if args.log_example_domain and args.log_example_scenario:
        ex_id = f"example.{len(manifest['runningContext']['examplesTaken']) + 1:02d}.{re.sub(r'[^a-zA-Z0-9]+', '-', args.log_example_domain.lower()).strip('-')}"
        manifest["runningContext"]["examplesTaken"].append({
            "id": ex_id,
            "conceptId": f"concept.{args.complete_topic.replace('topic.', '')}" if args.complete_topic else "concept.general",
            "domain": args.log_example_domain,
            "scenario": args.log_example_scenario,
            "tradeoffsExposed": args.log_example_tradeoffs,
            "date": today_str
        })

    # 3. Deferred Queue
    if args.defer_topic:
        def_id = f"defer.{len(manifest['runningContext']['deferredQueue']) + 1:02d}.{re.sub(r'[^a-zA-Z0-9]+', '-', args.defer_topic.lower()).strip('-')[:30]}"
        manifest["runningContext"]["deferredQueue"].append({
            "id": def_id,
            "topic": args.defer_topic,
            "originConceptId": f"concept.{args.complete_topic.replace('topic.', '')}" if args.complete_topic else "concept.general",
            "targetClusterId": args.defer_target_cluster or "cluster.general",
            "anchorNote": args.defer_anchor_note or "Deferred to target cluster",
            "status": "pending"
        })

    if args.resolve_defer_id:
        for item in manifest["runningContext"]["deferredQueue"]:
            if item["id"] == args.resolve_defer_id:
                item["status"] = "resolved"

    # 4. Advance Cursor Target
    if args.next_topic_id:
        manifest["curriculum"]["activeTopicId"] = args.next_topic_id
        manifest["cursor"]["topicFoundationId"] = f"foundation.{args.next_topic_id.replace('topic.', '')}"
        manifest["cursor"]["topicFoundationStatus"] = "not-started"

        for cluster in manifest["curriculum"]["clusters"]:
            for topic in cluster["topics"]:
                if topic["id"] == args.next_topic_id:
                    manifest["curriculum"]["activeClusterId"] = cluster["id"]
                    manifest["cursor"]["activeMechanismGroupId"] = f"group.{args.next_topic_id.replace('topic.', '')}"

    if args.next_action:
        manifest["cursor"]["nextTeachingAction"] = args.next_action

    if args.backward_anchor:
        manifest["cursor"]["backwardAnchor"] = args.backward_anchor

    if args.forward_hook:
        manifest["cursor"]["forwardHook"] = args.forward_hook

    # 5. Tick off in CURRICULUM.md if complete_topic passed
    if args.complete_topic and os.path.exists(curriculum_path) and completed_topic_title:
        with open(curriculum_path, "r", encoding="utf-8") as f:
            c_lines = f.readlines()
        new_lines = []
        for line in c_lines:
            if re.search(r"-\s*\[\s*\]\s*" + re.escape(completed_topic_title), line):
                new_lines.append(re.sub(r"-\s*\[\s*\]", "- [x]", line, count=1))
            else:
                new_lines.append(line)
        atomic_write(curriculum_path, "".join(new_lines))

    # 6. Save manifest atomically
    atomic_write(manifest_path, manifest, is_json=True)

    # 7. Re-render CURSOR.md atomically
    active_cluster_id = manifest["curriculum"]["activeClusterId"]
    active_topic_id = manifest["curriculum"]["activeTopicId"]

    active_cluster = None
    active_topic = None
    for c in manifest["curriculum"]["clusters"]:
        if c["id"] == active_cluster_id:
            active_cluster = c
            for t in c["topics"]:
                if t["id"] == active_topic_id:
                    active_topic = t
                    break
            break

    if not active_cluster:
        active_cluster = manifest["curriculum"]["clusters"][0]
    if not active_topic:
        active_topic = active_cluster["topics"][0]

    completed_topics = sum(
        1 for c in manifest["curriculum"]["clusters"] for t in c["topics"] if t["status"] == "completed"
    )
    total_topics = sum(len(c["topics"]) for c in manifest["curriculum"]["clusters"])
    pct = (completed_topics / total_topics * 100) if total_topics > 0 else 0

    examples_md = ""
    for ex in manifest["runningContext"]["examplesTaken"]:
        tradeoffs = ", ".join(ex.get("tradeoffsExposed", []))
        examples_md += f"- **{ex['domain']}**: {ex['scenario']}"
        if tradeoffs:
            examples_md += f" *(Exposes: {tradeoffs})*"
        examples_md += f" — `{ex['date']}`\n"
    if not examples_md:
        examples_md = "*(None logged yet)*\n"

    deferred_md = ""
    for d in manifest["runningContext"]["deferredQueue"]:
        if d.get("status") == "pending":
            deferred_md += f"- **{d['topic']}** (`{d['id']}`): Target: `{d['targetClusterId']}`. *Anchor*: {d['anchorNote']}\n"
    if not deferred_md:
        deferred_md = "*(Queue currently empty)*\n"

    cluster_topics_md = ""
    for t in active_cluster["topics"]:
        box = "[x]" if t["status"] == "completed" else "[ ]"
        is_cur = " **CURRENT** ➔" if t["id"] == active_topic_id else ""
        cluster_topics_md += f"- {box}{is_cur} **{t['title']}** (`{t['id']}`)\n"

    cluster_code = active_cluster.get("code") or active_cluster["id"].replace("cluster.", "")
    rc_questions = extract_cluster_reality_checks(inst_dir, cluster_code)
    rc_md = "\n".join(f"    {q}" for q in rc_questions)

    cursor_md = f"""# Living Teaching Cursor & Running Context

> **Role**: The operational brain of this learning instance. Tracks active focus, causal continuity, depth of covered mechanisms, examples & mental models, deferred topics, and upcoming forward hooks across sessions, models, and agents. The Cursor and Curriculum are the sole shared context.

---

## 1. Active Focus & Immediate Pedagogical Horizon

- **Curriculum**: {manifest['curriculum']['title']} (`{manifest['curriculum']['id']}`)
- **Active Cluster**: {active_cluster['title']} (`{active_cluster['id']}`)
  - *Cluster Reality Checks*:
{rc_md}
- **Active Topic**: **{active_topic['title']}** (`{active_topic['id']}`)
  - *Topic Foundation Status*: `{manifest['cursor']['topicFoundationStatus']}`
  - *Active Mechanism Group*: `{manifest['cursor']['activeMechanismGroupId']}`
  - *Last Checkpoint*: `{manifest['cursor']['lastCheckpointId']}` (Status: `{manifest['cursor']['lastCheckpointStatus']}`)
  - *Immediate Next Teaching Action*: {manifest['cursor']['nextTeachingAction']}

---

## 2. Connected Cognitive Lineage (Causal Anchors)

- **Backward Anchor (Where we came from & Why)**:
  - {manifest['cursor'].get('backwardAnchor', 'Grounding in physical network realities.')}
- **Forward Hook (Where this leads next)**:
  - {manifest['cursor'].get('forwardHook', 'Connecting to the next protocol layer.')}

---

## 3. Examples Registry & Metaphor Continuity (`examplesTaken`)

{examples_md}
---

## 4. Deferred Topics Queue (`deferredQueue`)

{deferred_md}
---

## 5. Active Cluster Progress: {active_cluster['title']}

{cluster_topics_md}
---

## Progress Overview: {completed_topics} / {total_topics} Topics ({pct:.1f}%)
"""

    atomic_write(cursor_path, cursor_md)

    print(f"✅ Cursor advanced! Active topic: {active_topic['title']}")
    print(f"   Progress: {completed_topics}/{total_topics} ({pct:.1f}%)")

if __name__ == "__main__":
    main()
