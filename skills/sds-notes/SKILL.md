---
name: sds-notes
description: List or view project-scoped active learning study notes with clickable links in System Design Studio.
argument-hint: "[topic]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-notes

Display direct clickable links (`file:///...`) to all active-learning study notes generated in this project.

## Instructions

1. **Query project notes index**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/manage-projects.py notes
   ```
2. **Display structured note links**:
   - Format results as a tidy table or bullet list organized by Tier and Cluster.
   - Use absolute file links: `[<note-name>](file:///<path-to-note.md>)`.
   - Notes contain the 4 active-learning sections: Initial Hypothesis, Dialectic Friction, Derived Invariant, and Personal Rules of Thumb.
