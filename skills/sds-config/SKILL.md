---
name: sds-config
description: View or dynamically update studio settings (theme, HTML vs Markdown, notes structure) in System Design Studio.
argument-hint: "[key] [value]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.5.1
---

# /sds-config

Inspect or dynamically update `.system-design/settings.json` (visual theme, output mode, notes structure). Settings can also be updated directly in the visual dashboard on `http://localhost:8420`.

## Instructions

1. **If arguments are provided** (e.g. `artifactStyle midnight-neon` or `outputType markdown`):
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/merge-settings.py \
     --settings .system-design/settings.json \
     --key "$1" --value "$2"
   ```
2. **If no arguments are provided**:
   - Read `.system-design/settings.json` and display current configuration:
     - `artifactStyle`: visual CSS theme
     - `outputType`: `html` (interactive simulators) or `markdown` (clean text)
     - `notesStructure`: `per-topic`, `per-cluster`, `per-tier`, or `single-file`
     - `notesDir`: target directory for active-learning notes
