# Living Teaching Cursor & Running Context

> **Role**: The operational brain of this learning instance. It is not merely a progress tracker, but the running cognitive state tracking what was taught, at what depth, what examples and metaphors were established, what forward questions are deferred, and how current mechanisms connect backwards and forwards to preserve an unbroken mental model across sessions, models, and agents.

---

## 1. Active Focus & Immediate Pedagogical Horizon

- **Curriculum**: System Design Mastery Roadmap — LLD, HLD & Mobile (`curriculum.system-design-mastery`)
- **Active Tier**: Tier 0 — HLD Building Blocks (Prerequisite Slice)
- **Active Cluster**: 1. [0.1] APIs & Network Transport for Design (`cluster.0.1`)
  - *Cluster Depth Target*: `[concept][contrast][trap]` | *Depends on*: None
  - *Cluster Reality Checks to Pass Cold*:
    1. *"For each provider API Anchor calls, do you know whether it paginates by page number, cursor or link header — and what your loop does if the list shifts mid-fetch?"*
    2. *"Explain how a retry after a timeout can double-charge without an idempotency key. Where exactly is the ambiguity: client, network, or server?"*
- **Active Topic**: **TCP vs UDP — what reliability costs, and why real-time media often picks UDP** (`topic.0.1.tcp-vs-udp`)
  - *Target Depth*: `[concept][mechanics][contrast][trap]`
  - *Topic Foundation Status*: `not-started`
  - *Active Mechanism Group*: Transport Reliability, Byte-Streams & Datagram Delivery (`group.0.1.tcp-udp-foundations`)
  - *Group Status*: `queued`
  - *Last Checkpoint*: `none` (`not-issued`)
  - *Immediate Next Teaching Action*: Deliver Topic 0.1 Foundation:
    1. **Pre-Protocol Physical Facts**: Separate machines, asynchronous physical networks, non-zero speed of light, packet loss, reordering, and duplicate delivery.
    2. **TCP Causal Mechanics**: Sequence space, cumulative ACKs, sliding window retransmission buffers, and the latency/jitter cost of guaranteed in-order byte streams.
    3. **UDP Contrast & Real-Time Trade-off**: Raw datagram boundaries, zero kernel retransmission queues, and why VoIP/WebRTC prefers dropping a late audio/video packet over stalling the stream.

---

## 2. Connected Cognitive Lineage (Causal Anchors)

- **Backward Anchor (Where we came from & Why)**:
  - *Starting Line*: Entry point into Tier 0. No prior topics covered yet.
  - *First Principles Origin*: Ground reasoning in physical network realities before abstracting into systems.
- **Active Mechanism & Causal Spine**:
  - Establishing the fundamental boundary between the IP network layer (unreliable packet routing) and transport protocols (TCP byte-stream abstraction vs UDP datagram abstraction).
- **Forward Hook (Where this leads next)**:
  - Connects to HTTP/1.1 vs HTTP/2 vs HTTP/3 (`topic.0.1.http-hol-blocking`) to trace head-of-line blocking across protocol layers.

---

## 3. Examples Registry & Metaphor Continuity (`examplesTaken`)

*Tracks all concrete domain scenarios used, ensuring continuity without random analogy thrashing.*

- **Active Metaphor Strategy**: Financial Ledger (ordered/reliable) vs Live Audio/Video Stream (loss-tolerant/low-jitter).
- **Logged History**: *(Clean slate)*

---

## 4. Deferred Topics Queue (`deferredQueue`)

*Tracks forward questions intentionally postponed to future milestones with formal anchor notes.*

- *(Queue currently empty)*

---

## 5. Covered Topics, Depth & Invariant Audit

| Topic ID | Topic Name | Depth Covered | Core Invariants & Guarantees Established | Revisit Triggers |
| :--- | :--- | :--- | :--- | :--- |
| *(None covered yet)* | — | — | — | — |

- **Unresolved Foundations / Misconceptions to Repair**: None currently diagnosed.
- **Divergence Log / Weak Areas**: None logged yet.

---

## 6. Visual Artifacts & Active Diagrams

- **Visual Backend Engine**: `mermaid` (saving locally to `.system-design/diagrams/`)
- **Active Diagrams in Workspace**: None yet.
- **Immediate Planned Visual**: Side-by-side sequence timeline comparing TCP packet loss retransmission stall vs UDP datagram drop in `.system-design/diagrams/diagram.0.1.tcp-udp-delivery.mmd`.

---

## 7. Upcoming Cluster Roadmap & Horizon: [0.1] APIs & Network Transport

- [ ] **CURRENT** ➔ **1. TCP vs UDP** — what reliability costs, and why real-time media often picks UDP
- [ ] 2. HTTP/1.1 vs HTTP/2 vs HTTP/3 — where head-of-line blocking lives at each layer and why QUIC moved to UDP
- [ ] 3. TLS handshake cost and session resumption — why connection reuse matters on cellular
- [ ] 4. REST vs gRPC vs GraphQL — payload shape, coupling, cacheability, tooling tradeoffs
- [ ] 5. Polling vs long-polling vs SSE vs WebSocket — connection cost vs latency
- [ ] 6. Pagination: offset vs cursor/keyset — why offset skips/duplicates under writes and degrades at depth
- [ ] 7. Idempotency — which HTTP methods are idempotent, idempotency keys for unsafe operations, why retries make this mandatory
- [ ] 8. API versioning and backward compatibility — additive changes, tolerant readers
