#!/usr/bin/env python3
"""
import-curriculum.py
Bring-Your-Own-Curriculum (BYO) adapter for System Design Studio.
Parses any custom markdown syllabus and scaffolds a fully-functional, 
idempotent .system-design/ learning instance.
"""

import os
import sys
import re
import json
import argparse
import datetime

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s]+', '-', text)[:40]

def parse_markdown_curriculum(file_path, default_title=None):
    if not os.path.exists(file_path):
        print(f"Error: file not found at {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    title = default_title
    clusters = []
    current_cluster = None
    cluster_order = 1
    topic_counter = 1

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Top level title if not set
        if not title and stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            continue

        # Cluster heading (## Cluster or # Cluster)
        cluster_match = re.match(r'^(?:##\s+|#\s+)(.+)$', stripped)
        if cluster_match and (not title or stripped[2:].strip() != title):
            cluster_name = cluster_match.group(1).strip()
            cluster_id = f"cluster.{cluster_order}.{slugify(cluster_name)}"
            current_cluster = {
                "id": cluster_id,
                "code": str(cluster_order),
                "title": cluster_name,
                "order": cluster_order,
                "topics": []
            }
            clusters.append(current_cluster)
            cluster_order += 1
            continue

        # Topic detection: either ### Topic or - [ ] Topic
        topic_match = re.match(r'^(?:###\s+|- \[[ x]\]\s+)(.+)$', stripped)
        if topic_match:
            if not current_cluster:
                current_cluster = {
                    "id": f"cluster.{cluster_order}.general",
                    "code": str(cluster_order),
                    "title": "General System Design",
                    "order": cluster_order,
                    "topics": []
                }
                clusters.append(current_cluster)
                cluster_order += 1

            topic_name = topic_match.group(1).strip()
            # Clean tick-off rules if embedded
            topic_clean = re.sub(r'—\s*\*?Tick off.*$', '', topic_name).strip()
            topic_id = f"topic.{current_cluster['code']}.{slugify(topic_clean)}"
            
            # Avoid duplicate topic IDs
            if any(t["id"] == topic_id for t in current_cluster["topics"]):
                topic_id = f"{topic_id}-{topic_counter}"
                topic_counter += 1

            current_cluster["topics"].append({
                "id": topic_id,
                "title": topic_clean,
                "status": "unseen"
            })

    if not title:
        title = "Custom System Design Curriculum"

    # Filter out empty clusters
    clusters = [c for c in clusters if len(c["topics"]) > 0]
    return title, clusters

def main():
    parser = argparse.ArgumentParser(description="Import custom markdown syllabus into System Design Studio")
    parser.add_argument("--input", required=True, help="Path to markdown curriculum file")
    parser.add_argument("--instance-dir", default=".system-design", help="Instance directory path")
    parser.add_argument("--title", help="Custom instance title override")
    parser.add_argument("--domain", default="Custom Engineering Domain", help="Primary engineering domain focus")

    args = parser.parse_args()
    title, clusters = parse_markdown_curriculum(args.input, args.title)

    if not clusters:
        print("Error: No clusters or topics could be parsed from the file.", file=sys.stderr)
        sys.exit(1)

    inst_dir = args.instance_dir
    lessons_dir = os.path.join(inst_dir, "lessons")
    os.makedirs(lessons_dir, exist_ok=True)

    first_cluster = clusters[0]
    first_topic = first_cluster["topics"][0]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Manifest
    manifest = {
        "$schemaVersion": "2.0",
        "instanceName": title,
        "createdAt": now_iso,
        "lastUpdated": now_iso,
        "curriculum": {
            "id": f"curriculum.{slugify(title)}",
            "title": title,
            "source": "custom-byo-markdown",
            "sourceRef": args.input,
            "activeClusterId": first_cluster["id"],
            "activeTopicId": first_topic["id"],
            "clusters": clusters
        },
        "cursor": {
            "topicFoundationId": f"foundation.{first_topic['id'].replace('topic.', '')}",
            "topicFoundationStatus": "not-started",
            "activeMechanismGroupId": f"group.{first_topic['id'].replace('topic.', '')}",
            "lastCheckpointId": "none",
            "lastCheckpointStatus": "none",
            "nextTeachingAction": f"Deliver Topic 1.1 Foundation for {first_topic['title']} as an interactive HTML artifact.",
            "backwardAnchor": "Grounding in fundamental systems engineering physics.",
            "forwardHook": "Connecting to the next protocol layer.",
            "flagshipDomain": args.domain
        },
        "runningContext": {
            "coveredConcepts": [],
            "examplesTaken": [],
            "deferredQueue": []
        },
        "evidence": []
    }

    manifest_path = os.path.join(inst_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2. CURRICULUM.md
    curr_md = f"# {title}\n\n"
    curr_md += f"> **Source**: Custom Import from `{args.input}` · Initialized {now_iso}\n\n---\n\n"
    for c in clusters:
        curr_md += f"## {c['title']} (`{c['id']}`)\n\n"
        for t in c["topics"]:
            curr_md += f"- [ ] **{t['title']}** (`{t['id']}`) — *Tick off when: demonstrated with causal proof and reality check.*\n"
        curr_md += "\n"

    curr_path = os.path.join(inst_dir, "CURRICULUM.md")
    with open(curr_path, "w", encoding="utf-8") as f:
        f.write(curr_md)

    # 3. CURSOR.md
    cursor_md = f"""# Living Teaching Cursor & Running Context

> **Role**: The operational brain of this learning instance. Tracks active focus, causal continuity, depth of covered mechanisms, examples & mental models, deferred topics, and upcoming forward hooks across sessions, models, and agents. The Cursor and Curriculum are the sole shared context.

---

## 1. Active Focus & Immediate Pedagogical Horizon

- **Curriculum**: {title} (`curriculum.{slugify(title)}`)
- **Active Cluster**: {first_cluster['title']} (`{first_cluster['id']}`)
- **Active Topic**: **{first_topic['title']}** (`{first_topic['id']}`)
  - *Topic Foundation Status*: `not-started`
  - *Active Mechanism Group*: `group.{first_topic['id'].replace('topic.', '')}`
  - *Primary Flagship Domain*: `{args.domain}`
  - *Immediate Next Teaching Action*: Deliver Topic 1.1 Foundation for {first_topic['title']} as an interactive HTML artifact.

---

## 2. Connected Cognitive Lineage (Causal Anchors)

- **Backward Anchor (Where we came from & Why)**:
  - Grounding in fundamental systems engineering physics and hardware realities.
- **Forward Hook (Where this leads next)**:
  - Establishing baseline mechanics before introducing distributed partitions.

---

## 3. Examples Registry & Metaphor Continuity (`examplesTaken`)

*(No examples logged yet)*

---

## 4. Deferred Topics Queue (`deferredQueue`)

*(Queue currently empty)*

---

## 5. Active Cluster Progress: {first_cluster['title']}

"""
    for t in first_cluster["topics"]:
        is_cur = " **CURRENT** ➔" if t["id"] == first_topic["id"] else ""
        cursor_md += f"- [ ]{is_cur} **{t['title']}** (`{t['id']}`)\n"

    total_topics = sum(len(c["topics"]) for c in clusters)
    cursor_md += f"\n---\n\n## Progress Overview: 0 / {total_topics} Topics (0.0%)\n"

    cursor_path = os.path.join(inst_dir, "CURSOR.md")
    with open(cursor_path, "w", encoding="utf-8") as f:
        f.write(cursor_md)

    # 4. DECISIONS.md
    dec_path = os.path.join(inst_dir, "DECISIONS.md")
    if not os.path.exists(dec_path):
        with open(dec_path, "w", encoding="utf-8") as f:
            f.write("# Architecture Decision Records (ADRs)\n\n*No decisions accepted yet. Decisions will be recorded as architectural trade-offs are evaluated and defended in workshops.*\n")

    print(f"🎉 Successfully imported custom curriculum '{title}'!")
    print(f"   Clusters: {len(clusters)}")
    print(f"   Total Topics: {total_topics}")
    print(f"   Scaffolded instance at: {inst_dir}/")

if __name__ == "__main__":
    main()
