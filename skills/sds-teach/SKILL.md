---
name: sds-teach
description: Deliver the next or specified interactive system design lesson artifact in System Design Studio.
argument-hint: "[topic]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-teach

Deliver an interactive system design lesson artifact with live simulators (HTML) or diagrams (Markdown) based on instance settings.

## Instructions

1. **Resolve target topic**:
   - If `$ARGUMENTS` is provided (e.g., `0.1` or `topic.0.1.tcp-vs-udp`), resolve that topic from `CURRICULUM.md`.
   - Otherwise, read the active topic from `.system-design/CURSOR.md` under `activeFocus.topicId`.
2. **Inspect instance settings**:
   - Read `.system-design/settings.json` to determine `outputType` (`html` or `markdown`) and `artifactStyle`.
3. **Active learning prompt (Hypothesis First)**:
   - Before exposing internal mechanics, prompt the learner for their intuition:
     *"Before we dive into the internal mechanics of [topic], what is your initial intuition on how [problem] should be handled?"*
4. **Render lesson artifact**:
   - If HTML mode: compile to `.system-design/lessons/<topic-slug>.html` with interactive simulator.
   - If Markdown mode: compile to `.system-design/lessons/<topic-slug>.md` with Mermaid diagrams & ASCII charts.
   ```bash
   python3 ~/.system-design-studio/skills/system-design-studio/scripts/render-lesson.py \
     --topic <topic-id> \
     --format <html|markdown> \
     --style <theme>
   ```
5. **In Antigravity**: Stage HTML artifacts to `<appDataDir>/brain/<conversation-id>/<topic>.html` for side-pane inspection.
