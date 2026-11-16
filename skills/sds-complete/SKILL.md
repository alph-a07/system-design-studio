---
name: sds-complete
description: Verify defense against unannounced gate, sign off topic, record decision, and compile active-learning notes in System Design Studio.
argument-hint: "[evidence]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-complete

Verify that the learner has defended the unannounced gate scenario in CURRICULUM.md, tick off the topic, advance CURSOR.md, record an ADR in DECISIONS.md, and synthesize active-learning notes.

## Instructions

1. **Verify unannounced gate**:
   - Inspect `.system-design/CURRICULUM.md` for the active topic's hidden tick-off requirement (`— *Tick off when:*`).
   - Confirm that the learner has independently defended the trade-off in chat without assistance.
2. **Execute state advance**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/advance-cursor.py \
     --complete-topic <topic-id> \
     --evidence "$ARGUMENTS" \
     --hypothesis "<learner's initial hypothesis>" \
     --discussion-summary "<summary of discussion>"
   ```
3. **Confirm file-backed updates**:
   - `CURRICULUM.md`: active topic marked `[x]`.
   - `CURSOR.md`: active topic updated to next syllabus item; anchors recorded.
   - `DECISIONS.md`: ADR added with context, decision, and consequences.
   - `notes/`: active learning study note compiled according to `notesStructure` (`per-topic`, `per-cluster`, `per-tier`, `single-file`).
