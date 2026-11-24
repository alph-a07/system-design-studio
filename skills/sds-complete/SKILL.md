---
name: sds-complete
description: Complete topic sign-off with self evaluation, record decision (ADR), and compile active-learning notes in System Design Studio.
argument-hint: "[evidence]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.2.0
---

# /sds-complete — Topic Sign-Off & Active-Learning Note Synthesis

Verify that the learner has achieved closure on the topic trade-offs through self evaluation, tick off the topic, advance `CURSOR.md`, record an ADR in `DECISIONS.md`, and compile discussion-synthesized study notes. Learners conclude on their terms once they have internal closure.

## Strict Active Project Context Isolation Invariant

- **ZERO EXTERNAL PROJECT CONTEXT**: Record and verify sign-off strictly within the active project workspace (`.system-design/CURSOR.md`, `.system-design/DECISIONS.md`, `.system-design/CURRICULUM.md`, `notes/`).
- Never pull context or reference external projects in `~/.system-design-studio/projects/`. Treat every project as an independent, self-contained learning environment.

## Agentic Notes Pipeline (Crafter ➔ Auditor ➔ Deterministic Markdown Render)

When `autoGenerateNotes` is enabled, notes are authored agentically rather than mechanically:
1. **`sds-notes-crafter` (Subagent)**: Synthesizes the topic context, the user's self-evaluation answers, saved highlights (`.system-design/highlights/`), any existing manual notes in `notes/`, all additional discussions since `/sds-teach`, and prior adaptiveness history (`.system-design/notes-adaptiveness.json`). Writes `.system-design/.generated-note-<slug>.json` and appends an adaptiveness decision entry to `.system-design/notes-adaptiveness.json`.
2. **`sds-pedagogy-auditor` (Notes Audit Mode)**: Audits `.system-design/.generated-note-<slug>.json` against topic context, user context, `.system-design/notes-adaptiveness.json`, zero learning-process leakage, decorative-only highlight colors, and future-safety (ensuring effortless re-reads months later).
3. **`generate-notes.py` (Deterministic Renderer)**: Once `sds-pedagogy-auditor` returns `APPROVED`, `advance-cursor.py --notes-data-file .system-design/.generated-note-<slug>.json` deterministically compiles the signed-off JSON into clean Markdown under `notes/`.

## Mandatory Architectural Invariants

1. **SELF EVALUATION & CLOSURE (CONCLUDE ON YOUR TERMS)**:
   - You MUST inspect `.system-design/CURRICULUM.md` for the active topic's tick-off requirement (`— *Tick off when:*`).
   - Confirm that the learner has achieved internal closure and articulated the physical invariants and trade-offs.
   - Learners conclude on their terms: once they have clarity and confidence in the trade-offs, approve the sign-off and seal the record into Git.

2. **CONTEXTUAL, FRICTIONLESS, FUTURE-SAFE NOTE GOVERNANCE**:
   - Notes MUST read as clean, direct technical reference documents built for effortless re-reads months later—never leaking meta-commentary about the learning/study process.
   - Highlight colors (`yellow`, `emerald`, `cyan`) are purely decorative—never assign semantic meanings to colors.

## Execution Sequence

1. **Verify Evidence & Closure**:
   - Ensure the learner has addressed the core tick-off criterion from `CURRICULUM.md` and reached internal closure.

2. **Invoke `sds-notes-crafter` (when `autoGenerateNotes` is enabled)**:
   - Pass the active topic ID, self-evaluation answers, any post-`sds-teach` discussions from chat, and instruct it to read `.system-design/highlights/`, any existing manual note in `notes/`, `.system-design/lessons/.generated-<slug>.json`, and `.system-design/notes-adaptiveness.json`.
   - `sds-notes-crafter` writes `.system-design/.generated-note-<slug>.json` and logs its adaptiveness decision in `.system-design/notes-adaptiveness.json`.

3. **Invoke `sds-pedagogy-auditor` (Notes Audit Mode)**:
   - Audit `.system-design/.generated-note-<slug>.json` against topic context, user context, `.system-design/notes-adaptiveness.json`, zero leakage, and future-safety.
   - If `REVISIONS_REQUIRED`, route fixes back to `sds-notes-crafter` until `APPROVED`.

4. **Execute State Advance & Deterministic Markdown Render**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/advance-cursor.py \
     --complete-topic <topic-id> \
     --evidence "$ARGUMENTS" \
     --hypothesis "<core context / initial framing>" \
     --discussion-summary "<key failure modes and edge cases explored>" \
     --notes-data-file .system-design/.generated-note-<slug>.json
   ```

5. **Verify Generated Artifacts**:
   - Confirm `CURRICULUM.md` shows `[x]`.
   - Confirm `DECISIONS.md` has logged a new ADR.
   - If auto-notes is enabled, confirm `notes/` contains the newly compiled study note: `[Open Study Note](file:///<path-to-note.md>)`. If disabled, remind learner that notes can be compiled manually on demand via `/sds-notes`.
   - Note the atomic Git commit created in your local repository (`sds(learn): complete ...`).
