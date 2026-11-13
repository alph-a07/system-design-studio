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
    manifest_path = os.path.join(inst_dir, "manifest.json")
    cursor_path = os.path.join(inst_dir, "CURSOR.md")
    curriculum_path = os.path.join(inst_dir, "CURRICULUM.md")

    if not os.path.exists(manifest_path):
        print(f"Error: manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
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
        lessons_dir = os.path.join(inst_dir, "lessons")
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

    # Clean legacy objects if present
    manifest["runningContext"].pop("notion", None)
    manifest["runningContext"].pop("drawBoard", None)
    manifest["runningContext"].pop("visualBackend", None)

    # Save manifest.json
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # 5. Update CURRICULUM.md checkbox if topic completed
    if completed_topic_title and os.path.exists(curriculum_path):
        with open(curriculum_path) as f:
            curr_content = f.read()

        escaped_title = re.escape(completed_topic_title)
        pattern = rf"- \[ \] (\s*{escaped_title}\b)"
        curr_content = re.sub(pattern, r"- [x] \1", curr_content, count=1)

        with open(curriculum_path, "w") as f:
            f.write(curr_content)

    # 6. Regenerate CURSOR.md
    active_cluster_id = manifest["curriculum"]["activeClusterId"]
    active_topic_id = manifest["curriculum"]["activeTopicId"]

    active_cluster = next((c for c in manifest["curriculum"]["clusters"] if c["id"] == active_cluster_id), manifest["curriculum"]["clusters"][0])
    active_topic = next((t for t in active_cluster["topics"] if t["id"] == active_topic_id), active_cluster["topics"][0])

    total_topics = sum(len(c["topics"]) for c in manifest["curriculum"]["clusters"])
    completed_topics = sum(1 for c in manifest["curriculum"]["clusters"] for t in c["topics"] if t["status"] == "completed")
    pct = (completed_topics / total_topics * 100) if total_topics else 0

    examples_md = ""
    if manifest["runningContext"]["examplesTaken"]:
        for ex in manifest["runningContext"]["examplesTaken"]:
            examples_md += f"- **{ex['domain']}** (`{ex['id']}`): {ex['scenario']}\n"
            if ex.get("tradeoffsExposed"):
                for to in ex["tradeoffsExposed"]:
                    examples_md += f"  - *Tradeoff*: {to}\n"
    else:
        examples_md = "*(No examples logged yet)*\n"

    deferred_md = ""
    pending_def = [d for d in manifest["runningContext"]["deferredQueue"] if d["status"] == "pending"]
    if pending_def:
        for d in pending_def:
            deferred_md += f"- **{d['topic']}** (`{d['id']}`): Target: `{d['targetClusterId']}`. *Anchor*: {d['anchorNote']}\n"
    else:
        deferred_md = "*(Queue currently empty)*\n"

    cluster_topics_md = ""
    for t in active_cluster["topics"]:
        box = "[x]" if t["status"] == "completed" else "[ ]"
        is_cur = " **CURRENT** ➔" if t["id"] == active_topic_id else ""
        cluster_topics_md += f"- {box}{is_cur} **{t['title']}** (`{t['id']}`)\n"

    cursor_md = f"""# Living Teaching Cursor & Running Context

> **Role**: The operational brain of this learning instance. Tracks active focus, causal continuity, depth of covered mechanisms, examples & mental models, deferred topics, and upcoming forward hooks across sessions, models, and agents. The Cursor and Curriculum are the sole shared context.

---

## 1. Active Focus & Immediate Pedagogical Horizon

- **Curriculum**: {manifest['curriculum']['title']} (`{manifest['curriculum']['id']}`)
- **Active Cluster**: {active_cluster['title']} (`{active_cluster['id']}`)
  - *Cluster Reality Checks*:
    1. *"For each provider API Anchor calls, do you know whether it paginates by page number, cursor or link header — and what your loop does if the list shifts mid-fetch?"*
    2. *"Explain how a retry after a timeout can double-charge without an idempotency key. Where exactly is the ambiguity: client, network, or server?"*
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

    with open(cursor_path, "w") as f:
        f.write(cursor_md)

    print(f"✅ Cursor advanced! Active topic: {active_topic['title']}")
    print(f"   Progress: {completed_topics}/{total_topics} ({pct:.1f}%)")

if __name__ == "__main__":
    main()
