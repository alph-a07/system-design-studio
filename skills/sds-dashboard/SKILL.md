---
name: sds-dashboard
description: Launch or view the interactive curriculum studio workbench, real-time progress tracker, revision mode, and artifact studio on localhost in sync with Git.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.5.0
---

# /sds-dashboard

Launch the interactive, zero-dependency curriculum studio workbench and visual progress tracker on `http://localhost:8420`.

## Value to User
- **Dashboard First, Fewer Commands**: Manage projects, syllabus, progress tracking, study notes, and settings directly via UI.
- **Dual-Direction Read-Write**: Edits in the dashboard update local Git-tracked files; agent actions in chat immediately update the dashboard without manual page refresh.
- **Real-Time Progress Tracking**: Granular topic statuses (`not started`, `in progress`, `completed`) with 1-click sign-off defense & ADR generation.
- **Revision Mode**: High-yield conceptual understanding flashcards auto-compiled from accepted sign-off defenses, failure boundaries, and trade-off formulas.
- **Interactive Simulator Player & Reader Mode**: Test interactive HTML simulators or switch to distraction-free reader mode with built-in text highlighting (zero dedicated server required).
- **In-Dashboard Notes Editor**: Read and edit Markdown study notes with instant disk synchronization.
- **Multi-Project Management**: Switch active projects, initialize new learning instances, or configure syllabus tracks right from the dashboard.
- **Universal Theming & Flawless Contrast**: Seamless Dark and Light mode support with zero contrast failures, matching the Bauhaus Neo-Brutalist design philosophy.

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
