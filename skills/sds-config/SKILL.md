---
name: sds-config
description: View or dynamically update studio settings (theme, notes structure) in System Design Studio.
argument-hint: "[key] [value]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.2.0
---

# /sds-config

Inspect or dynamically update `.system-design/settings.json` (visual theme, notes structure). Settings can also be updated directly in the visual dashboard on `http://localhost:8420`.

> **Note**: Lessons are strictly delivered as interactive HTML artifacts featuring embedded simulators and collision-aware tooltips. Active-learning notes are compiled into Markdown upon topic verification.

## Instructions

1. **If arguments are provided** (e.g. `artifactStyle midnight-neon` or `notesStructure per-cluster`):
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/merge-settings.py \
     --settings .system-design/settings.json \
     --key "$1" --value "$2"
   ```
2. **If no arguments are provided**:
   - Read `.system-design/settings.json` and display current configuration:
     - `artifactStyle`: visual CSS theme
     - `notesStructure`: `per-topic`, `per-cluster`, `per-tier`, or `single-file`
     - `notesDir`: target directory for active-learning notes
