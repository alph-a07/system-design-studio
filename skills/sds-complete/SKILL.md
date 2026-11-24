---
name: sds-complete
description: Complete topic sign-off with self evaluation, record decision (ADR), and compile active-learning notes in System Design Studio.
argument-hint: "[evidence]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.1.1
---

# /sds-complete — Topic Sign-Off & Active-Learning Note Synthesis

Verify that the learner has achieved closure on the topic trade-offs through self evaluation, tick off the topic, advance `CURSOR.md`, record an ADR in `DECISIONS.md`, and compile discussion-synthesized study notes. Learners conclude on their terms once they have internal closure.

## Strict Active Project Context Isolation Invariant

- **ZERO EXTERNAL PROJECT CONTEXT**: Record and verify sign-off strictly within the active project workspace (`.system-design/CURSOR.md`, `.system-design/DECISIONS.md`, `.system-design/CURRICULUM.md`, `notes/`).
- Never pull context or reference external projects in `~/.system-design-studio/projects/`. Treat every project as an independent, self-contained learning environment.

## Agentic Optimization: Deterministic Local Synthesis
Rather than burning thousands of LLM tokens on trivial file formatting:
- Note compilation (`compile-notes.py`) and revision card generation (`update-revisions.py`) are deterministically triggered by `advance-cursor.py` in under 15ms with 0 LLM token cost.
- The coordinator extracts the learner's recorded hypothesis and discussion summary directly from the chat context into the advance command.

## Mandatory Architectural Invariants

1. **SELF EVALUATION & CLOSURE (CONCLUDE ON YOUR TERMS)**:
   - You MUST inspect `.system-design/CURRICULUM.md` for the active topic's tick-off requirement (`— *Tick off when:*`).
   - Confirm that the learner has achieved internal closure and articulated the physical invariants and trade-offs.
   - Learners conclude on their terms: once they have clarity and confidence in the trade-offs, approve the sign-off and seal the record into Git.

2. **ACTIVE LEARNING NOTE GOVERNANCE**:
   - The compiled study note MUST reflect **what the learner understood through self evaluation**, NOT passive textbook summaries.
   - You MUST extract:
     1. The learner's initial hypothesis from the start of the topic.
     2. The friction points and edge cases explored during the lesson.
     3. The derived invariant they proved cold.
     4. Concrete personal rules of thumb and sizing formulas.

## Execution Sequence

1. **Verify Evidence & Closure**:
   - Ensure the learner has addressed the core tick-off criterion from `CURRICULUM.md` and reached internal closure.

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
