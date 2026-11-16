#!/usr/bin/env python3
"""
configure-curriculum.py
Curriculum Track Generator, Pruner, and Restructuring Engine for System Design Studio.
Generates tailored CURRICULUM.md and manifest.json for curated goals (Interview Sprint,
Distributed Infrastructure, Staff Architect, Mobile/Offline, Full Mastery) or custom filter/reorder criteria.
Strictly adheres to Tier > Cluster > Topic taxonomy.
"""

import os
import sys
import re
import json
import argparse
import datetime

TRACK_DEFINITIONS = {
    "interview-sprint": {
        "id": "interview-sprint",
        "name": "Short-Term Interview Sprint (2-4 Weeks)",
        "description": "High-yield essentials: Transport, Core DB & Caching, Key LLD Patterns, and Classic Distributed HLD Systems.",
        "targetTiers": ["0", "1", "2"],
        "targetClusters": ["0.1", "0.2", "0.3", "0.4", "0.5", "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "2.7", "2.10"]
    },
    "distributed-systems": {
        "id": "distributed-systems",
        "name": "Distributed Systems & Storage Infrastructure (6-12 Weeks)",
        "description": "Exhaustive deep dive into storage engines, consensus protocols, replication, distributed transactions, and fault tolerance.",
        "targetTiers": ["0", "2"],
        "targetClusters": None # All clusters in Tier 0 and Tier 2
    },
    "staff-architect": {
        "id": "staff-architect",
        "name": "Staff+ / Principal Architecture & System Defense",
        "description": "High-level distributed architectures, multi-region active-active, capacity planning, cost modeling, and Tier 4 ADR system defenses.",
        "targetTiers": ["0", "2", "4"],
        "targetClusters": None
    },
    "mobile-offline": {
        "id": "mobile-offline",
        "name": "Mobile & Offline-First Systems (3-6 Weeks)",
        "description": "Client architecture, local persistence, delta sync engines, CRDTs, background workers, battery/network throttling, and offline queues.",
        "targetTiers": ["0", "3"],
        "targetClusters": None
    },
    "full-mastery": {
        "id": "full-mastery",
        "name": "Full 50-Cluster Systems Mastery (Comprehensive)",
        "description": "The complete 50-cluster syllabus across all 5 engineering tiers from transport mechanics to board-level ADR defense.",
        "targetTiers": ["0", "1", "2", "3", "4"],
        "targetClusters": None
    }
}

def parse_curriculum_template(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    tiers = []
    current_tier = None
    current_cluster = None
    
    tier_rx = re.compile(r'^#\s+Tier\s+(\d+|[A-Z0-9]+)\s*[:—\-]\s*(.+)$', re.IGNORECASE)
    cluster_rx = re.compile(r'^##\s+(?:[🔁\s]*(\d+)\.\s*\[([^\]]+)\]\s*(.+))$')
    topic_rx = re.compile(r'^-\s*\[([ xX])\]\s*(.+)$')

    tier_order = 0
    in_atomic = False
    has_sections = False
    for idx, line in enumerate(lines):
        st = line.strip()
        m_t = tier_rx.match(st)
        if m_t:
            tier_order += 1
            code = m_t.group(1).strip()
            name = m_t.group(2).strip()
            current_tier = {
                "code": code,
                "title": name,
                "order": tier_order,
                "header_lines": [line],
                "clusters": []
            }
            tiers.append(current_tier)
            current_cluster = None
            continue

        m_c = cluster_rx.match(st)
        if m_c and current_tier:
            c_order = int(m_c.group(1))
            c_code = m_c.group(2).strip()
            c_title = m_c.group(3).strip()
            current_cluster = {
                "order": c_order,
                "code": c_code,
                "title": c_title,
                "tierCode": current_tier["code"],
                "raw_lines": [line],
                "topics": []
            }
            current_tier["clusters"].append(current_cluster)
            in_atomic = False
            has_sections = False
            continue

        if current_cluster:
            current_cluster["raw_lines"].append(line)
            if st.startswith("###"):
                in_atomic = "atomic" in st.lower()
                has_sections = True
                continue

            m_top = topic_rx.match(st)
            if m_top:
                raw_topic = m_top.group(2).strip()
                if has_sections and not in_atomic:
                    continue
                if raw_topic.startswith("📖") or raw_topic.startswith("🛠️"):
                    continue
                t_parts = re.split(r'\s*(?:—|--)\s*', raw_topic, maxsplit=1)
                t_title = t_parts[0].strip()
                t_id = f"topic.{current_cluster['code']}.{re.sub(r'[^a-zA-Z0-9]+', '-', t_title.lower()).strip('-')[:40]}"
                current_cluster["topics"].append({
                    "id": t_id,
                    "title": t_title,
                    "status": "unseen"
                })

    return tiers

def build_filtered_curriculum(tiers, track_key=None, include_tiers=None, exclude_tiers=None, include_clusters=None, reorder_codes=None):
    track = TRACK_DEFINITIONS.get(track_key) if track_key else None
    
    selected_tiers = list(include_tiers) if include_tiers else (track["targetTiers"] if track and track.get("targetTiers") else None)
    selected_clusters = set(include_clusters) if include_clusters else (set(track["targetClusters"]) if track and track.get("targetClusters") else None)

    filtered_tiers = []

    for t in tiers:
        if selected_tiers is not None and t["code"] not in selected_tiers:
            continue
        if exclude_tiers and t["code"] in exclude_tiers:
            continue

        tier_copy = dict(t)
        tier_clusters = []
        for c in t["clusters"]:
            if selected_clusters is not None and c["code"] not in selected_clusters:
                continue
            tier_clusters.append(c)

        if tier_clusters:
            tier_copy["clusters"] = tier_clusters
            filtered_tiers.append(tier_copy)

    # Reorder clusters if requested
    if reorder_codes:
        cluster_map = {c["code"]: c for t in filtered_tiers for c in t["clusters"]}
        ordered_clusters = [cluster_map[code] for code in reorder_codes if code in cluster_map]
        remaining = [c for c in cluster_map.values() if c["code"] not in reorder_codes]
        # Re-pack into tiers
        final_clusters = ordered_clusters + remaining
        for t in filtered_tiers:
            t["clusters"] = [c for c in final_clusters if c["tierCode"] == t["code"]]

    return filtered_tiers

def export_curriculum(filtered_tiers, title, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "lessons"), exist_ok=True)

    curriculum_lines = [
        f"# {title}\n",
        f"> **Custom Track Generation**: Generated on {datetime.date.today().isoformat()} via System Design Studio.\n",
        "---\n"
    ]

    manifest_clusters = []
    cluster_order = 1

    for t in filtered_tiers:
        curriculum_lines.append(f"\n# Tier {t['code']} — {t['title']}\n")
        for c in t["clusters"]:
            curriculum_lines.extend(c["raw_lines"])
            curriculum_lines.append("\n---\n")

            manifest_clusters.append({
                "id": f"cluster.{c['code']}",
                "code": c["code"],
                "title": f"{c['order']}. [{c['code']}] {c['title']}",
                "order": cluster_order,
                "tierId": f"tier.{t['code']}",
                "topics": c["topics"]
            })
            cluster_order += 1

    # Write CURRICULUM.md
    curriculum_path = os.path.join(output_dir, "CURRICULUM.md")
    with open(curriculum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(curriculum_lines))

    # Write manifest.json
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    first_cluster = manifest_clusters[0] if manifest_clusters else None
    first_topic = first_cluster["topics"][0] if first_cluster and first_cluster["topics"] else None

    manifest = {
        "$schemaVersion": "3.2",
        "instanceName": title,
        "createdAt": now_iso,
        "lastUpdated": now_iso,
        "curriculum": {
            "id": f"curriculum.{re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:30]}",
            "title": title,
            "source": "curated-track",
            "sourceRef": ".system-design/CURRICULUM.md",
            "activeClusterId": first_cluster["id"] if first_cluster else None,
            "activeTopicId": first_topic["id"] if first_topic else None,
            "clusters": manifest_clusters
        },
        "cursor": {
            "version": 1,
            "lastTickTimestamp": now_iso,
            "activeClusterCode": first_cluster["code"] if first_cluster else "none",
            "activeClusterName": first_cluster["title"] if first_cluster else "none",
            "activeTier": f"Tier {filtered_tiers[0]['code']}" if filtered_tiers else "Tier 0",
            "activeTopic": first_topic["title"] if first_topic else "none",
            "topicFoundationId": f"foundation.{first_topic['id'].replace('topic.', '')}" if first_topic else "foundation.none",
            "topicFoundationStatus": "not-started",
            "activeMechanismGroupId": f"group.{first_topic['id'].replace('topic.', '')}" if first_topic else "group.none",
            "nextTeachingAction": f"Start foundational inquiry on {first_topic['title']}" if first_topic else "Review curriculum",
            "backwardAnchor": "Track initialized via configure-curriculum.py",
            "forwardHook": f"Connect foundational invariants to {first_topic['title']}" if first_topic else "Prepare initial lesson"
        },
        "runningContext": {
            "coveredConcepts": [],
            "examplesTaken": [],
            "deferredQueue": [],
            "causalAnchors": []
        },
        "evidence": []
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    total_topics = sum(len(c["topics"]) for c in manifest_clusters)
    print(f"✅ Generated tailored curriculum track: '{title}'")
    print(f"   • Tiers:    {len(filtered_tiers)}")
    print(f"   • Clusters: {len(manifest_clusters)}")
    print(f"   • Topics:   {total_topics}")
    print(f"   • Files:    {curriculum_path}, {manifest_path}")

def main():
    parser = argparse.ArgumentParser(description="Configure, prune, or select curriculum tracks for System Design Studio")
    parser.add_argument("--template", help="Path to CURRICULUM-template.md")
    parser.add_argument("--track", choices=list(TRACK_DEFINITIONS.keys()), help="Curated track name")
    parser.add_argument("--include-tiers", help="Comma-separated tier codes to include (e.g. 0,1,2)")
    parser.add_argument("--exclude-tiers", help="Comma-separated tier codes to exclude")
    parser.add_argument("--include-clusters", help="Comma-separated cluster codes to include (e.g. 0.1,0.2,1.3)")
    parser.add_argument("--reorder", help="Comma-separated cluster codes in desired sequence")
    parser.add_argument("--output-dir", default=".system-design", help="Target output instance directory")
    parser.add_argument("--title", help="Custom curriculum title")
    parser.add_argument("--list-tracks", action="store_true", help="List available curated tracks")

    args = parser.parse_args()

    if args.list_tracks:
        print("=" * 76)
        print("  SYSTEM DESIGN STUDIO — CURATED GOAL TRACKS")
        print("=" * 76)
        for k, v in TRACK_DEFINITIONS.items():
            print(f"🎯 Track: {k}")
            print(f"   Name:        {v['name']}")
            print(f"   Description: {v['description']}")
            print(f"   Tiers:       {', '.join(v['targetTiers'])}")
            print("-" * 76)
        return

    # Find template
    template_path = args.template
    if not template_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cand = os.path.join(script_dir, "..", "resources", "CURRICULUM-template.md")
        if os.path.exists(cand):
            template_path = cand
        else:
            print("❌ Error: CURRICULUM-template.md not found.", file=sys.stderr)
            sys.exit(1)

    tiers = parse_curriculum_template(template_path)

    inc_tiers = [x.strip() for x in args.include_tiers.split(",")] if args.include_tiers else None
    exc_tiers = [x.strip() for x in args.exclude_tiers.split(",")] if args.exclude_tiers else None
    inc_clusters = [x.strip() for x in args.include_clusters.split(",")] if args.include_clusters else None
    reorder_codes = [x.strip() for x in args.reorder.split(",")] if args.reorder else None

    filtered = build_filtered_curriculum(tiers, args.track, inc_tiers, exc_tiers, inc_clusters, reorder_codes)

    track_info = TRACK_DEFINITIONS.get(args.track) if args.track else None
    title = args.title or (track_info["name"] if track_info else "Custom System Design Curriculum")

    export_curriculum(filtered, title, args.output_dir)

if __name__ == "__main__":
    main()
