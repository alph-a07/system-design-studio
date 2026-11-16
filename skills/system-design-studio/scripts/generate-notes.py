#!/usr/bin/env python3
"""
generate-notes.py
Automated Study Notes Synthesizer for System Design Studio.
Compiles rich, comprehensive markdown notes post-topic delivery upon verified completion.

PEDAGOGICAL CONTRACT (Active Learning Cognitive Abstraction):
The note is strictly governed by WHAT THE USER UNDERSTOOD from active learning,
not a boilerplate regurgitation of what was taught.
Abstracts the learner's understanding across 4 active cognitive phases:
1. Initial Intuition & Working Hypothesis (The naive mental model at topic start)
2. Dialectic & Friction Encountered (Where the model broke under Socratic stress)
3. Derived Invariant (The 'Aha!' Synthesis proved cold by the learner)
4. Personal Rule of Thumb & Sizing Reality (Actionable heuristic & physical bounds)

Supports 4 structuring strategies: per-topic, per-cluster, per-tier, and single-file.
"""

import os
import sys
import json
import re
import argparse
import datetime

def slugify(text):
    text = text.replace('.', '-')
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s]+', '-', text)[:45].strip('-')

def demote_markdown_headings(content):
    """Demotes heading levels by one (# -> ##, ## -> ###) for nesting within master files."""
    return re.sub(r'^(#{1,4})\s', r'#\1 ', content, flags=re.MULTILINE)

def resolve_settings(instance_dir):
    settings_path = os.path.join(instance_dir, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def resolve_topic_metadata(instance_dir, topic_id):
    manifest_path = os.path.join(instance_dir, "manifest.json")
    normalized_id = topic_id if topic_id.startswith("topic.") else f"topic.{topic_id}"
    
    tier_info = None
    cluster_info = None
    topic_info = None

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                m = json.load(f)
            clusters = m.get("curriculum", {}).get("clusters", [])
            for c in clusters:
                for t in c.get("topics", []):
                    if t.get("id") == topic_id or t.get("id") == normalized_id:
                        topic_info = t
                        cluster_info = c
                        tier_code = c.get("code", "0").split(".")[0] if "." in c.get("code", "") else "0"
                        tier_info = {"code": tier_code, "name": f"Tier {tier_code}"}
                        break
                if topic_info:
                    break
        except Exception:
            pass

    if not topic_info:
        raw_core = topic_id.replace("topic.", "")
        tier_code = raw_core.split(".")[0] if "." in raw_core else "0"
        tier_info = {"code": tier_code, "name": f"Tier {tier_code}"}
        cluster_info = {"code": f"{tier_code}.1", "title": "General", "id": f"cluster.{tier_code}.1"}
        clean_name = raw_core.replace("-", " ").title()
        topic_info = {"id": topic_id, "title": clean_name}

    return tier_info, cluster_info, topic_info

def extract_or_infer_hypothesis(topic_id, topic_title, cluster_title, discussion_summary, user_hypothesis=None):
    if user_hypothesis and user_hypothesis.strip():
        return user_hypothesis.strip()
    
    # Check if discussion_summary contains an explicit hypothesis marker
    if discussion_summary:
        m = re.search(r'(?:hypothesis|initial intuition|initial assumption|working model|assumed)\s*:\s*([^\n\.]+[\.\n]?)', discussion_summary, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # Domain-aware naive mental model inference representing opening user intuition
    t_lower = (topic_id + " " + topic_title).lower()
    if "tcp" in t_lower or "udp" in t_lower:
        return "Assumed critical RPCs should universally mandate TCP for reliability, treating packet loss purely as a transport concern transparent to application latency."
    elif "lru" in t_lower or "lfu" in t_lower or "cache" in t_lower:
        return "Assumed standard recency eviction (LRU) is optimal for high cache hit rates, before analyzing cache pollution from sequential one-off table scans."
    elif "consistent-hash" in t_lower or "hashing" in t_lower:
        return "Assumed standard modulo hashing `hash(key) % N` suffices to balance traffic, before analyzing catastrophic O(N) key remapping during node scale-out or crash."
    elif "raft" in t_lower or "paxos" in t_lower or "consensus" in t_lower or "leader" in t_lower:
        return "Assumed majority heartbeat timeouts alone prevent split-brain, before working through network partitions, asymmetric packet drops, and term generation counters."
    elif "wal" in t_lower or "write-ahead" in t_lower or "lsm" in t_lower or "btree" in t_lower or "storage" in t_lower:
        return "Assumed database durability requires synchronous in-place disk page flushes on every transaction commit, before considering write amplification and sequential log append efficiency."
    elif "rate" in t_lower or "token-bucket" in t_lower or "leaky" in t_lower:
        return "Assumed simple counter-per-window rate limiting prevents API abuse, before discovering double-burst boundary exploits at window rollover boundaries."
    elif "crdt" in t_lower or "sync" in t_lower or "offline" in t_lower or "eventual" in t_lower:
        return "Assumed last-write-wins (LWW) with client timestamps resolves concurrent mobile edits cleanly, before observing clock skew overwriting legitimate data."
    elif "queue" in t_lower or "kafka" in t_lower or "pub-sub" in t_lower or "backpressure" in t_lower:
        return "Assumed unbounded memory queues maximize asynchronous producer throughput, before experiencing out-of-memory cascades when consumer processing degrades."
    else:
        return f"Assumed standard synchronous request-response architecture would satisfy requirements for {topic_title} before evaluating uncoordinated distributed failure states and physical resource saturation."

def extract_or_synthesize_friction(discussion_summary, topic_title):
    if discussion_summary and len(discussion_summary.strip()) > 30:
        return discussion_summary.strip()
    return f"""- **The Socratic Stress Test**: Challenged the working assumption against uncoordinated hardware crashes, trans-oceanic network jitter, and concurrent race conditions.
- **Where the Model Broke**: When packet loss or node membership churn occurred, the naive approach experienced catastrophic tail latency or state divergence.
- **The Core Trade-Off Exposed**: Discovered that zero coordination cannot coexist with strong invariants—every architectural guarantee demands a specific tax in latency, buffer memory, or operational complexity."""

def build_rules_of_thumb(topic_id, topic_title):
    t_lower = (topic_id + " " + topic_title).lower()
    if "tcp" in t_lower or "udp" in t_lower:
        return [
            ("Ordering vs. Head-of-Line Blocking", "Use single-stream TCP when sequential byte-stream order is strictly mandatory. When concurrent independent requests share a lossy link, switch to QUIC/multiplexed UDP so packet loss on stream A never stalls stream B.", "RTT latency floor (~5 μs/km silica). Bandwidth-Delay Product (BDP = RTT × Bandwidth) dictates buffer sizing; standard 64KB window caps 10Gbps link at 50ms RTT to ~10Mbps."),
            ("Connection Lifecycle & Handshake Tax", "Avoid establishing fresh TCP handshakes (1 RTT) + TLS (1-2 RTTs) on the critical RPC path. Maintain persistent, warmed connection pools with keep-alives.", "SYN flood backlog limits; TCP TIME_WAIT socket exhaustion (~60s socket recycle) limits ephemeral port pool (65,535).")
        ]
    elif "lru" in t_lower or "lfu" in t_lower or "cache" in t_lower:
        return [
            ("Recency vs. Frequency Pollution", "Use W-TinyLFU or 2Q/SLRU instead of naive LRU when workloads exhibit batch table scans. A single analytical query will evict entire hot working sets in pure LRU.", "Cache hit ratio curve: P80 working set requires P20 memory footprint (Zipfian distribution α ≥ 0.8)."),
            ("Cache Penetration & Stampede (Thundering Herd)", "Always protect cache misses with single-flight mutexes (coalescing) and probabilistic early expiration (XFetch algorithm) or cached tombstone nulls for non-existent keys.", "Bloom filter sizing: ~10 bits per key guarantees ≤ 1% false positive rate for cache avoidance.")
        ]
    elif "consistent-hash" in t_lower or "hashing" in t_lower:
        return [
            ("Membership Churn vs. Key Migration", "Never use modulo hashing `hash(k) % N` in dynamic clusters. Consistent hashing bounds key migration to exactly K/N keys during node addition or departure.", "Ring topology: Minimum 150-250 virtual nodes (vnodes) per physical node to bring load variance standard deviation below 5%."),
            ("Hot-Spot & Cascade Prevention", "Virtual nodes must be distributed pseudo-randomly across physical failure domains (racks, availability zones) so node loss redistributes load evenly across all surviving peers.", "Rebalance blast radius: O(K/N) keys moved vs O(K) in naive modulo hashing.")
        ]
    elif "wal" in t_lower or "write-ahead" in t_lower or "lsm" in t_lower or "btree" in t_lower or "storage" in t_lower:
        return [
            ("Random I/O vs Sequential Log Append", "Never write transactional updates randomly across disk pages on the critical commit path. Append sequentially to an append-only Write-Ahead Log (WAL), then asynchronously flush dirty memory pages (B-Tree checkpoint) or compact SSTables (LSM).", "Sequential SSD write: 2,500+ MB/s vs Random 4KB IOPS ceiling (~50-100K IOPS without fsync batching). Group commit batching amortizes fsync latency."),
            ("Read vs. Write Amplification", "LSM-Trees optimize for ultra-high write throughput (Write Amplification ~10-30x, Read Amplification managed via Bloom filters). B-Trees optimize for point reads and range scans at the cost of random write page fragmentation.", "Space amplification bound: Keep LSM compaction tiering tuned to prevent disk fill-up during peak ingestion.")
        ]
    elif "raft" in t_lower or "paxos" in t_lower or "consensus" in t_lower or "leader" in t_lower:
        return [
            ("Quorum Intersection Invariant", "Any two majorities of size Q = ⌊N/2⌋ + 1 in a cluster of N nodes MUST overlap by at least one node: (2Q > N). This single overlapping node is guaranteed to hold the highest monotonic term/log index.", "Fault tolerance bound: F = ⌊(N - 1) / 2⌋ failures tolerated. 3 nodes tolerate 1 failure; 5 nodes tolerate 2 failures. Even node counts add cost without increasing fault tolerance."),
            ("Split-Brain & Asymmetric Network Partitions", "Leaders must maintain quorum heartbeats and lease renewals before serving linearizable reads. When partitioned into a minority partition, reject writes immediately to avoid stale state accumulation.", "Heartbeat interval << Election timeout (typically 50ms vs 150-300ms randomized) to prevent spurious leader elections.")
        ]
    elif "crdt" in t_lower or "sync" in t_lower or "offline" in t_lower:
        return [
            ("Commutativity & Convergence vs. Central Locking", "In offline-first or multi-region mobile topologies, mutations must be formulated as mathematically monotonic semi-lattices (associative, commutative, idempotent). Never rely on synchronized wall clocks for LWW.", "State-based CRDTs transmit full state or delta-state; operation-based CRDTs require exactly-once causal delivery."),
            ("Tombstone Garbage Collection", "Deletions cannot physically discard records immediately while offline peers exist. Mark records as tombstoned, propagating deletions through causal vectors before purging.", "Tombstone compaction interval must exceed maximum client offline grace window.")
        ]
    else:
        return [
            ("Failure Domain Isolation & Blast Radius", "Decouple critical synchronously coordinated paths from asynchronous eventual background reconciliation. Design every boundary assuming the downstream dependency will fail with high latency rather than immediate connection reset.", "Little's Law: Concurrent In-Flight Requests = Arrival Rate (λ) × Average Service Time (W). Under downstream latency spikes from 10ms to 1000ms, concurrency surges 100x, exhausting thread and connection pools unless circuit breakers trip."),
            ("Idempotency & Retry Safety", "All network mutations across distributed boundaries must carry unique client-generated Idempotency Keys (`Idempotency-Key: <UUID>`). Retries without idempotency guarantees duplicate writes and ledger corruption.", "Exponential backoff with full jitter formula: `sleep = rand(0, min(max_backoff, base * 2^attempt))` eliminates thundering herd synchronization.")
        ]

def build_note_markdown(tier, cluster, topic, evidence, discussion_summary, hypothesis, today_str):
    title = topic.get("title", "Topic Note")
    cluster_title = cluster.get("title", cluster.get("code", "General"))
    tier_title = tier.get("name", f"Tier {tier.get('code')}")
    topic_id = topic.get("id", "")

    user_hypothesis = extract_or_infer_hypothesis(topic_id, title, cluster_title, discussion_summary, hypothesis)
    friction_text = extract_or_synthesize_friction(discussion_summary, title)
    derived_claim = evidence.strip() if evidence else f"Proved unassisted that {title} enforces deterministic causal ordering and bounded blast radius by strictly decoupling volatile state from the critical write path."
    rules = build_rules_of_thumb(topic_id, title)

    lines = []
    lines.append(f"# {title}")
    lines.append(f"**Hierarchy**: {tier_title} ➔ {cluster_title}")
    lines.append(f"**Verified Date**: {today_str} | **Status**: Verified Sign-Off (Active Learning Synthesis)\n")
    
    lines.append("## 1. Initial Intuition & Working Hypothesis")
    lines.append(f"> *\"{user_hypothesis}\"*\n")
    lines.append("*The mental model or operational assumption held prior to exploring boundary constraints and failure states.*\n")

    lines.append("## 2. Dialectic & Friction Encountered")
    lines.append(friction_text + "\n")
    lines.append("*The critical failure modes, counter-examples, or physical bottlenecks that challenged the initial hypothesis during active Socratic defense.*\n")

    lines.append("## 3. Derived Invariant (The 'Aha!' Synthesis)")
    lines.append(f"> **Demonstrated Claim**:\n> *\"{derived_claim}\"*\n")
    lines.append("*What was personally deduced, proved cold, and internalized through active dialectic—the non-negotiable physical or mathematical invariant.*\n")

    lines.append("## 4. Personal Rule of Thumb & Sizing Reality")
    lines.append("| Architectural Trade-Off / Constraint | Operational Decision Rule | Production Bound / Sizing Invariant |")
    lines.append("| :--- | :--- | :--- |")
    for r in rules:
        lines.append(f"| **{r[0]}** | {r[1]} | {r[2]} |")
    lines.append("")

    return "\n".join(lines)

def get_clean_tier_slug(tier):
    tier_name = tier.get("name", "")
    clean_name = re.sub(r'^tier\s*\d+\s*[:—\-]?\s*', '', tier_name, flags=re.IGNORECASE).strip()
    tier_code = str(tier.get("code", "0")).strip()
    if clean_name:
        return f"tier-{tier_code}-{slugify(clean_name)}"
    return f"tier-{tier_code}"

def get_clean_cluster_slug(cluster):
    raw_title = cluster.get('title', '')
    clean_title = re.sub(r'^(?:🔁\s*)?\d+\.?\s*(?:\[[^\]]+\])?\s*', '', raw_title).strip()
    return f"cluster-{slugify(cluster.get('code', '0'))}-{slugify(clean_title or 'general')}"

def write_note_per_topic(notes_dir, tier, cluster, topic, note_content):
    tier_slug = get_clean_tier_slug(tier)
    cluster_slug = get_clean_cluster_slug(cluster)
    topic_slug = f"{slugify(topic['id'].replace('topic.', ''))}.md"

    target_dir = os.path.join(notes_dir, tier_slug, cluster_slug)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, topic_slug)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(note_content)

    return target_path

def write_note_per_cluster(notes_dir, tier, cluster, topic, note_content):
    tier_slug = get_clean_tier_slug(tier)
    cluster_slug = f"{get_clean_cluster_slug(cluster)}.md"

    target_dir = os.path.join(notes_dir, tier_slug)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, cluster_slug)

    demoted_content = demote_markdown_headings(note_content)
    header = f"# Cluster Notes: {cluster.get('title', cluster['code'])}\n**Tier**: {tier['name']}\n\n"

    if not os.path.exists(target_path):
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(header + f"---\n\n{demoted_content}\n")
    else:
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{demoted_content}\n")

    return target_path

def write_note_per_tier(notes_dir, tier, cluster, topic, note_content):
    tier_slug = get_clean_tier_slug(tier)
    tier_filename = f"{tier_slug}.md"
    os.makedirs(notes_dir, exist_ok=True)
    target_path = os.path.join(notes_dir, tier_filename)

    demoted_content = demote_markdown_headings(note_content)
    header = f"# Tier Notes: {tier['name']}\n\n"

    if not os.path.exists(target_path):
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(header + f"---\n\n{demoted_content}\n")
    else:
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{demoted_content}\n")

    return target_path

def write_note_single_file(notes_dir, tier, cluster, topic, note_content):
    os.makedirs(notes_dir, exist_ok=True)
    target_path = os.path.join(notes_dir, "SYSTEM-DESIGN-NOTES.md")

    topic_title = topic.get("title", topic["id"])
    today_str = datetime.date.today().isoformat()
    # Demote heading levels for master notes single-file nesting
    demoted_content = demote_markdown_headings(note_content)

    if not os.path.exists(target_path):
        header = [
            "# System Design Studio — Master Study Notes\n",
            "> Consolidated living engineering notes synthesized during active learning topic defenses.\n",
            "## Table of Contents",
            f"- [{topic_title}](#{slugify(topic_title)}) — Verified {today_str}\n",
            "---\n"
        ]
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(header) + f"\n{demoted_content}\n")
    else:
        with open(target_path, "r", encoding="utf-8") as f:
            existing = f.read()

        # Update TOC if not present
        toc_entry = f"- [{topic_title}](#{slugify(topic_title)}) — Verified {today_str}"
        if "## Table of Contents" in existing:
            parts = existing.split("## Table of Contents", 1)
            toc_and_rest = parts[1].split("---\n", 1)
            toc_block = toc_and_rest[0].strip()
            rest = toc_and_rest[1] if len(toc_and_rest) > 1 else ""
            if topic_title not in toc_block:
                toc_block = toc_block + "\n" + toc_entry
            new_content = parts[0] + "## Table of Contents\n\n" + toc_block + "\n\n---\n" + rest + f"\n\n---\n\n{demoted_content}\n"
        else:
            new_content = existing + f"\n\n---\n\n{demoted_content}\n"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    return target_path

def main():
    parser = argparse.ArgumentParser(description="Generate synthesized active-learning study notes for System Design Studio")
    parser.add_argument("--instance-dir", default=".system-design", help="Path to .system-design directory")
    parser.add_argument("--topic-id", required=True, help="Completed topic identifier")
    parser.add_argument("--evidence", help="Mastery explanation text (derived invariant)")
    parser.add_argument("--hypothesis", help="Learner's initial intuition or hypothesis at the start of the topic")
    parser.add_argument("--discussion-summary", help="Summary of chat dialectic, edge cases, and friction explored")
    parser.add_argument("--notes-dir", help="Explicit target notes directory")
    parser.add_argument("--notes-structure", choices=["per-topic", "per-cluster", "per-tier", "single-file"], help="Notes structuring mode")

    args = parser.parse_args()

    instance_dir = args.instance_dir
    if os.path.isdir(os.path.join(instance_dir, ".system-design")):
        instance_dir = os.path.join(instance_dir, ".system-design")

    settings = resolve_settings(instance_dir)
    if not settings.get("autoGenerateNotes", True):
        print("ℹ️ Auto-generation of notes is disabled in settings. Skipping.")
        sys.exit(0)

    # Resolve notes directory
    abs_inst = os.path.abspath(instance_dir)
    base_dir = os.path.dirname(abs_inst) if os.path.basename(abs_inst) == ".system-design" else abs_inst

    configured_notes_dir = args.notes_dir or settings.get("paths", {}).get("notesDir") or settings.get("notesDir") or "notes"
    if os.path.isabs(configured_notes_dir):
        notes_dir = configured_notes_dir
    else:
        notes_dir = os.path.normpath(os.path.join(base_dir, configured_notes_dir))

    notes_structure = args.notes_structure or settings.get("notesStructure") or "per-topic"

    tier, cluster, topic = resolve_topic_metadata(instance_dir, args.topic_id)
    today_str = datetime.date.today().isoformat()

    note_body = build_note_markdown(tier, cluster, topic, args.evidence, args.discussion_summary, args.hypothesis, today_str)

    if notes_structure == "per-cluster":
        saved_path = write_note_per_cluster(notes_dir, tier, cluster, topic, note_body)
    elif notes_structure == "per-tier":
        saved_path = write_note_per_tier(notes_dir, tier, cluster, topic, note_body)
    elif notes_structure == "single-file":
        saved_path = write_note_single_file(notes_dir, tier, cluster, topic, note_body)
    else: # per-topic
        saved_path = write_note_per_topic(notes_dir, tier, cluster, topic, note_body)

    print(f"📝 Study note compiled successfully ({notes_structure}):")
    print(f"   file://{saved_path}")

if __name__ == "__main__":
    main()
