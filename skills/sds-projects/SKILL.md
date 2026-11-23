---
name: sds-projects
description: List all registered System Design Studio project instances and tracks across this machine.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.1.0
---

# /sds-projects

Display an overview table of all registered learning instances, their paths, curriculum tracks, and completion percentages.

## Instructions

1. **Query central registry**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/manage-projects.py list
   ```
   *(Or manage and switch projects visually on `http://localhost:8420` via `sds dashboard`)*
2. **Present overview table**:
   - Project ID and Display Name
   - Workspace directory path
   - Active curriculum track
   - Completed topics / Total topics
   - Clearly mark the currently active instance (`*`).
