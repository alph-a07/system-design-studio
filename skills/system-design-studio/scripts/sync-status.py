#!/usr/bin/env python3
"""
sync-status.py
Diagnostic tool for System Design Studio learning instances.
Reads .system-design/manifest.json and reports active focus, running context,
examples registry, and deferred queue health.
"""

import os
import sys
import json

def main():
    instance_dir = sys.argv[1] if len(sys.argv) > 1 else ".system-design"
    manifest_path = os.path.join(instance_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        print(f"❌ No System Design Studio instance found at '{instance_dir}/'. Run init-learning-instance.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        m = json.load(f)

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
    print(f"Curriculum:      {curriculum.get('title', 'Unknown')} ({curriculum.get('id', 'unknown')})")
    print(f"Overall Progress: {completed_topics} / {total_topics} Topics ({pct:.1f}%)")
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

if __name__ == "__main__":
    main()
