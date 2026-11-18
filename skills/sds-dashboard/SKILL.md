---
name: sds-dashboard
description: Launch or view the read-only curriculum progress tracker, interactive lessons, and styled study notes on localhost in sync with Git.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.3.1
---

# /sds-dashboard

Launch the zero-dependency, read-only curriculum progress tracker and artifact workbench on `http://localhost:8420`.

## Value to User
- **Live Git & Disk Sync**: Real-time progress updates polled every 3 seconds as topics advance in chat.
- **Visual Syllabus**: Complete 50-cluster syllabus with verified checkboxes, current focus indicator, and tier groupings.
- **Interactive Simulator Player**: Test and inspect compiled HTML lessons directly inside your browser.
- **Styled Notes Reader**: Read formatted Markdown study notes matching the Bauhaus Neo-Brutalist brand identity.
- **Architecture Decisions**: Review all accepted ADR trade-off records logged into `DECISIONS.md`.

## Instructions

1. If the user asks to launch, open, or view the dashboard/tracker:
   ```bash
   # Run via sds CLI:
   sds dashboard

   # Or directly via Python:
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/serve-dashboard.py
   ```
2. Present the user with the clickable local URL: `http://localhost:8420`.
3. If the user specifies a custom port or asks for background execution, pass `--port <PORT>`.
