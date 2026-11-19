#!/usr/bin/env python3
"""
update-revisions.py
Revision Mode Engine for System Design Studio.
Compiles and manages high-value conceptual understanding distilled from:
1. Accepted sign-off ADRs in DECISIONS.md (claims, defenses, guarantees, and taxes)
2. Verified active-learning study notes in notes/ (hypotheses, friction, derived invariants, sizing tables)
3. Living teaching context in manifest.json & CURSOR.md (invariants, anchors, examples)
4. Reality check prompts and atomic topic trade-offs in CURRICULUM.md
5. Curated domain-aware scenario challenges across foundational distributed systems archetypes

Provides:
- Auto-compilation and continuous background sync into .system-design/revisions.json
- High-yield active recall flashcard structures with concrete scenario questions
- Defended invariants, failure boundaries, sizing math/formulas, and operational rules of thumb
- Spaced repetition scheduling (SM-2 / Leitner intervals: 1d, 3d, 7d+)
- Programmatic API for serve-dashboard.py and advance-cursor.py
"""

import os
import sys
import json
import re
import argparse
import datetime
import tempfile

DEFAULT_FOUNDATIONAL_REVISIONS = [
    {
        "id": "rev.0.1.tcp-vs-udp",
        "topicId": "topic.0.1.tcp-vs-udp",
        "topicTitle": "TCP Monotonic Stream vs UDP Datagram Boundaries",
        "tierId": "tier.0",
        "tierName": "Tier 0 — Network & Transport Mechanics",
        "clusterId": "cluster.0.1.transport",
        "clusterTitle": "Transport Protocols & Kernel Sockets",
        "realityCheckPrompt": "Under 1% network packet loss on a 50ms RTT link, why does an HTTP/2 connection stall all concurrent streams, and why does VoD pick TCP while live videoconferencing picks UDP?",
        "invariant": "TCP guarantees total in-order byte stream delivery via sequence numbers and ACK sliding windows at the cost of Head-of-Line (HoL) blocking across all streams multiplexed onto that socket. UDP passes datagrams directly to userspace with no kernel-level reordering or retransmission.",
        "failureBoundary": "Under 1% network packet loss, HTTP/2 connection throughput degrades by up to 50% because the kernel TCP receive buffer stalls all application streams while waiting for the dropped segment retransmission.",
        "formula": "Throughput <= (MSS / RTT) * (1 / sqrt(p)) [Mathis Equation] | BDP = Bandwidth × RTT",
        "ruleOfThumb": "Use single-stream TCP when sequential byte-stream order is strictly mandatory. When concurrent independent requests share a lossy link, switch to QUIC/multiplexed UDP so packet loss on stream A never stalls stream B.",
        "naiveTrap": "Assuming TCP packet loss is transparent to application latency when multiplexing many requests onto a single connection.",
        "defenseAnswer": "TCP provides a single monotonic byte stream; a single dropped packet stalls socket read() for every application request sharing that TCP connection. UDP passes raw datagrams directly to userspace with no kernel-level reordering or retransmission.",
        "guarantees": ["Deterministic in-order byte delivery", "Kernel-level flow control and congestion avoidance"],
        "taxes": ["Head-of-Line blocking latency jitter", "Three-way handshake roundtrips before payload transmission"],
        "masteryStatus": "proficient",
        "lastReviewed": None,
        "reviewCount": 0,
        "streak": 1,
        "source": "Foundational"
    },
    {
        "id": "rev.0.2.quic-http3",
        "topicId": "topic.0.2.quic-and-http3",
        "topicTitle": "QUIC Stream Multiplexing & Connection Migration",
        "tierId": "tier.0",
        "tierName": "Tier 0 — Network & Transport Mechanics",
        "clusterId": "cluster.0.1.transport",
        "clusterTitle": "Transport Protocols & Kernel Sockets",
        "realityCheckPrompt": "Why can HTTP/1.1 with 6 parallel TCP connections outperform multiplexed HTTP/2 over a single connection under 2% packet loss, and how does HTTP/3 (QUIC) eliminate transport HoL blocking?",
        "invariant": "QUIC shifts reliable transport and crypto handshakes from kernel OS space into user-space UDP datagrams, isolating packet loss and congestion state to individual stream frames.",
        "failureBoundary": "NAT rebinding during cellular-to-Wi-Fi handoff breaks 4-tuple TCP connections; QUIC connection ID (CID) enables seamless migration without renegotiating TLS.",
        "formula": "Handshake RTT: 0-RTT (resumed) or 1-RTT (initial) vs TCP+TLS 1.3 (2-3 RTT)",
        "ruleOfThumb": "Deploy HTTP/2 on high-reliability internal server-to-server backbones; deploy HTTP/3/QUIC on public internet edge and lossy mobile client networks.",
        "naiveTrap": "Assuming HTTP/2 multiplexing is unconditionally faster than HTTP/1.1 on lossy wireless networks.",
        "defenseAnswer": "QUIC packets carry independent stream IDs. Dropping a packet for stream #3 halts decoding for stream #3 only; streams #1 and #2 continue reading immediately.",
        "guarantees": ["Zero stream-level Head-of-Line blocking", "Cryptographic connection migration across cellular/Wi-Fi handoffs"],
        "taxes": ["Higher userspace CPU utilization (UDP syscall overhead)", "Middlebox UDP rate limiting and packet drop policies"],
        "masteryStatus": "learning",
        "lastReviewed": None,
        "reviewCount": 0,
        "streak": 0,
        "source": "Foundational"
    },
    {
        "id": "rev.0.3.tls-resumption",
        "topicId": "topic.0.1.tls-handshake-cost-and-session-resumptio",
        "topicTitle": "TLS Handshake Cost & Session Resumption",
        "tierId": "tier.0",
        "tierName": "Tier 0 — Network & Transport Mechanics",
        "clusterId": "cluster.0.1.transport",
        "clusterTitle": "Transport Protocols & Kernel Sockets",
        "realityCheckPrompt": "Why does connection reuse matter so critically on cellular networks, and what replay attack vulnerability does TLS 1.3 0-RTT Early Data introduce to non-idempotent endpoints?",
        "invariant": "Fresh TLS 1.3 handshakes cost 1 RTT (plus 1 TCP RTT); 0-RTT resumption uses pre-shared keys (PSK) without forward secrecy on early data, allowing adversaries to replay captured application requests.",
        "failureBoundary": "Replayed 0-RTT packets duplicate payment or state mutation requests unless the server enforces anti-replay timestamp windows and single-use ticket caches.",
        "formula": "Cellular RTT is 50-200ms; warming connection pools with keep-alives cuts API tail latency by 100-300ms.",
        "ruleOfThumb": "Allow 0-RTT Early Data only for strictly idempotent GET requests; enforce persistent warmed connection pools with TLS keep-alives for critical RPCs.",
        "naiveTrap": "Enabling 0-RTT early data blindly on stateful mutation endpoints (POST/PUT).",
        "defenseAnswer": "0-RTT sends client payload in the initial Flight 1 packet before the server hello, so an attacker sniffing the link can replay Flight 1 to duplicate side effects.",
        "guarantees": ["Forward-secret encrypted payload transport", "Session resumption avoids asymmetric key computation tax"],
        "taxes": ["Initial connection setup roundtrip latency", "Replay vulnerability on 0-RTT early data"],
        "masteryStatus": "learning",
        "lastReviewed": None,
        "reviewCount": 0,
        "streak": 0,
        "source": "Foundational"
    },
    {
        "id": "rev.1.1.lsm-compaction",
        "topicId": "topic.1.1.lsm-trees",
        "topicTitle": "LSM Trees: MemTable, SSTables, and Leveled Compaction",
        "tierId": "tier.1",
        "tierName": "Tier 1 — Storage Engines & Data Layout",
        "clusterId": "cluster.1.1.storage",
        "clusterTitle": "Storage Engines & Inverted Indices",
        "realityCheckPrompt": "Why does an LSM engine trigger write stalls even when spare disk storage is plentiful, and how do leveled vs tiered compaction differ?",
        "invariant": "LSM engines trade read latency and compaction write amplification for sequential disk write throughput via append-only commit logs and immutable sorted string tables (SSTables).",
        "failureBoundary": "Write stalls occur when background compaction threads cannot keep pace with write ingestion, forcing write rate throttling to avoid SSTable unbounded accumulation.",
        "formula": "Write Amplification Factor (WAF) = Total Bytes Written to Disk / Bytes Ingested (typically 10-30x in leveled compaction)",
        "ruleOfThumb": "Use LSM-Trees for high-velocity write ingest (logs, metrics, timeseries); use B-Trees for read-heavy workloads with complex range filters and covering index requirements.",
        "naiveTrap": "Assuming LSM disk append speed means compaction comes with zero background I/O performance tax.",
        "defenseAnswer": "LSM writes strictly append to an in-memory MemTable and on-disk WAL. Reads must check MemTable, Bloom filters, and multi-level SSTables, demanding Bloom filter cache tuning.",
        "guarantees": ["Sequential disk writes for high ingest throughput", "Immutable SSTables simplify crash recovery and concurrency"],
        "taxes": ["High background write amplification and disk wear", "Read amplification mitigated only by Bloom filters"],
        "masteryStatus": "needs_review",
        "lastReviewed": None,
        "reviewCount": 0,
        "streak": 0,
        "source": "Foundational"
    },
    {
        "id": "rev.1.2.isolation-write-skew",
        "topicId": "topic.0.2.isolation-levels",
        "topicTitle": "Transaction Isolation Levels & Write Skew",
        "tierId": "tier.0",
        "tierName": "Tier 0 — Databases & Storage Mechanics",
        "clusterId": "cluster.0.2.databases",
        "clusterTitle": "Indexes, Transactions & Isolation",
        "realityCheckPrompt": "In a hospital on-call database where at least one doctor must be active, two doctors simultaneously attempt to go off call under Snapshot Isolation. Both read 2 active doctors. Why does Snapshot Isolation permit both (Write Skew), and what pattern prevents it?",
        "invariant": "Snapshot Isolation prevents dirty reads and non-repeatable reads by checking write-write conflicts on identical rows, but CANNOT detect cross-row constraint violations where concurrent transactions read overlapping rows and write to disjoint rows (Write Skew).",
        "failureBoundary": "Both doctors successfully go off call, violating the invariant of having at least one active doctor, with zero transaction errors or deadlocks.",
        "formula": "Serializable Isolation or explicit SELECT ... FOR UPDATE (pessimistic locking) is mathematically mandatory to eliminate Write Skew.",
        "ruleOfThumb": "When a business decision reads across multiple rows to validate a constraint before writing, standard Snapshot Isolation is insufficient: enforce Serializable or SELECT ... FOR UPDATE.",
        "naiveTrap": "Believing that 'running inside a database transaction' automatically prevents all concurrency bugs and data anomalies.",
        "defenseAnswer": "Write skew occurs because neither transaction modifies a row that the other modified; they read overlapping state and write to separate rows, bypassing first-committer-wins row locks.",
        "guarantees": ["Consistent snapshot reads without blocking concurrent writers"],
        "taxes": ["Vulnerability to phantom reads and write skew without explicit locks"],
        "masteryStatus": "learning",
        "lastReviewed": None,
        "reviewCount": 0,
        "streak": 0,
        "source": "Foundational"
    },
    {
        "id": "rev.2.1.raft-consensus",
        "topicId": "topic.2.1.raft-consensus",
        "topicTitle": "Raft Leader Election, Log Replication & Quorums",
        "tierId": "tier.2",
        "tierName": "Tier 2 — Distributed Coordination & Consensus",
        "clusterId": "cluster.2.1.consensus",
        "clusterTitle": "Consensus Protocols & Split-Brain Fencing",
        "realityCheckPrompt": "Why must any two Raft majorities overlap by at least one node (2Q > N), and how does term monotonicity prevent a partitioned former leader from overwriting committed state?",
        "invariant": "Raft guarantees strong state machine safety across asymmetric network partitions through strict term monotonicity and majoritarian log matching: a leader must possess all committed entries from prior terms.",
        "failureBoundary": "In an asymmetric network partition where a leader can talk to clients but not to a majority of followers, reads without lease verification return stale uncommitted data.",
        "formula": "Quorum Size Q = floor(N / 2) + 1 (Fault tolerance F = floor((N - 1) / 2))",
        "ruleOfThumb": "Always deploy odd cluster sizes (3, 5, 7) for consensus. Implement leader leases and generation term counters before serving linearizable reads.",
        "naiveTrap": "Assuming adding an even node (e.g. 4th node to a 3-node cluster) increases fault tolerance; it actually reduces availability under network partitions.",
        "defenseAnswer": "Raft avoids split-brain by requiring strict majority quorum (N/2 + 1) for both leader election and entry commitment. Two majorities in a cluster of size N must intersect by at least one common node.",
        "guarantees": ["Linearizable read/write consistency", "Deterministic automatic failover within randomized election timeout"],
        "taxes": ["Minimum 3 nodes required to tolerate 1 failure; 5 nodes for 2 failures", "Write latency bounded by slowest node in the majority quorum"],
        "masteryStatus": "proficient",
        "lastReviewed": None,
        "reviewCount": 0,
        "streak": 1,
        "source": "Foundational"
    }
]

DOMAIN_CHALLENGES = {
    "tcp": {
        "realityCheckPrompt": "Under 1% network packet loss on a 50ms link, why does an HTTP/2 connection stall across all multiplexed streams, and why does VoD use TCP while live videoconferencing picks UDP?",
        "invariant": "TCP receive buffers enforce total monotonic byte ordering; a single dropped segment halts socket read() across all multiplexed application streams until retransmission succeeds.",
        "failureBoundary": "Under 1-2% loss on high BDP links (>50ms RTT), Mathis formula throughput collapses (Throughput <= (MSS / RTT) * (1 / sqrt(p))).",
        "formula": "Throughput <= (MSS / RTT) * (1 / sqrt(p)) [Mathis Equation] | BDP = RTT × Bandwidth",
        "ruleOfThumb": "Use single-stream TCP when sequential byte-stream order is strictly mandatory. Switch to QUIC/multiplexed UDP when concurrent independent requests share a lossy link.",
        "naiveTrap": "Treating packet loss purely as a transport concern transparent to application latency."
    },
    "http": {
        "realityCheckPrompt": "Why can HTTP/1.1 with 6 parallel TCP connections outperform multiplexed HTTP/2 over a single connection under 2% packet loss, and what problem does QUIC solve?",
        "invariant": "HTTP/2 multiplexes application frames over 1 TCP connection, creating a single point of HoL blocking at the transport layer. HTTP/3 moves multiplexing over UDP datagrams with per-stream frame isolation.",
        "failureBoundary": "HoL blocking in HTTP/2 stalls every request on the connection when 1 packet drops. HTTP/1.1 bounds the stall to 1 of 6 connections.",
        "formula": "QUIC 0-RTT/1-RTT connection setup saves 1-2 network roundtrips over TCP + TLS 1.3.",
        "ruleOfThumb": "Use HTTP/2 on reliable low-loss internal backbones; deploy HTTP/3/QUIC on public internet edge and mobile clients.",
        "naiveTrap": "Assuming HTTP/2 multiplexing is always faster than HTTP/1.1 under lossy cellular networks."
    },
    "tls": {
        "realityCheckPrompt": "Why does connection reuse matter so critically on cellular networks, and what replay attack risk does TLS 1.3 0-RTT Early Data introduce to stateful APIs?",
        "invariant": "Fresh TLS 1.3 handshakes cost 1 RTT (plus 1 TCP RTT); 0-RTT resumption lacks forward secrecy on early data, allowing attackers to replay POST requests.",
        "failureBoundary": "Replayed 0-RTT early data packets can duplicate payment or mutation requests unless server enforces anti-replay caches.",
        "formula": "Cellular 1 RTT can exceed 100-200ms; warming connection pools with keep-alives cuts API tail latency by >300ms.",
        "ruleOfThumb": "Allow 0-RTT only for strictly idempotent GET requests; enforce persistent warmed connection pools with TLS keep-alives for critical RPCs.",
        "naiveTrap": "Enabling 0-RTT early data blindly on stateful mutation endpoints (POST/PUT)."
    },
    "pagination": {
        "realityCheckPrompt": "Why does offset pagination (OFFSET N LIMIT M) degrade to O(N) CPU/disk scan cost at deep offsets and cause duplicate or skipped rows during active insertions, and how does keyset/cursor pagination fix this?",
        "invariant": "OFFSET N requires the database engine to scan and discard N rows in index order (O(N) CPU/IO cost). A cursor (WHERE id > :last_id LIMIT M) executes a direct O(log N) B-tree seek.",
        "failureBoundary": "Inserting a row on page 1 shifts all subsequent rows down, causing users scrolling to page 2 to see the last item from page 1 again (duplicate) or miss items entirely.",
        "formula": "OFFSET 1,000,000 scans 1,000,000 index entries, turning a 2ms query into a 5-second disk/memory thrash.",
        "ruleOfThumb": "Mandate cursor/keyset pagination for all infinite feeds, large tables, and public APIs. Reserve offset pagination strictly for small, static datasets (<1,000 rows).",
        "naiveTrap": "Using offset pagination for real-time activity feeds where concurrent writes occur."
    },
    "idempotency": {
        "realityCheckPrompt": "When an HTTP payment API times out, where is the ambiguity across client, network, and server, and how does an Idempotency Key table prevent duplicate charges?",
        "invariant": "Network timeouts are fundamentally ambiguous: the request may have failed before reaching the server, during processing, or on the response path. Without idempotency keys, client retries re-execute unsafe mutations.",
        "failureBoundary": "Client retries under transient packet drop without unique Idempotency-Key headers create duplicate financial transactions and inventory race conditions.",
        "formula": "Idempotency store TTL should exceed the maximum client retry window (e.g. 24-72 hours) with atomic conditional insert (INSERT ... ON CONFLICT DO NOTHING).",
        "ruleOfThumb": "All non-idempotent POST/PATCH endpoints must require a client-generated UUID idempotency key stored in an atomic persistence table before business logic executes.",
        "naiveTrap": "Assuming HTTP status codes or client timeouts indicate whether a backend transaction succeeded or failed."
    },
    "b-tree": {
        "realityCheckPrompt": "Why do B-Tree indexes optimize for range scans and ordered seeks, and why does every additional secondary index impose a hidden write tax during inserts and updates?",
        "invariant": "B-Tree point reads require O(log_B N) page lookups with in-place page modification; secondary indexes require random write updates across separate B-Tree disk pages for every inserted row.",
        "failureBoundary": "Uncontrolled secondary indexes turn single sequential inserts into 5-10 random 4KB disk I/O operations, exhausting IOPS limits.",
        "formula": "Fanout B ~ 100-500. A 4-level B-tree with fanout 100 indexes 100M rows with at most 3-4 page reads.",
        "ruleOfThumb": "Use B-Trees for read-heavy workloads with complex range filters and covering index requirements; use LSM-Trees for high-velocity ingest.",
        "naiveTrap": "Adding secondary indexes liberally without measuring their write amplification impact."
    },
    "lsm": {
        "realityCheckPrompt": "Why do LSM-Trees achieve 10-100x higher write throughput than B-Trees on SSDs, and what causes write stalls when compaction threads fall behind ingestion?",
        "invariant": "LSM engines trade compaction CPU/disk bandwidth for sequential append ingest; when background compaction cannot keep up with L0 SSTable generation, writes must pause to prevent unbounded read amplification.",
        "failureBoundary": "Too many uncompacted SSTables in L0 force point reads to check every L0 file sequentially, causing read latency spikes from 1ms to 200ms.",
        "formula": "Write Amplification Factor (WAF) in leveled compaction is typically 10-30x. Total Disk IO = Ingested Bytes * WAF.",
        "ruleOfThumb": "Tune compaction threads, MemTable buffer sizing, and Bloom filters (10 bits/key) before increasing ingestion limits in RocksDB/Cassandra.",
        "naiveTrap": "Assuming LSM disk append speed means compaction comes with zero background I/O performance tax."
    },
    "isolation": {
        "realityCheckPrompt": "In an on-call system where at least one doctor must be active, two doctors simultaneously attempt to go off call under Snapshot Isolation. Both read 2 active doctors. Why does Snapshot Isolation permit both (Write Skew), and what pattern prevents it?",
        "invariant": "Snapshot Isolation prevents dirty reads and non-repeatable reads by checking write-write conflicts on identical rows, but CANNOT detect cross-row constraint violations where concurrent transactions read overlapping rows and write to disjoint rows (Write Skew).",
        "failureBoundary": "Both doctors successfully go off call, violating the invariant of having at least one active doctor, with zero transaction errors or deadlocks.",
        "formula": "Serializable Isolation or explicit SELECT ... FOR UPDATE (pessimistic locking) is mathematically mandatory to eliminate Write Skew.",
        "ruleOfThumb": "When a business decision reads across multiple rows to validate a constraint before writing, standard Snapshot Isolation is insufficient: enforce Serializable or SELECT ... FOR UPDATE.",
        "naiveTrap": "Believing that 'running inside a database transaction' automatically prevents all concurrency bugs and data anomalies."
    },
    "cache": {
        "realityCheckPrompt": "When a hot cached key expires under 20,000 req/s, how does Single-Flight mutex coalescing prevent a database thundering herd, and what is the difference between Cache-Aside and Write-Through?",
        "invariant": "Cache expiration of a high-cardinality key causes thousands of concurrent cache misses to hit the backend database simultaneously (Thundering Herd / Cache Stampede).",
        "failureBoundary": "Database connection pool exhaustion and query queue backlog crash the primary database, which fails health checks and cascades upstream.",
        "formula": "XFetch Optimal Expiration: Delta - beta * ln(rand()) * compute_time. Recomputes cache in background before expiration.",
        "ruleOfThumb": "Always protect hot cache read paths with Single-Flight request coalescing and soft TTLs with probabilistic background refresh.",
        "naiveTrap": "Setting fixed TTLs on hot cached items without jitter or request deduplication."
    },
    "consistent-hash": {
        "realityCheckPrompt": "Why does simple modulo hashing (hash(k) % N) cause O(K) key remapping during node crashes or additions, and how do virtual nodes prevent hot-spot load skew in a consistent hash ring?",
        "invariant": "Modulo hashing remaps almost all keys (K * (N-1)/N) when N changes, clearing caches. Consistent hashing maps keys and nodes to a circular hash ring, bounding key migration to exactly K/N keys.",
        "failureBoundary": "In a basic ring without virtual nodes, non-uniform hash distribution causes hot-spot nodes to receive 3-5x the average traffic, causing cascade crashes.",
        "formula": "Minimum 150-250 virtual nodes (vnodes) per physical machine brings load distribution standard deviation below 5%.",
        "ruleOfThumb": "Use consistent hashing with virtual nodes for all distributed caches, partitioned databases, and load balancers where node membership changes dynamically.",
        "naiveTrap": "Using consistent hashing without virtual nodes and assuming physical servers will receive equal traffic."
    },
    "raft": {
        "realityCheckPrompt": "Why must any two Raft quorum majorities overlap by at least one node (2Q > N), and how does term monotonicity prevent a partitioned former leader from overwriting committed state?",
        "invariant": "Any two subsets containing floor(N/2) + 1 nodes in a cluster of size N must share at least one node. That overlapping node guarantees that the newest term and committed logs cannot be overwritten.",
        "failureBoundary": "If an even node count (e.g. 4 nodes) splits 2-2, neither partition can form a majority, halting all write operations.",
        "formula": "Fault tolerance F = floor((N - 1) / 2). 3 nodes tolerate 1 crash; 5 nodes tolerate 2 crashes. Even node counts increase cost without adding fault tolerance.",
        "ruleOfThumb": "Always deploy odd cluster sizes (3, 5, 7) for consensus. Implement leader leases and generation term counters before serving linearizable reads.",
        "naiveTrap": "Assuming adding an even node (e.g. 4th node to a 3-node cluster) increases fault tolerance; it actually reduces availability under partitions."
    },
    "crdt": {
        "realityCheckPrompt": "Why does Last-Write-Wins (LWW) with client timestamps inevitably lose data under clock drift, and how do operation-based vs state-based CRDTs guarantee mathematical convergence?",
        "invariant": "Physical wall clocks drift by tens of milliseconds (NTP skew); LWW resolves conflicts by arbitrary timestamp comparison, silently overwriting causally newer offline edits. CRDTs form bounded join-semilattices where all operations are associative, commutative, and idempotent.",
        "failureBoundary": "A client with a fast clock overwrites edits made by all other clients for days into the future.",
        "formula": "Vector Clocks: V_A[i] > V_B[i] implies A causally succeeded B. Concurrent if neither dominates.",
        "ruleOfThumb": "Never use wall-clock timestamps for distributed multi-master conflict resolution. Use State-based (CvRDT) or Delta-CRDTs for offline mobile clients.",
        "naiveTrap": "Relying on client new Date().toISOString() to decide which concurrent mobile edit wins."
    },
    "queue": {
        "realityCheckPrompt": "Why do unbounded in-memory queues cause Out-Of-Memory (OOM) crashes under downstream degradation, and how does an append-only partitioned log decouple slow consumers?",
        "invariant": "Little's Law dictates that queue depth surges linearly when consumer service time spikes. In-memory queues store payload bytes in volatile RAM; disk-backed partitioned logs store immutable streams with client-tracked read offsets.",
        "failureBoundary": "Memory queues hit heap limits, triggering GC pauses and OOM termination, losing all in-flight messages.",
        "formula": "Queue Length L = lambda * W. Under downstream latency spikes from 10ms to 1s at 10,000 msg/s, in-memory queue surges from 100 to 10,000 items instantly.",
        "ruleOfThumb": "Always bound in-memory queues and apply explicit backpressure (rejection or pushback). Use partitioned commit logs (Kafka/Redpanda) for high-throughput decoupled streams.",
        "naiveTrap": "Allowing message queues to grow unbounded in application memory without backpressure."
    }
}

def atomic_write_json(filepath, data):
    dirname = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(dirname, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dirname, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name
    os.replace(temp_name, filepath)

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
        cand = os.path.join(curr, ".system-design")
        if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "manifest.json")):
            return cand
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
                    p_dir = os.path.expanduser(p.get("projectPath", ""))
                    c_inst = os.path.join(p_dir, ".system-design")
                    if os.path.isdir(c_inst):
                        return c_inst
        except Exception:
            pass

    return os.path.abspath(".system-design")

def parse_adrs_from_decisions(decisions_path):
    if not os.path.isfile(decisions_path):
        return []

    try:
        with open(decisions_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    adrs = []
    blocks = re.split(r"\n##\s+(ADR-\d+:[^\n]+)", content)
    for i in range(1, len(blocks), 2):
        header_line = blocks[i].strip()
        body = blocks[i+1] if (i+1) < len(blocks) else ""

        adr_id_match = re.search(r"^(ADR-\d+)", header_line)
        adr_id = adr_id_match.group(1) if adr_id_match else "ADR"
        topic_title_match = re.search(r"^ADR-\d+:\s*(.*?)(?:\s+Architectural Defense)?$", header_line)
        topic_title = topic_title_match.group(1).strip() if topic_title_match else header_line

        date_m = re.search(r"-\s*\*\*Date\*\*:\s*([^\n]+)", body)
        date_str = date_m.group(1).strip() if date_m else ""

        cluster_m = re.search(r"-\s*\*\*Cluster\*\*:\s*([^\n]+)", body)
        cluster_raw = cluster_m.group(1).strip() if cluster_m else "General Systems"

        topic_id_m = re.search(r"-\s*\*\*Topic ID\*\*:\s*`([^`]+)`", body)
        topic_id = topic_id_m.group(1).strip() if topic_id_m else f"topic.{topic_title.lower().replace(' ', '-')}"

        hypo_m = re.search(r"-\s*\*\*Initial Hypothesis\*\*:\s*([^\n]+)", body)
        hypothesis = hypo_m.group(1).strip() if hypo_m else ""

        claim_m = re.search(r"### Invariant Claim & Decision\s*\n+>\s*([^\n]+(?:\n>[^\n]+)*)", body)
        claim = re.sub(r"\n>\s*", " ", claim_m.group(1)).strip() if claim_m else ""

        disc_m = re.search(r"### Trade-Off Discussion & Defense Summary\s*\n+([\s\S]*?)(?=\n###|\Z)", body)
        discussion = disc_m.group(1).strip() if disc_m else ""

        gain_m = re.search(r"-\s*\*\*Guaranteed \(Gain\)\*\*:\s*([^\n]+)", body)
        gain = gain_m.group(1).strip() if gain_m else ""

        tax_m = re.search(r"-\s*\*\*Non-Guarantee \(Tax\)\*\*:\s*([^\n]+)", body)
        tax = tax_m.group(1).strip() if tax_m else ""

        adrs.append({
            "adr_id": adr_id,
            "topic_title": topic_title,
            "topic_id": topic_id,
            "date": date_str,
            "cluster": cluster_raw,
            "hypothesis": hypothesis,
            "claim": claim,
            "discussion": discussion,
            "guarantees": [gain] if gain else [],
            "taxes": [tax] if tax else []
        })

    return adrs

def parse_reality_checks(curriculum_path):
    if not os.path.isfile(curriculum_path):
        return {}

    try:
        with open(curriculum_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    results = {}
    cluster_blocks = re.findall(r"##\s+(?:🔁\s*)?\d+\.\s*\[(.*?)\]\s*([^\n]+)[\s\S]*?### Reality Check[^\n]*\n+([\s\S]*?)(?:\n---|\n##\s|\Z)", content)
    for code, title, block in cluster_blocks:
        code_clean = code.strip()
        items = re.findall(r"-\s*\[\s*\]\s*(.*?)(?:\s*—\s*\*Tick off when:|\n|$)", block)
        clean_items = [it.strip() for it in items if it.strip()]
        if clean_items:
            results[code_clean] = clean_items[0]
            results[title.strip()] = clean_items[0]

    return results

def parse_curriculum_atomic_topics(curriculum_path):
    """Parses individual topic trade-off lines from CURRICULUM.md."""
    if not os.path.isfile(curriculum_path):
        return {}

    try:
        with open(curriculum_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    topics_map = {}
    topic_lines = re.findall(r"-\s*\[[ xX]\]\s*([^\n—]+)\s*—\s*([^\n—]+?)(?:\s*—\s*\*Tick off when:|\n|$)", content)
    for title, desc in topic_lines:
        t_clean = title.strip()
        d_clean = desc.strip()
        if t_clean and d_clean:
            topics_map[t_clean.lower()] = d_clean
    return topics_map

def parse_notes_for_revisions(inst_dir):
    """Extracts derived invariants, hypotheses, rules of thumb, and formulas from synthesized study notes."""
    notes_data = {}
    search_dirs = [
        os.path.join(inst_dir, "notes"),
        os.path.join(os.path.dirname(inst_dir), "notes")
    ]

    for n_dir in search_dirs:
        if not os.path.isdir(n_dir):
            continue
        for root, _, files in os.walk(n_dir):
            for file in files:
                if not file.endswith(".md"):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    title_m = re.search(r"^#\s+(.+)$", content, re.M)
                    title = title_m.group(1).strip() if title_m else ""

                    hypo_m = re.search(r"## 1\.\s+Initial Intuition[^\n]*\n+>\s*([^\n]+(?:\n>[^\n]+)*)", content)
                    hypo = re.sub(r'[\">\*]', '', hypo_m.group(1)).strip() if hypo_m else ""

                    frict_m = re.search(r"## 2\.\s+Dialectic & Friction[^\n]*\n+([\s\S]*?)(?=\n## 3|\Z)", content)
                    frict = frict_m.group(1).strip() if frict_m else ""

                    inv_m = re.search(r"## 3\.\s+Derived Invariant[^\n]*\n+>\s*(?:\*\*Demonstrated Claim\*\*:\s*\n+>\s*)?([^\n]+(?:\n>[^\n]+)*)", content)
                    inv = re.sub(r'[\">\*]', '', inv_m.group(1)).strip() if inv_m else ""

                    table_m = re.search(r"## 4\.\s+Personal Rule of Thumb[^\n]*\n+([\s\S]*?)(?=\n## 5|\n#|\Z)", content)
                    rules = []
                    if table_m:
                        rows = [r.strip() for r in table_m.group(1).split("\n") if r.strip().startswith("|") and not ":---" in r and not "Architectural Trade-Off" in r]
                        for r in rows:
                            cols = [c.strip() for c in r.split("|")[1:-1]]
                            if len(cols) >= 3:
                                rules.append({
                                    "constraint": cols[0].replace("**", ""),
                                    "rule": cols[1],
                                    "bound": cols[2]
                                })

                    key = file.replace(".md", "").lower()
                    notes_data[key] = {
                        "title": title,
                        "hypothesis": hypo,
                        "friction": frict,
                        "invariant": inv,
                        "rules": rules
                    }
                    if title:
                        notes_data[title.lower()] = notes_data[key]
                except Exception:
                    pass

    return notes_data

def find_domain_challenge(topic_id, topic_title):
    search_str = f"{topic_id} {topic_title}".lower()
    for key, challenge in DOMAIN_CHALLENGES.items():
        if key in search_str:
            return challenge
    return None

def sync_revisions(inst_dir=None):
    inst = resolve_instance_dir(inst_dir)
    if not os.path.isdir(inst):
        return {"error": f"Instance directory '{inst}' does not exist"}

    revisions_file = os.path.join(inst, "revisions.json")
    existing_revisions = []
    if os.path.isfile(revisions_file):
        try:
            with open(revisions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_revisions = data.get("revisions", [])
        except Exception:
            existing_revisions = []

    # Map existing by topicId or id
    rev_map = {r.get("topicId") or r.get("id"): r for r in existing_revisions}

    # Add foundational defaults if missing, or backfill new fields if missing
    for d in DEFAULT_FOUNDATIONAL_REVISIONS:
        key = d["topicId"]
        if key not in rev_map:
            rev_map[key] = dict(d)
        else:
            for field in ["realityCheckPrompt", "ruleOfThumb", "formula", "naiveTrap", "failureBoundary", "invariant"]:
                if not rev_map[key].get(field):
                    rev_map[key][field] = d.get(field)

    # Ingest from DECISIONS.md, CURRICULUM.md, and notes/
    decisions_path = os.path.join(inst, "DECISIONS.md")
    curriculum_path = os.path.join(inst, "CURRICULUM.md")
    reality_checks = parse_reality_checks(curriculum_path)
    curriculum_atomic_topics = parse_curriculum_atomic_topics(curriculum_path)
    notes_catalog = parse_notes_for_revisions(inst)
    adrs = parse_adrs_from_decisions(decisions_path)

    # Ingest from manifest
    manifest_path = os.path.join(inst, "manifest.json")
    manifest = {}
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as mf:
                manifest = json.load(mf)
        except Exception:
            pass

    clusters = manifest.get("curriculum", {}).get("clusters", [])
    cluster_lookup = {}
    for c in clusters:
        for t in c.get("topics", []):
            cluster_lookup[t.get("id")] = {
                "clusterId": c.get("id"),
                "clusterTitle": c.get("title"),
                "tierId": c.get("tierId", "tier.0"),
                "tierName": c.get("tierName", "Tier 0 — Network & Transport Mechanics")
            }

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for adr in adrs:
        t_id = adr["topic_id"]
        meta = cluster_lookup.get(t_id, {})
        cluster_title = meta.get("clusterTitle") or adr.get("cluster", "General Systems")
        topic_title = adr["topic_title"]

        # 1. Match from notes catalog
        clean_slug = t_id.replace("topic.", "").lower()
        note_entry = notes_catalog.get(clean_slug) or notes_catalog.get(topic_title.lower()) or {}

        # 2. Match from domain challenges knowledge base
        domain_match = find_domain_challenge(t_id, topic_title) or {}

        # 3. Determine best challenge prompt
        # Priority: Domain Challenge -> Curriculum Reality Check -> Notes friction -> Default
        rc_prompt = None
        if domain_match.get("realityCheckPrompt"):
            rc_prompt = domain_match["realityCheckPrompt"]
        elif reality_checks.get(adr.get("cluster")):
            rc_prompt = reality_checks[adr.get("cluster")]
        elif topic_title.lower() in curriculum_atomic_topics:
            desc = curriculum_atomic_topics[topic_title.lower()]
            rc_prompt = f"For {topic_title}: {desc}. Under what physical failure mode or scale ceiling does a naive design break down, and what invariant guarantees recovery?"

        if not rc_prompt or len(rc_prompt) < 15:
            rc_prompt = f"Defend the core invariant and quantitative trade-off for {topic_title} under hardware/network failure."

        # 4. Determine best invariant
        claim = adr["claim"]
        if not claim or "Verified cold in chat" in claim:
            claim = note_entry.get("invariant") or domain_match.get("invariant") or claim or "Verified operational invariant."

        # 5. Determine failure boundary
        fail_b = domain_match.get("failureBoundary")
        if not fail_b and note_entry.get("friction"):
            fail_b = note_entry["friction"].split("\n")[0].replace("- **", "").replace("**:", ":")
        if not fail_b:
            fail_b = "Evaluated failure modes, boundary constraints, and partition states under high load."

        # 6. Determine formula / sizing invariant
        formula = domain_match.get("formula")
        if not formula and note_entry.get("rules"):
            for r in note_entry["rules"]:
                if r.get("bound"):
                    formula = r["bound"]
                    break
        if not formula:
            formula = "Quantitative trade-off defended during sign-off."

        # 7. Determine rule of thumb
        rule = domain_match.get("ruleOfThumb")
        if not rule and note_entry.get("rules"):
            for r in note_entry["rules"]:
                if r.get("rule"):
                    rule = r["rule"]
                    break
        if not rule:
            rule = f"Apply deterministic invariants to isolate blast radius in {topic_title}."

        # 8. Determine naive trap
        naive_trap = note_entry.get("hypothesis") or domain_match.get("naiveTrap") or adr.get("hypothesis") or f"Assuming naive synchronous approach suffices for {topic_title}."

        item = rev_map.get(t_id) or {}
        item["id"] = f"rev.{t_id.replace('topic.', '')}"
        item["topicId"] = t_id
        item["topicTitle"] = topic_title
        item["tierId"] = meta.get("tierId") or item.get("tierId", "tier.0")
        item["tierName"] = meta.get("tierName") or item.get("tierName", "Systems Architecture")
        item["clusterId"] = meta.get("clusterId") or item.get("clusterId", "cluster.general")
        item["clusterTitle"] = cluster_title
        
        # Override generic placeholders with rich domain/note values
        if not item.get("realityCheckPrompt") or "Defend the core invariant and quantitative" in item.get("realityCheckPrompt", ""):
            item["realityCheckPrompt"] = rc_prompt
        elif rc_prompt and len(rc_prompt) > len(item.get("realityCheckPrompt", "")):
            item["realityCheckPrompt"] = rc_prompt

        if not item.get("invariant") or "Verified cold in chat defense" in item.get("invariant", ""):
            item["invariant"] = claim

        if not item.get("failureBoundary") or "Evaluated failure modes and partition bounds" in item.get("failureBoundary", ""):
            item["failureBoundary"] = fail_b

        if not item.get("formula") or "Quantitative trade-off defended" in item.get("formula", ""):
            item["formula"] = formula

        if not item.get("ruleOfThumb") or "Apply deterministic invariants" in item.get("ruleOfThumb", ""):
            item["ruleOfThumb"] = rule

        if not item.get("naiveTrap") or "Assuming naive synchronous approach" in item.get("naiveTrap", ""):
            item["naiveTrap"] = naive_trap
        item["defenseAnswer"] = adr["discussion"] or note_entry.get("friction") or item.get("defenseAnswer", "Verified cold in chat defense without notes.")
        
        if adr.get("guarantees"):
            item["guarantees"] = adr["guarantees"]
        if adr.get("taxes"):
            item["taxes"] = adr["taxes"]

        item["masteryStatus"] = item.get("masteryStatus") or "mastered"
        item["lastReviewed"] = item.get("lastReviewed") or adr.get("date") or today_str
        item["reviewCount"] = item.get("reviewCount", 0)
        item["streak"] = item.get("streak", 1 if item["masteryStatus"] == "mastered" else 0)
        item["source"] = adr["adr_id"]

        # Calculate next review date if missing
        if not item.get("nextReviewDate"):
            interval = 7 if item["masteryStatus"] == "mastered" else (3 if item["masteryStatus"] == "proficient" else 1)
            next_d = datetime.date.today() + datetime.timedelta(days=interval)
            item["nextReviewDate"] = next_d.strftime("%Y-%m-%d")

        rev_map[t_id] = item

    # Compile result list and compute stats
    today_date = datetime.date.today()
    final_list = list(rev_map.values())
    
    due_count = 0
    mastered_count = 0
    learning_count = 0
    needs_review_count = 0

    for r in final_list:
        # Check due status
        next_d_str = r.get("nextReviewDate")
        is_due = True
        if next_d_str:
            try:
                parts = [int(p) for p in next_d_str.split("-")]
                card_date = datetime.date(parts[0], parts[1], parts[2])
                is_due = (card_date <= today_date)
            except Exception:
                is_due = True
        r["isDue"] = is_due
        if is_due:
            due_count += 1

        status = r.get("masteryStatus", "learning")
        if status == "mastered":
            mastered_count += 1
        elif status in ["learning", "proficient"]:
            learning_count += 1
        elif status == "needs_review":
            needs_review_count += 1

    payload = {
        "$schemaVersion": "1.0",
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "totalRevisions": len(final_list),
        "dueCount": due_count,
        "masteredCount": mastered_count,
        "learningCount": learning_count,
        "needsReviewCount": needs_review_count,
        "revisions": final_list
    }

    atomic_write_json(revisions_file, payload)
    return payload

def main():
    parser = argparse.ArgumentParser(description="Revision Mode Compiler for System Design Studio")
    parser.add_argument("--instance-dir", help="Path to .system-design directory")
    parser.add_argument("--sync", action="store_true", help="Sync revisions from DECISIONS.md and notes")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    parser.add_argument("--update-mastery", nargs=2, metavar=("REVISION_ID", "STATUS"), help="Update mastery status (needs_review, learning, mastered)")

    args = parser.parse_args()
    inst = resolve_instance_dir(args.instance_dir)

    if args.update_mastery:
        rev_id, status = args.update_mastery
        revisions_file = os.path.join(inst, "revisions.json")
        if os.path.isfile(revisions_file):
            try:
                with open(revisions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                updated = False
                today = datetime.date.today()
                interval = 1 if status == "needs_review" else (3 if status in ["learning", "proficient"] else 7)
                next_d = (today + datetime.timedelta(days=interval)).strftime("%Y-%m-%d")

                for r in data.get("revisions", []):
                    if r.get("id") == rev_id or r.get("topicId") == rev_id:
                        r["masteryStatus"] = status
                        r["lastReviewed"] = today.strftime("%Y-%m-%d")
                        r["nextReviewDate"] = next_d
                        r["reviewCount"] = r.get("reviewCount", 0) + 1
                        updated = True
                        break
                if updated:
                    atomic_write_json(revisions_file, data)
                    print(f"✅ Updated {rev_id} status to '{status}'")
            except Exception as e:
                print(f"❌ Failed to update mastery: {e}", file=sys.stderr)
                sys.exit(1)
        return

    res = sync_revisions(inst)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("=" * 76)
        print("  SYSTEM DESIGN STUDIO — REVISION MODE SYNC")
        print("=" * 76)
        print(f"📁 Instance State:    {inst}")
        print(f"🧠 Total Flashcards:  {res.get('totalRevisions', 0)}")
        print(f"⏰ Due for Review:    {res.get('dueCount', 0)}")
        print(f"🏆 Mastered:          {res.get('masteredCount', 0)}")
        print(f"⏱️  Last Synchronized: {res.get('lastUpdated')}")
        print("=" * 76)

if __name__ == "__main__":
    main()
