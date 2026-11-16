#!/usr/bin/env python3
"""
import-curriculum.py
Bring-Your-Own-Curriculum (BYO) Validator and Adapter for System Design Studio.
Strictly enforces the 3-level taxonomy: Tier (Level 1) > Cluster (Level 2) > Topic (Level 3) + Sign-Off Gate.
Parses, validates, and generates a fully-functional .system-design/ learning instance.
"""

import os
import sys
import re
import json
import argparse
import datetime

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s]+', '-', text)[:45]

def validate_and_parse_curriculum(file_path, default_title=None, auto_fix=False):
    """
    Validates and parses markdown curriculum enforcing Tier > Cluster > Topic taxonomy.
    Returns (title, tiers, clusters, errors, warnings)
    """
    if not os.path.exists(file_path):
        return None, None, None, [f"File not found: {file_path}"], []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    errors = []
    warnings = []
    
    title = default_title
    tiers = []
    clusters = []

    current_tier = None
    current_cluster = None
    
    tier_counter = 0
    cluster_counter = 0
    topic_counter = 0

    tier_regex = re.compile(r'^#\s+(?:Tier\s+(\d+|[A-Z0-9]+)\s*[:—\-]\s*(.+)|Tier\s+(\d+|[A-Z0-9]+)\b(.*))$', re.IGNORECASE)
    doc_title_regex = re.compile(r'^#\s+([^#\n]+)$')
    cluster_regex = re.compile(r'^##\s+(?:[🔁\s]*(\d+)\.\s*\[([^\]]+)\]\s*(.+)|(?:Cluster\s+([0-9\.]+)\s*[:—\-]\s*(.+))|(.+))$', re.IGNORECASE)
    topic_regex = re.compile(r'^-\s*\[([ xX])\]\s*(.+)$')

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # Check for Tier header (Level 1: '# Tier ...')
        m_tier = tier_regex.match(stripped)
        if m_tier:
            code = (m_tier.group(1) or m_tier.group(3) or str(tier_counter)).strip()
            name = (m_tier.group(2) or m_tier.group(4) or f"Tier {code}").strip()
            tier_counter += 1
            current_tier = {
                "id": f"tier.{slugify(code)}",
                "code": code,
                "title": name if name else f"Tier {code}",
                "clusters": []
            }
            tiers.append(current_tier)
            current_cluster = None # Reset current cluster when entering new tier
            continue

        # Check for top-level document title if not a tier
        if stripped.startswith("# ") and not stripped.startswith("## ") and not current_tier and not title:
            m_title = doc_title_regex.match(stripped)
            if m_title and not tier_regex.match(stripped):
                title = m_title.group(1).strip()
                continue

        # Check for Cluster header (Level 2: '## ...')
        if stripped.startswith("## ") and not stripped.startswith("### "):
            m_cluster = cluster_regex.match(stripped)
            if not current_tier:
                if auto_fix:
                    tier_counter += 1
                    current_tier = {
                        "id": f"tier.{tier_counter}",
                        "code": str(tier_counter),
                        "title": "General System Design",
                        "clusters": []
                    }
                    tiers.append(current_tier)
                    warnings.append(f"Line {line_idx}: Cluster defined before any Tier. Auto-assigned to Tier {tier_counter}.")
                else:
                    errors.append(f"Line {line_idx}: Cluster '{stripped}' found outside of any Tier definition. Curriculums must follow Tier > Cluster > Topic.")
                    continue

            cluster_counter += 1
            if m_cluster:
                if m_cluster.group(1) and m_cluster.group(2):
                    c_order = int(m_cluster.group(1))
                    c_code = m_cluster.group(2).strip()
                    c_title = m_cluster.group(3).strip()
                elif m_cluster.group(4):
                    c_order = cluster_counter
                    c_code = m_cluster.group(4).strip()
                    c_title = m_cluster.group(5).strip()
                else:
                    c_order = cluster_counter
                    raw_title = m_cluster.group(6).strip()
                    c_code = f"{current_tier['code']}.{cluster_counter}"
                    c_title = raw_title
            else:
                c_order = cluster_counter
                c_code = f"{current_tier['code']}.{cluster_counter}"
                c_title = stripped.replace("##", "").strip()

            current_cluster = {
                "id": f"cluster.{slugify(c_code)}",
                "code": c_code,
                "title": c_title,
                "order": c_order,
                "tierId": current_tier["id"],
                "topics": []
            }
            current_tier["clusters"].append(current_cluster)
            clusters.append(current_cluster)
            continue

        # Check for Topic entry (Level 3: '- [ ] ...')
        m_topic = topic_regex.match(stripped)
        if m_topic:
            if not current_cluster:
                if auto_fix:
                    if not current_tier:
                        tier_counter += 1
                        current_tier = {"id": f"tier.{tier_counter}", "code": str(tier_counter), "title": "General", "clusters": []}
                        tiers.append(current_tier)
                    cluster_counter += 1
                    current_cluster = {
                        "id": f"cluster.{current_tier['code']}.{cluster_counter}",
                        "code": f"{current_tier['code']}.{cluster_counter}",
                        "title": "Foundations",
                        "order": cluster_counter,
                        "tierId": current_tier["id"],
                        "topics": []
                    }
                    current_tier["clusters"].append(current_cluster)
                    clusters.append(current_cluster)
                    warnings.append(f"Line {line_idx}: Topic found outside any cluster. Auto-created cluster '{current_cluster['title']}'.")
                else:
                    errors.append(f"Line {line_idx}: Topic '{stripped}' found outside of any Cluster. Curriculums must follow Tier > Cluster > Topic.")
                    continue

            topic_body = m_topic.group(2).strip()
            topic_status = "completed" if m_topic.group(1).lower() == "x" else "unseen"

            # Validate Sign-off gate
            if "—" in topic_body or "--" in topic_body:
                parts = re.split(r'\s*(?:—|--)\s*', topic_body, maxsplit=2)
                topic_title = parts[0].strip()
                spec = parts[1].strip() if len(parts) > 1 else ""
                gate = parts[2].strip() if len(parts) > 2 else ""
            else:
                topic_title = topic_body
                spec = topic_body
                gate = ""

            if not gate and not re.search(r'tick off when', topic_body, re.IGNORECASE):
                if auto_fix:
                    gate = "*Tick off when: you can derive the core trade-off and explain invariants cold without notes.*"
                    warnings.append(f"Line {line_idx}: Topic '{topic_title}' missing sign-off gate. Added standard sign-off gate.")
                else:
                    errors.append(f"Line {line_idx}: Topic '{topic_title}' missing mandatory sign-off gate ('— *Tick off when: <criteria>*').")

            topic_counter += 1
            t_id = f"topic.{current_cluster['code']}.{slugify(topic_title)}"
            
            # Avoid collisions
            if any(t["id"] == t_id for t in current_cluster["topics"]):
                t_id = f"{t_id}-{topic_counter}"

            current_cluster["topics"].append({
                "id": t_id,
                "title": topic_title,
                "specification": spec,
                "signOffGate": gate,
                "status": topic_status
            })

    if not title:
        title = "System Design Curriculum"

    return title, tiers, clusters, errors, warnings

def main():
    parser = argparse.ArgumentParser(description="Strict Tier > Cluster > Topic Curriculum Validator and Importer")
    parser.add_argument("--input", required=True, help="Path to markdown curriculum file")
    parser.add_argument("--instance-dir", default=".system-design", help="Path to target .system-design directory")
    parser.add_argument("--title", help="Custom curriculum title")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-normalize missing tiers/clusters/gates")
    parser.add_argument("--check-only", action="store_true", help="Only validate without writing files")

    args = parser.parse_args()

    print(f"🔍 Validating curriculum against Tier > Cluster > Topic taxonomy: {args.input}")
    title, tiers, clusters, errors, warnings = validate_and_parse_curriculum(args.input, args.title, args.auto_fix)

    for w in warnings:
        print(f"   ⚠️ {w}")

    if errors:
        print("\n❌ Curriculum Taxonomy Validation FAILED:")
        for e in errors:
            print(f"   • {e}")
        print("\nRequired hierarchy standard:")
        print("   # Tier <N>: <Tier Title>                                  (Level 1)")
        print("   ## <Order>. [<Code>] <Cluster Title>                      (Level 2)")
        print("   - [ ] <Topic Title> — <Specification> — *Tick off when:*  (Level 3)")
        print("\n💡 Run with --auto-fix to automatically normalize and fill placeholder tiers/gates.")
        sys.exit(1)

    total_topics = sum(len(c["topics"]) for c in clusters)
    print(f"✅ Taxonomy verified: {len(tiers)} Tiers, {len(clusters)} Clusters, {total_topics} Topics.")

    if args.check_only:
        sys.exit(0)

    # Scaffolding
    os.makedirs(args.instance_dir, exist_ok=True)
    os.makedirs(os.path.join(args.instance_dir, "lessons"), exist_ok=True)

    today_str = datetime.date.today().isoformat()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    manifest_clusters = []
    for c in clusters:
        manifest_clusters.append({
            "id": c["id"],
            "code": c["code"],
            "title": c["title"],
            "order": c["order"],
            "tierId": c.get("tierId"),
            "topics": [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "status": t["status"]
                }
                for t in c["topics"]
            ]
        })

    first_cluster = clusters[0] if clusters else None
    first_topic = first_cluster["topics"][0] if first_cluster and first_cluster["topics"] else None

    manifest = {
        "$schemaVersion": "3.2",
        "instanceName": title,
        "createdAt": now_iso,
        "lastUpdated": now_iso,
        "curriculum": {
            "id": f"curriculum.{slugify(title)}",
            "title": title,
            "source": "byo-markdown",
            "sourceRef": args.input,
            "activeClusterId": first_cluster["id"] if first_cluster else None,
            "activeTopicId": first_topic["id"] if first_topic else None,
            "clusters": manifest_clusters
        },
        "cursor": {
            "version": 1,
            "lastTickTimestamp": now_iso,
            "activeClusterCode": first_cluster["code"] if first_cluster else "none",
            "activeClusterName": first_cluster["title"] if first_cluster else "none",
            "activeTier": "Tier 0",
            "activeTopic": first_topic["title"] if first_topic else "none",
            "topicFoundationId": f"foundation.{first_topic['id'].replace('topic.', '')}" if first_topic else "foundation.none",
            "topicFoundationStatus": "not-started",
            "activeMechanismGroupId": f"group.{first_topic['id'].replace('topic.', '')}" if first_topic else "group.none",
            "nextTeachingAction": f"Start foundational inquiry on {first_topic['title']}" if first_topic else "Review curriculum",
            "backwardAnchor": "Curriculum initialized via Bring-Your-Own (BYO) Markdown import",
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

    manifest_path = os.path.join(args.instance_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Copy input markdown as CURRICULUM.md
    with open(args.input, "r", encoding="utf-8") as src, open(os.path.join(args.instance_dir, "CURRICULUM.md"), "w", encoding="utf-8") as dst:
        dst.write(src.read())

    print(f"📦 Scaffolded BYO learning instance at {args.instance_dir}/")
    print(f"   • Manifest:   {manifest_path}")
    print(f"   • Curriculum: {os.path.join(args.instance_dir, 'CURRICULUM.md')}")

if __name__ == "__main__":
    main()
