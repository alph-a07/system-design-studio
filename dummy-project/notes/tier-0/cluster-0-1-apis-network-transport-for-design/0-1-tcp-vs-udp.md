# TCP vs UDP
**Hierarchy**: Tier 0 ➔ 1. [0.1] APIs & Network Transport for Design
**Verified Date**: 2026-11-19 | **Status**: Verified Sign-Off (Active Learning Synthesis)

## 1. Initial Intuition & Working Hypothesis
> *"Assumed critical RPCs should universally mandate TCP for reliability, treating packet loss purely as a transport concern transparent to application latency."*

*The mental model or operational assumption held prior to exploring boundary constraints and failure states.*

## 2. Dialectic & Friction Encountered
- **The Socratic Stress Test**: Challenged the working assumption against uncoordinated hardware crashes, trans-oceanic network jitter, and concurrent race conditions.
- **Where the Model Broke**: When packet loss or node membership churn occurred, the naive approach experienced catastrophic tail latency or state divergence.
- **The Core Trade-Off Exposed**: Discovered that zero coordination cannot coexist with strong invariants—every architectural guarantee demands a specific tax in latency, buffer memory, or operational complexity.

*The critical failure modes, counter-examples, or physical bottlenecks that challenged the initial hypothesis during active Socratic defense.*

## 3. Derived Invariant (The 'Aha!' Synthesis)
> **Demonstrated Claim**:
> *"Proved unassisted that TCP vs UDP enforces deterministic causal ordering and bounded blast radius by strictly decoupling volatile state from the critical write path."*

*What was personally deduced, proved cold, and internalized through active dialectic—the non-negotiable physical or mathematical invariant.*

## 4. Personal Rule of Thumb & Sizing Reality
| Architectural Trade-Off / Constraint | Operational Decision Rule | Production Bound / Sizing Invariant |
| :--- | :--- | :--- |
| **Ordering vs. Head-of-Line Blocking** | Use single-stream TCP when sequential byte-stream order is strictly mandatory. When concurrent independent requests share a lossy link, switch to QUIC/multiplexed UDP so packet loss on stream A never stalls stream B. | RTT latency floor (~5 μs/km silica). Bandwidth-Delay Product (BDP = RTT × Bandwidth) dictates buffer sizing; standard 64KB window caps 10Gbps link at 50ms RTT to ~10Mbps. |
| **Connection Lifecycle & Handshake Tax** | Avoid establishing fresh TCP handshakes (1 RTT) + TLS (1-2 RTTs) on the critical RPC path. Maintain persistent, warmed connection pools with keep-alives. | SYN flood backlog limits; TCP TIME_WAIT socket exhaustion (~60s socket recycle) limits ephemeral port pool (65,535). |
