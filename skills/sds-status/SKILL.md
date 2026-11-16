---
name: sds-status
description: Check current progress, active topic, cognitive focus, and learning statistics in System Design Studio.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-status

Check current progress, active topic, cognitive focus, and learning statistics for the active learning instance.

## Instructions

1. **Locate the project's `.system-design` instance directory**:
   - Check current working directory for `.system-design`
   - If not found in current directory, check active project in `~/.system-design-studio/projects.json` or run `manage-projects.py list`.
2. **Run status synchronization**:
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/sync-status.py <instance-dir>
   ```
   *(Or dispatch the local script from `skills/system-design-studio/scripts/sync-status.py` if working within the studio repo)*.
3. **Present the cognitive state report**:
   - Active Topic ID & Title
   - Current Progress Percentage across active curriculum track
   - Lineage anchors and verified physical invariants
   - Next pedagogical action
