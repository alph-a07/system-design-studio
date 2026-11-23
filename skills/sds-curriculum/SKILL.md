---
name: sds-curriculum
description: Inspect, customize, or reorder curriculum tracks or import BYO syllabus in System Design Studio.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.1.0
---

# /sds-curriculum

Inspect active syllabus, navigate hierarchical topic codes, filter curated study tracks, or import a custom Markdown syllabus adhering to the 3-level taxonomy (`Tier > Cluster > Topic`).

## Curriculum Taxonomy & Indexing Nomenclature

System Design Studio organizes systems engineering concepts into a deterministic, 3-level indexing structure:

```
Tier (e.g., Tier 0, Tier 1, Tier 2, Tier 3, Tier 4)
  └── Cluster Code (e.g., 0.1, 1.2, 2.3)
        └── Topic Index Code (e.g., 0.1.1, 1.2.3, 2.3.1)
```

### Canonical Tiers
- **Tier 0 — High-Level Design (HLD) Building Blocks** (`T0`): Transport protocols, database indexes & isolation, caching primitives, blob storage, async queues.
- **Tier 1 — Low-Level Design (LLD) & In-Process Architecture** (`T1`): Domain modeling, invariants & ownership, SOLID patterns, in-process concurrency, buffers & memory safety.
- **Tier 2 — High-Level Design (HLD) & Distributed Systems** (`T2`): Scalability, data partitioning, replication, consensus (Raft/Paxos), distributed transactions, coordination.
- **Tier 3 — Mobile & Offline-First Systems** (`T3`): Client state, local persistence, delta sync engines, CRDTs, battery & bandwidth invariants, offline queues.
- **Tier 4 — Production Architecture Reviews & ADR Defenses** (`T4`): Failure injection, Socratic stress tests, board-level trade-off defense, ADR portfolio synthesis.

### Curated Study Tracks
When working with learners, offer curated focus tracks to simplify the 354-topic surface:
- **`full-mastery`**: All 50 clusters across Tiers 0–4.
- **`interview-sprint`**: 15 high-yield clusters (`0.1`, `0.2`, `0.3`, `0.4`, `0.5`, `1.1`, `1.2`, `1.3`, `2.1`, `2.2`, `2.3`, `2.4`, `2.5`, `2.7`, `2.10`).
- **`distributed-systems`**: Core infrastructure deep dive (Tiers 0 & 2).
- **`mobile-offline`**: Edge and client resilience deep dive (Tiers 0 & 3).

## Instructions

1. **Inspect active syllabus & living cursor**:
   - Read `.system-design/CURSOR.md` and `.system-design/manifest.json`.
   - Output active topic with its clean index code (e.g., `0.1.3: TLS handshake cost and session resumption`).
   - Present progress: verified count, cluster completion, and tier distribution.
2. **Handle direct topic code lookups**:
   - When a user supplies an index code (e.g., `/sds-teach 0.1.1` or `/sds-complete 2.1.3`), resolve it to its corresponding cluster code (`0.1`) and topic ID (`topic.0.1.tcp-vs-udp`).
3. **Handle track switching or custom BYO import**:
   - To switch active track or prune clusters:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/configure-curriculum.py \
       --track <interview-sprint|distributed-systems|mobile-offline|full-mastery> \
       --output-dir .system-design
     ```
   - To import a custom Markdown syllabus:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/import-curriculum.py \
       --input <syllabus-file.md> \
       --instance-dir .system-design \
       --auto-fix
     ```
