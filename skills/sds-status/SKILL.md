---
name: sds-status
description: Check current progress, active topic, cognitive focus, and learning statistics in System Design Studio.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.1.0
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
   - **Artifact Status**: Check if a lesson artifact (`.system-design/lessons/<slug>.html`) exists for the active topic. If delivered and pending discussion, explicitly report: `Delivered — pending review & self evaluation` and provide a clickable link to the lesson.
   - **Next pedagogical action**:
     - If an artifact is delivered and awaiting self evaluation: Prompt the user to explore the lesson and interactive simulator, and conclude on their terms when they have closure. **DO NOT** prompt for `/sds-teach` when an artifact is already delivered.
     - Only if no artifact exists: Prompt the user to run `/sds-teach` to deliver the foundational lesson.
