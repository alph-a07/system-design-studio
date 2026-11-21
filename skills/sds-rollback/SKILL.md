---
name: sds-rollback
description: Safely roll back or restore learning state, topic completions, or curriculum mutations to a previous atomic checkpoint or Git commit.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.5.0
---

# /sds-rollback

Safely undo an accidental topic completion, restore curriculum structure, or revert to an earlier learning checkpoint with 100% atomic safety.

## Value to User
- **Zero-Risk Experimentation**: You can test defense scenarios or reorder curriculum tracks without fear of corrupting your progress.
- **Atomic Git Tracking**: Every checkpoint rollback generates a clean, traceable Git commit (`sds(rollback): ...`).
- **Dry-Run Preview**: Preview exact file differences before applying the rollback.

## Instructions

1. **List available checkpoints**:
   ```bash
   sds checkpoints
   ```
2. **Roll back 1 step (default)**:
   ```bash
   sds rollback
   ```
3. **Roll back to specific checkpoint ID**:
   ```bash
   sds rollback --id <checkpoint-id>
   ```
4. **Preview without touching disk**:
   ```bash
   sds rollback --dry-run
   ```
5. Confirm restored topic status and cursor position to the user.
