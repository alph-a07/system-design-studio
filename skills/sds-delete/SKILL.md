---
name: sds-delete
description: Safely delete a System Design Studio project learning instance and remove it from the central registry.
argument-hint: "<project-name-or-id> [--delete-notes] [--force]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.1.1
---

# /sds-delete

Safely remove a System Design Studio project learning instance from the registry and delete its `.system-design` state directory.

## Instructions

1. **Delete project**:
   - If user explicitly confirms deletion or passes `--force` / `-f`:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/manage-projects.py delete "$ARGUMENTS"
     ```
   - If `--delete-notes` is requested, pass `--delete-notes` to clean up the notes directory as well.
   - For previewing what would be deleted without making changes:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/manage-projects.py delete --dry-run "$ARGUMENTS"
     ```
2. **Safety Invariants**:
   - Deleting a project removes its `.system-design/` instance directory (manifest, cursor, lessons, settings) and its registry entry in `projects.json`.
   - In custom workspaces and home directories, source code and non-studio files are strictly preserved.
   - Project study notes are preserved by default unless `--delete-notes` is explicitly passed.
3. **Report Outcome**:
   - Confirm project deletion to the user.
   - Report whether another project became active or if no active projects remain.
