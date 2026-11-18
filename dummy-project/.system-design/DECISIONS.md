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

## ADR-002: HTTP/1.1 vs HTTP/2 vs HTTP/3 Architectural Defense
- **Date**: 2026-11-18
- **Cluster**: 1. [0.1] APIs & Network Transport for Design (`0.1`)
- **Topic ID**: `topic.0.1.http-1-1-vs-http-2-vs-http-3`
- **Status**: Accepted (Verified Sign-Off Gate)

### Context & Problem Statement
Evaluating architectural choices under physical network/hardware boundaries, uncoordinated failure modes, and latency floors.
- **Initial Hypothesis**: Assumed HTTP/2 multiplexing completely solved Head-of-Line blocking; discovered TCP single-loss kernel queue stalls freeze all parallel streams

### Invariant Claim & Decision
> Derived TCP-level head-of-line blocking in HTTP/2 single connection multiplexing; verified QUIC independent stream frames over UDP cold in chat

### Trade-Off Discussion & Defense Summary
Analyzed packet loss curves: at 2% loss HTTP/1.1 with 6 parallel connections actually outperforms HTTP/2; QUIC eliminates transport-layer HoL blocking while keeping stream dependencies

### Consequences & Non-Negotiable Invariants
- **Guaranteed (Gain)**: Verified operational ordering, bounded blast radius, and deterministic recovery.
- **Non-Guarantee (Tax)**: Coordination overhead, queueing jitter under packet loss, and protocol complexity.

---

