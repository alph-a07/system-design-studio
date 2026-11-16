---
name: sds-discuss
description: Engage in active learning Socratic dialectic and stress-test trade-off defense in System Design Studio.
argument-hint: "[defense]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-discuss

Stress-test the learner's architectural mental model and trade-off defense against physical constraints, latency bounds, and edge-case failure modes without revealing the hidden sign-off gate.

## Instructions

1. **Capture learner's intuition or defense**:
   - Extract reasoning from `$ARGUMENTS` or conversational chat history.
2. **Review cognitive anchors**:
   - Inspect `.system-design/CURSOR.md` to identify verified prerequisites and established hardware invariants.
3. **Socratic stress-testing**:
   - Probe cold failure modes: network partitions, head-of-line blocking, cascading timeouts, queue backpressure.
   - For senior engineers: require concrete back-of-envelope math (bandwidth-delay product, disk IOPS bounds, Little's Law).
   - For hesitant engineers: provide Socratic scaffolding questions without giving away the answer.
4. **Trace the boundary**:
   - Identify precisely where the learner's initial hypothesis breaks down to guide them to the derived invariant.
