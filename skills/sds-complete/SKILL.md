---
name: sds-complete
description: Verify defense against unannounced gate, sign off topic, record decision, and compile active-learning notes in System Design Studio.
argument-hint: "[evidence]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.5.0
---

# /sds-complete — Topic Sign-Off & Active-Learning Note Synthesis

Verify that the learner has defended the unannounced gate scenario, tick off the topic, advance `CURSOR.md`, record an ADR in `DECISIONS.md`, and compile discussion-synthesized study notes.

## Agentic Optimization: Deterministic Local Synthesis
Rather than burning thousands of LLM tokens on trivial file formatting:
- Note compilation (`compile-notes.py`) and revision card generation (`update-revisions.py`) are deterministically triggered by `advance-cursor.py` in under 15ms with 0 LLM token cost.
- The coordinator extracts the learner's recorded hypothesis and dialectic friction directly from the chat context into the advance command.

## Mandatory Architectural Invariants

1. **UNASSISTED GATE VERIFICATION (MANDATORY DEFENSE)**:
   - You MUST inspect `.system-design/CURRICULUM.md` for the active topic's tick-off requirement (`— *Tick off when:*`).
   - You MUST NOT approve sign-off unless the learner has independently articulated the physical invariants and trade-offs in chat.

2. **ACTIVE LEARNING NOTE GOVERNANCE**:
   - The compiled study note MUST reflect **what the learner understood through the dialectic**, NOT passive textbook summaries.
   - You MUST extract:
     1. The learner's initial hypothesis from the start of the topic.
     2. The friction points and edge cases where that hypothesis broke down.
     3. The derived invariant they proved cold.
     4. Concrete personal rules of thumb and sizing formulas.

## Execution Sequence

1. **Verify Evidence & Defense**:
   - Compare the learner's chat defense against the hidden criterion in `CURRICULUM.md`.

2. **Execute State Advance**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/advance-cursor.py \
     --complete-topic <topic-id> \
     --evidence "$ARGUMENTS" \
     --hypothesis "<initial hypothesis from chat>" \
     --discussion-summary "<dialectic friction and edge cases explored>"
   ```

3. **Verify Generated Artifacts**:
   - Confirm `CURRICULUM.md` shows `[x]`.
   - Confirm `DECISIONS.md` has logged a new ADR.
   - If auto-notes is enabled, confirm `notes/` contains the newly compiled study note: `[Open Study Note](file:///<path-to-note.md>)`. If disabled, remind learner that notes can be compiled manually on demand via `/sds-notes`.
   - Note the atomic Git commit created in your local repository (`sds(learn): complete ...`).
