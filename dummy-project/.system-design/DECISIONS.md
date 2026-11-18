# Architecture Decision Records (ADRs)

## ADR-001: TCP vs UDP Architectural Defense
- **Date**: 2026-11-18
- **Cluster**: 1. [0.1] APIs & Network Transport for Design (`0.1`)
- **Topic ID**: `topic.0.1.tcp-vs-udp`
- **Status**: Accepted (Verified Sign-Off Gate)

### Context & Problem Statement
Evaluating architectural choices under physical network/hardware boundaries, uncoordinated failure modes, and latency floors.
- **Initial Hypothesis**: Initially assumed UDP streaming was fragile; proved jitter buffers and PLC absorb drops without stalling the decoder

### Invariant Claim & Decision
> Defended TCP monotonic byte stream and socket buffer backpressure against HoL blocking cold in chat under 1% loss model

### Trade-Off Discussion & Defense Summary
Analyzed packet loss scenarios, socket memory boundaries, and why YouTube live streaming uses WebRTC/UDP while VoD uses HLS/TCP

### Consequences & Non-Negotiable Invariants
- **Guaranteed (Gain)**: Verified operational ordering, bounded blast radius, and deterministic recovery.
- **Non-Guarantee (Tax)**: Coordination overhead, queueing jitter under packet loss, and protocol complexity.

---

