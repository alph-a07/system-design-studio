---
name: sds-open
description: Switch active project learning instance context to another project in System Design Studio.
argument-hint: "<project-name>"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.2.0
---

# /sds-open

Switch the active learning instance context to the specified project.

## Instructions

1. **Switch active project in registry**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/manage-projects.py switch "$ARGUMENTS"
   ```
2. **Verify target instance**:
   - Inspect target `.system-design/manifest.json` and `.system-design/CURSOR.md`.
3. **Report context update**:
   - Confirm active project switch to the learner.
   - Output current active topic, track, and progress percentage for the newly selected instance.
