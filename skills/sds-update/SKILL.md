---
name: sds-update
description: Check on-demand for System Design Studio updates without background telemetry.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.2.0
---

# /sds-update

Check for new releases on GitHub without background telemetry and guide non-destructive update.

## Instructions

1. **Run update check**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/check-updates.py --force
   ```
2. **If an update is available**:
   - Present release summary and prompt user to run:
     ```bash
     curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash
     ```
   - Remind the user that updates strictly preserve all existing projects, cursors, and notes.
3. **If up to date**:
   - Confirm that the local installation is on the latest release.
