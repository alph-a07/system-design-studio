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

def get_home_dir():
    return os.environ.get("HOME") or os.environ.get("USERPROFILE") or os.path.expanduser("~")

def get_global_studio_dir():
    home = get_home_dir()
    return os.environ.get("SDS_GLOBAL_DIR") or os.path.join(home, ".system-design-studio")

def get_projects_registry_path():
    return os.path.join(get_global_studio_dir(), "projects.json")

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

def resolve_project_output_dir(raw_dir=None, project_id=None):
    if project_id:
        reg_path = get_projects_registry_path()
        if os.path.isfile(reg_path):
            try:
                with open(reg_path, "r", encoding="utf-8") as f:
                    reg = json.load(f)
                for p in reg.get("projects", []):
                    if p.get("id") == project_id:
                        p_path = os.path.expanduser(p.get("projectPath", ""))
                        return os.path.join(p_path, ".system-design") if not p_path.endswith(".system-design") else p_path
            except Exception:
                pass

    if raw_dir:
        expanded = os.path.expanduser(raw_dir)
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

    reg_path = get_projects_registry_path()
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

def export_curriculum(filtered_tiers, title, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "lessons"), exist_ok=True)

    manifest_path = os.path.join(output_dir, "manifest.json")
    curriculum_path = os.path.join(output_dir, "CURRICULUM.md")

    # Load existing manifest to preserve user progress across track changes / pruning
    old_manifest = None
    status_map = {}
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as mf:
                old_manifest = json.load(mf)
                for c in old_manifest.get("curriculum", {}).get("clusters", []):
                    for t in c.get("topics", []):
                        status_map[t["id"]] = {
                            "status": t.get("status", "unseen"),
                            "lessonArtifact": t.get("lessonArtifact")
                        }
        except Exception:
            old_manifest = None

    curriculum_lines = [
        f"# {title}\n",
        f"> **Project Curriculum Track**: Scoped to project. Generated on {datetime.date.today().isoformat()} via System Design Studio.\n",
        "---\n"
    ]

    manifest_clusters = []
    cluster_order = 1

    for t in filtered_tiers:
        curriculum_lines.append(f"\n# Tier {t['code']} — {t['title']}\n")
        for c in t["clusters"]:
            # Process topics and restore completed status if previously completed
            updated_topics = []
            for top in c["topics"]:
                top_copy = dict(top)
                if top["id"] in status_map:
                    top_copy["status"] = status_map[top["id"]]["status"]
                    if status_map[top["id"]]["lessonArtifact"]:
                        top_copy["lessonArtifact"] = status_map[top["id"]]["lessonArtifact"]
                updated_topics.append(top_copy)

            # Build raw lines for CURRICULUM.md, checking [x] for completed topics
            c_raw = []
            for rline in c["raw_lines"]:
                # If topic line, check if completed
                matched = False
                for ut in updated_topics:
                    if ut["status"] == "completed" and ut["title"] in rline:
                        c_raw.append(re.sub(r'^-\s*\[\s*\]', '- [x]', rline))
                        matched = True
                        break
                if not matched:
                    c_raw.append(rline)

            curriculum_lines.extend(c_raw)
            curriculum_lines.append("\n---\n")

            manifest_clusters.append({
                "id": f"cluster.{c['code']}",
                "code": c["code"],
                "title": f"{c['order']}. [{c['code']}] {c['title']}",
                "order": cluster_order,
                "tierId": f"tier.{t['code']}",
                "topics": updated_topics
            })
            cluster_order += 1

    # Write CURRICULUM.md
    with open(curriculum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(curriculum_lines))

    # Write manifest.json
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    first_cluster = manifest_clusters[0] if manifest_clusters else None
    first_topic = first_cluster["topics"][0] if first_cluster and first_cluster["topics"] else None

    # Find next active topic (first uncompleted)
    active_cluster = first_cluster
    active_topic = first_topic
    for mc in manifest_clusters:
        uncompleted = [top for top in mc["topics"] if top["status"] != "completed"]
        if uncompleted:
            active_cluster = mc
            active_topic = uncompleted[0]
            break

    # Preserve or initialize manifest
    manifest = {
        "$schemaVersion": "3.2",
        "instanceName": title,
        "createdAt": old_manifest.get("createdAt", now_iso) if old_manifest else now_iso,
        "lastUpdated": now_iso,
        "curriculum": {
            "id": f"curriculum.{re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:30]}",
            "title": title,
            "source": "project-scoped-track",
            "sourceRef": ".system-design/CURRICULUM.md",
            "activeClusterId": active_cluster["id"] if active_cluster else None,
            "activeTopicId": active_topic["id"] if active_topic else None,
            "clusters": manifest_clusters
        },
        "cursor": {
            "version": (old_manifest.get("cursor", {}).get("version", 0) + 1) if old_manifest else 1,
            "lastTickTimestamp": now_iso,
            "activeClusterCode": active_cluster["code"] if active_cluster else "none",
            "activeClusterName": active_cluster["title"] if active_cluster else "none",
            "activeTier": f"Tier {filtered_tiers[0]['code']}" if filtered_tiers else "Tier 0",
            "activeTopic": active_topic["title"] if active_topic else "none",
            "topicFoundationId": f"foundation.{active_topic['id'].replace('topic.', '')}" if active_topic else "foundation.none",
            "topicFoundationStatus": "not-started",
            "activeMechanismGroupId": f"group.{active_topic['id'].replace('topic.', '')}" if active_topic else "group.none",
            "nextTeachingAction": f"Start foundational inquiry on {active_topic['title']}" if active_topic else "Review curriculum",
            "backwardAnchor": old_manifest.get("cursor", {}).get("backwardAnchor", "Track initialized via configure-curriculum.py") if old_manifest else "Track initialized via configure-curriculum.py",
            "forwardHook": f"Connect foundational invariants to {active_topic['title']}" if active_topic else "Prepare initial lesson"
        },
        "runningContext": old_manifest.get("runningContext", {
            "coveredConcepts": [],
            "examplesTaken": [],
            "deferredQueue": [],
            "causalAnchors": []
        }) if old_manifest else {
            "coveredConcepts": [],
            "examplesTaken": [],
            "deferredQueue": [],
            "causalAnchors": []
        },
        "evidence": old_manifest.get("evidence", []) if old_manifest else []
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    total_topics = sum(len(c["topics"]) for c in manifest_clusters)
    completed_topics = sum(1 for c in manifest_clusters for t in c["topics"] if t.get("status") == "completed")
    print(f"✅ Generated project-scoped curriculum track: '{title}'")
    print(f"   • Tiers:     {len(filtered_tiers)}")
    print(f"   • Clusters:  {len(manifest_clusters)}")
    print(f"   • Topics:    {total_topics} ({completed_topics} completed preserved)")
    print(f"   • Directory: {output_dir}")

    # Record atomic Git checkpoint
    script_dir = os.path.dirname(os.path.abspath(__file__))
    checkpoint_script = os.path.join(script_dir, "git-checkpoint.py")
    if os.path.exists(checkpoint_script):
        try:
            import subprocess
            subj = f"update track '{title}' ({len(manifest_clusters)} clusters, {total_topics} topics)"
            subprocess.run([
                sys.executable,
                checkpoint_script,
                "commit",
                "--instance-dir", output_dir,
                "--type", "curriculum",
                "--subject", subj
            ], check=False)
        except Exception as e:
            print(f"⚠️ Git checkpoint error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Configure, prune, or select curriculum tracks for System Design Studio")
    parser.add_argument("--template", help="Path to CURRICULUM-template.md")
    parser.add_argument("--track", choices=list(TRACK_DEFINITIONS.keys()), help="Curated track name")
    parser.add_argument("--include-tiers", help="Comma-separated tier codes to include (e.g. 0,1,2)")
    parser.add_argument("--exclude-tiers", help="Comma-separated tier codes to exclude")
    parser.add_argument("--include-clusters", help="Comma-separated cluster codes to include (e.g. 0.1,0.2,1.3)")
    parser.add_argument("--reorder", help="Comma-separated cluster codes in desired sequence")
    parser.add_argument("--output-dir", "--instance-dir", dest="output_dir", default=".system-design", help="Target output instance directory")
    parser.add_argument("--project", dest="project_id", help="Target project ID from multi-project registry")
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

    resolved_output_dir = resolve_project_output_dir(args.output_dir, args.project_id)
    export_curriculum(filtered, title, resolved_output_dir)

if __name__ == "__main__":
    main()
