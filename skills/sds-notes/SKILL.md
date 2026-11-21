---
name: sds-notes
description: List or view project-scoped active learning study notes with clickable links in System Design Studio.
argument-hint: "[topic]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.5.0
---

# /sds-notes

Display direct clickable links (`file:///...`) to all active-learning study notes generated in this project, or read and edit notes live in the visual dashboard on `http://localhost:8420`.

## Value to User
- **Knowledge Retention**: Access synthesized study notes combining your initial intuition, cold dialectic friction, and verified physical sizing rules.
- **Auto vs. Manual Control**: When `autoGenerateNotes` is enabled, notes compile seamlessly on completion. If disabled, generate notes on demand whenever you want.

## Instructions

1. **List project notes**:
   ```bash
   sds notes
   ```
2. **Manually generate or recompile a note** (e.g. when auto-notes is disabled):
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/generate-notes.py --topic-id [topic]
   ```
3. **Display structured note links**:
   - Format results as a tidy table or bullet list organized by Tier and Cluster.
   - Use absolute file links: `[<note-name>](file:///<path-to-note.md>)`.
   - Notes contain the 4 active-learning sections: Initial Hypothesis, Dialectic Friction, Derived Invariant, and Personal Rules of Thumb.
