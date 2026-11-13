#!/usr/bin/env python3
"""
verify-instance.py
Automated health-check and integrity verification for System Design Studio instances.
Validates manifest schemas, cursor lineage consistency, curriculum checkbox counts,
and HTML lesson artifacts.
"""

import os
import sys
import json
import re

def verify_instance(instance_dir=".system-design"):
    errors = []
    warnings = []
    passes = []

    print(f"🔍 Verifying System Design Studio instance at: {instance_dir}")

    # 1. Directory Structure
    req_files = ["manifest.json", "CURSOR.md", "CURRICULUM.md", "DECISIONS.md"]
    for f in req_files:
        p = os.path.join(instance_dir, f)
        if os.path.exists(p):
            passes.append(f"File exists: {f}")
        else:
            errors.append(f"Missing required file: {p}")

    lessons_dir = os.path.join(instance_dir, "lessons")
    if os.path.isdir(lessons_dir):
        passes.append("Directory exists: lessons/")
    else:
        errors.append(f"Missing lessons directory: {lessons_dir}")

    manifest_path = os.path.join(instance_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print("\n❌ CRITICAL: Cannot continue verification without manifest.json")
        for err in errors:
            print(f"  ❌ {err}")
        sys.exit(1)

    # 2. Manifest Schema Validation
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

    # 3. Check CURRICULUM.md parity
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

    # 4. Check CURSOR.md
    cursor_path = os.path.join(instance_dir, "CURSOR.md")
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

    # 5. Check Lessons Directory
    if os.path.isdir(lessons_dir):
        lesson_files = [f for f in os.listdir(lessons_dir) if f.endswith(".html")]
        passes.append(f"Found {len(lesson_files)} HTML lesson artifacts in lessons/")
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
    target = sys.argv[1] if len(sys.argv) > 1 else ".system-design"
    success = verify_instance(target)
    sys.exit(0 if success else 1)
