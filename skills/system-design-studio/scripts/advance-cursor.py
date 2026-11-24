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

def log_adr_record(inst_dir, topic_id, topic_title, cluster_title, cluster_code, evidence, discussion_summary, hypothesis, today_str):
    decisions_path = os.path.join(inst_dir, "DECISIONS.md")
    if not os.path.exists(decisions_path):
        header = "# Architecture Decision Records (ADRs)\n\n"
    else:
        with open(decisions_path, "r", encoding="utf-8") as f:
            header = f.read()

    placeholder = "*No decisions accepted yet. Decisions will be recorded as architectural trade-offs are evaluated and defended in workshops.*"
    if placeholder in header:
        header = header.replace(placeholder, "").strip() + "\n\n"

    existing_adrs = re.findall(r"##\s+ADR-(\d+)", header)
    next_num = (max([int(x) for x in existing_adrs]) + 1) if existing_adrs else 1
    adr_id = f"ADR-{next_num:03d}"

    claim_text = evidence.strip() if evidence else "Verified cold in chat defense without notes."
    discussion_text = discussion_summary.strip() if discussion_summary else "Learner evaluated physical failure modes and quantitative boundaries during self evaluation."
    hypo_text = hypothesis.strip() if hypothesis else "Assumed naive architectural approach prior to stress testing failure boundaries."

    adr_entry = f"""## {adr_id}: {topic_title} Architectural Defense
- **Date**: {today_str}
- **Cluster**: {cluster_title} (`{cluster_code}`)
- **Topic ID**: `{topic_id}`
- **Status**: Accepted (Verified Sign-Off Gate)

### Context & Problem Statement
Evaluating architectural choices under physical network/hardware boundaries, uncoordinated failure modes, and latency floors.
- **Initial Hypothesis**: {hypo_text}

### Invariant Claim & Decision
> {claim_text}

### Trade-Off Discussion & Defense Summary
{discussion_text}

### Consequences & Non-Negotiable Invariants
- **Guaranteed (Gain)**: Verified operational ordering, bounded blast radius, and deterministic recovery.
- **Non-Guarantee (Tax)**: Coordination overhead, queueing jitter under packet loss, and protocol complexity.

---

"""
    new_content = header.rstrip() + "\n\n" + adr_entry
    atomic_write(decisions_path, new_content)
    print(f"📋 Architecture Decision Record logged: {adr_id} in DECISIONS.md")

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
    parser = argparse.ArgumentParser(description="Advance System Design Studio cursor state")
    parser.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")
    parser.add_argument("--complete-topic", help="Topic ID to mark completed (e.g. topic.0.1.tcp-vs-udp)")
    parser.add_argument("--evidence", help="Evidence text demonstrating mastery")
    parser.add_argument("--hypothesis", help="Learner's initial intuition or hypothesis at the start of the topic")
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
    parser.add_argument("--discussion-summary", help="Summary of chat defense and edge cases discussed for note synthesis")
    parser.add_argument("--auto-notes", dest="auto_notes_opt", action="store_true", default=None, help="Force auto-generate notes regardless of settings")
    parser.add_argument("--no-auto-notes", dest="auto_notes_opt", action="store_false", help="Disable auto-generation of notes for this completion")
    parser.add_argument("--notes-data-file", "--data-file", dest="notes_data_file", help="Path to pre-structured NoteDocument or Lesson AST JSON")
    parser.add_argument("--notes-data", "--data", dest="notes_data", help="Raw JSON string for note synthesis")

    args = parser.parse_args()
    inst_dir = resolve_instance_dir(args.instance_dir)

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
    completed_cluster = None
    if args.complete_topic:
        normalized_id = args.complete_topic
        if not normalized_id.startswith("topic."):
            normalized_id = f"topic.{normalized_id}"

        matched_topic = None
        # 1. Exact match
        for cluster in manifest["curriculum"]["clusters"]:
            for topic in cluster["topics"]:
                if topic["id"] == args.complete_topic or topic["id"] == normalized_id:
                    matched_topic = topic
                    completed_cluster = cluster
                    args.complete_topic = topic["id"]
                    break
            if matched_topic:
                break

        # 2. Substring / Prefix match fallback
        if not matched_topic:
            query = args.complete_topic.lower().replace("topic.", "").strip()
            for cluster in manifest["curriculum"]["clusters"]:
                for topic in cluster["topics"]:
                    t_id_lower = topic["id"].lower()
                    t_title_lower = topic["title"].lower()
                    if query in t_id_lower or query in t_title_lower:
                        matched_topic = topic
                        completed_cluster = cluster
                        args.complete_topic = topic["id"]
                        break
                if matched_topic:
                    break

        if not matched_topic:
            print(f"❌ Error: Topic '{args.complete_topic}' not found in curriculum.", file=sys.stderr)
            sys.exit(1)

        matched_topic["status"] = "completed"
        completed_topic_title = matched_topic["title"]
        concept_id = f"concept.{args.complete_topic.replace('topic.', '')}"
        if concept_id not in manifest["runningContext"]["coveredConcepts"]:
            manifest["runningContext"]["coveredConcepts"].append(concept_id)
        if args.lesson_artifact:
            matched_topic["lessonArtifact"] = f"lessons/{os.path.basename(args.lesson_artifact)}"

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
    elif args.complete_topic:
        # Auto-advance cursor target to the next uncompleted topic when --next-topic-id is omitted
        auto_next_topic = None
        auto_next_cluster = None

        curr_cluster = completed_cluster
        if not curr_cluster:
            for cluster in manifest["curriculum"]["clusters"]:
                for topic in cluster["topics"]:
                    if topic["id"] == args.complete_topic:
                        curr_cluster = cluster
                        break
                if curr_cluster:
                    break

        if curr_cluster:
            comp_idx = -1
            for idx, t in enumerate(curr_cluster["topics"]):
                if t["id"] == args.complete_topic:
                    comp_idx = idx
                    break

            # 1. Look within the current cluster first for the next topic where topic.status != 'completed'
            if comp_idx != -1:
                for t in curr_cluster["topics"][comp_idx + 1:]:
                    if t.get("status") != "completed":
                        auto_next_topic = t
                        auto_next_cluster = curr_cluster
                        break

            if not auto_next_topic:
                for t in curr_cluster["topics"]:
                    if t.get("status") != "completed":
                        auto_next_topic = t
                        auto_next_cluster = curr_cluster
                        break

        # 2. If all topics in the current cluster are completed, advance to the next cluster's first uncompleted topic
        if not auto_next_topic:
            clusters = manifest["curriculum"]["clusters"]
            curr_cluster_idx = clusters.index(curr_cluster) if (curr_cluster and curr_cluster in clusters) else -1
            for i in range(1, len(clusters) + 1):
                idx = (curr_cluster_idx + i) % len(clusters)
                cand_cluster = clusters[idx]
                for t in cand_cluster["topics"]:
                    if t.get("status") != "completed":
                        auto_next_topic = t
                        auto_next_cluster = cand_cluster
                        break
                if auto_next_topic:
                    break

        if auto_next_topic and auto_next_cluster:
            manifest["curriculum"]["activeTopicId"] = auto_next_topic["id"]
            manifest["curriculum"]["activeClusterId"] = auto_next_cluster["id"]
            manifest["cursor"]["topicFoundationId"] = f"foundation.{auto_next_topic['id'].replace('topic.', '')}"
            manifest["cursor"]["topicFoundationStatus"] = "not-started"
            manifest["cursor"]["activeMechanismGroupId"] = f"group.{auto_next_topic['id'].replace('topic.', '')}"

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
  - *Topic Foundation Status*: `{manifest['cursor'].get('topicFoundationStatus', 'in-progress')}`
  - *Active Mechanism Group*: `{manifest['cursor'].get('activeMechanismGroupId', 'group.none')}`
  - *Last Checkpoint*: `{manifest['cursor'].get('lastCheckpointId', 'none')}` (Status: `{manifest['cursor'].get('lastCheckpointStatus', 'unseen')}`)
  - *Immediate Next Teaching Action*: {manifest['cursor'].get('nextTeachingAction', 'Review next topic')}

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

    # Auto-generate study note and log ADR if topic was completed
    if args.complete_topic:
        c_code = completed_cluster.get("code", "") if completed_cluster else ""
        c_title = completed_cluster.get("title", "") if completed_cluster else ""
        log_adr_record(inst_dir, args.complete_topic, completed_topic_title, c_title, c_code, args.evidence, args.discussion_summary, args.hypothesis, today_str)

        # Check auto-notes preference
        auto_notes_enabled = True
        if args.auto_notes_opt is not None:
            auto_notes_enabled = args.auto_notes_opt
        elif os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as sf:
                    s_cfg = json.load(sf)
                    if "autoGenerateNotes" in s_cfg:
                        val = s_cfg["autoGenerateNotes"]
                        auto_notes_enabled = val is True or str(val).lower() in ("true", "1", "yes")
            except Exception:
                pass

        script_dir = os.path.dirname(os.path.abspath(__file__))
        gen_notes_script = os.path.join(script_dir, "generate-notes.py")
        note_generated = False
        if auto_notes_enabled and os.path.exists(gen_notes_script):
            import subprocess
            cmd = [
                sys.executable,
                gen_notes_script,
                "--instance-dir", inst_dir,
                "--topic-id", args.complete_topic
            ]
            if args.evidence:
                cmd.extend(["--evidence", args.evidence])
            if args.hypothesis:
                cmd.extend(["--hypothesis", args.hypothesis])
            if args.discussion_summary:
                cmd.extend(["--discussion-summary", args.discussion_summary])
            if getattr(args, "notes_data_file", None):
                cmd.extend(["--data-file", args.notes_data_file])
            if getattr(args, "notes_data", None):
                cmd.extend(["--data", args.notes_data])
            try:
                subprocess.run(cmd, check=False)
                note_generated = True
            except Exception as e:
                print(f"⚠️ Note generation hook: {e}")
        elif not auto_notes_enabled:
            print("ℹ️ Auto-notes generation is disabled (autoGenerateNotes: false). Run 'sds notes generate' or /sds-notes to compile study notes manually.")

        # Auto-update Revision Mode flashcards in background
        rev_script = os.path.join(script_dir, "update-revisions.py")
        if os.path.exists(rev_script):
            try:
                import subprocess
                subprocess.run([sys.executable, rev_script, "--instance-dir", inst_dir, "--sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass

        # Record atomic Git checkpoint with tractable commit message
        checkpoint_script = os.path.join(script_dir, "git-checkpoint.py")
        if os.path.exists(checkpoint_script):
            try:
                import subprocess
                subject = f"complete {args.complete_topic} - {completed_topic_title} [verified]"
                subprocess.run([
                    sys.executable,
                    checkpoint_script,
                    "commit",
                    "--instance-dir", inst_dir,
                    "--type", "learn",
                    "--subject", subject
                ], check=False)
            except Exception as e:
                print(f"⚠️ Git checkpoint warning: {e}")

if __name__ == "__main__":
    main()
