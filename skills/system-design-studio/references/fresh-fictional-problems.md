# Fresh, Fictional Design Problem Invention

## The Golden Rule

**The default source of every design exercise, workshop, case study, and interview challenge must be a newly invented, self-contained fictional problem.**

Under no circumstances should the tutor mine, adapt, derive, extrapolate from, or populate a design problem using:
- The learner's proprietary employer systems or production code.
- Personal repositories or private side-projects detected in the workspace.
- Specific company architectures discussed in passing.

### Why This Rule Is Absolute:
1. **IP & Privacy Protection**: Prevents accidental leakage of confidential employer constraints, architecture, or credentials into shared boards, cloud logs, or public canvases.
2. **Pedagogical Superiority (True Transfer)**: When students work on their familiar day-job systems, they rely on memorized organizational habits rather than deriving architecture from first principles. Fresh fictional domains force pure engineering reasoning.

---

## How to Invent High-Fidelity Fictional Domains

A good fictional domain has:
- A realistic physical or business constraint.
- Concrete scale numbers that actually force architectural decisions.
- Clear functional requirements and explicit non-goals.

### Diverse Domain Inspiration Archetypes:

| Archetype | Sample Fictional Problem | Architectural Forces Exposed |
| :--- | :--- | :--- |
| **Edge / IoT Mesh** | **Global Deep-Sea Seismic Sensor Mesh**: 100,000 underwater buoys recording acoustic pressure; intermittent acoustic modems; battery constraints. | Eventual consistency, offline-first sync, compression, lossy gossip protocols. |
| **High-Throughput Routing** | **Autonomous Agricultural Drone Swarm Dispatcher**: 10,000 drones harvesting crops in real time; continuous GPS telemetry; obstacle avoidance consensus. | Low-latency spatial indexing (geohash / quadtrees), distributed locking, Raft quorums. |
| **Strict Ordering / Ledger** | **Cross-Border Interbank Carbon Credit Clearinghouse**: Financial settlement across 50 international banks; strict audit trail; zero double-spend. | Idempotency, two-phase commit, linearizable logs, cryptographic tamper-proofing. |
| **Burst / Heavy Media** | **Orbital Satellite Earth-Observation Image Ingestion**: Satellites dumping 50GB multispectral imagery chunks during 8-minute ground station passes. | Chunked uploads, resumable protocols, backpressure, distributed object storage, presigned URLs. |
| **Real-Time Collaboration** | **Interactive Musical Score Co-Editing Canvas**: Thousands of musicians collaborating on orchestral scores; sub-30ms local latency. | Conflict-Free Replicated Data Types (CRDTs), Operational Transformation (OT), WebSockets. |

---

## The Brief Construction Checklist

Before presenting any invented exercise to the learner, verify:
- [ ] **Actors & Boundaries**: Who uses it? (Human users, automated IoT agents, external APIs).
- [ ] **Functional Scope**: Exactly 2 to 3 core capabilities (do not overload the prompt with 15 features).
- [ ] **Scale Assumptions**: State explicit numbers:
  - *Read QPS & Write QPS* (e.g. 50,000 writes/sec, 500 reads/sec).
  - *Data Volume & Retention* (e.g. 1 KB payload = 50MB/sec = ~4.3TB/day; 90-day retention).
  - *Latency SLA* (e.g. p99 < 50ms for ingestion).
- [ ] **Clear Failure Mode to Solve**: Introduce the specific bottleneck that forces the lesson's concept.

---

## Explicit Permission Exception

An actual learner project may be used **only when the learner explicitly requests an architecture review or design consultation for that specific project**.
- Even then, the permission applies **only to that bounded conversation turn**.
- It does NOT grant permission to reuse that project's domain for future curriculum exercises or upload confidential architecture to link-shared visual boards.
