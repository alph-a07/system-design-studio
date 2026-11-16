---
name: sds-teach
description: Deliver the next or specified interactive system design lesson artifact in System Design Studio.
argument-hint: "[topic]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-teach — Interactive System Design Lesson Engine

Deliver an immersive, first-principles system design lesson artifact featuring tactile simulators (HTML) or visual diagrams (Markdown) based on instance settings.

## Mandatory Architectural Invariants

1. **STRICT PROHIBITION OF GENERIC BOILERPLATE**:
   - You MUST NOT deliver abstract or mad-libs template text (such as *"The system maintains dual kernel/storage states"*).
   - Every lesson MUST be deeply grounded in the physical reality of the topic: exact protocol headers, byte sizes, physical network propagation limits, kernel queue boundaries, OS socket syscalls, and hardware invariants.

2. **TACTILE INTERACTIVE SIMULATOR CONTRACT (HTML MODE)**:
   - In HTML mode, the simulator MUST NOT be a passive 3-click mock.
   - It MUST provide real-time interactive manipulation of the topic's core failure mode (e.g., toggling packet drops to demonstrate Head-of-Line blocking in the kernel receive queue, comparing TCP stalls vs UDP pass-through, and visualizing P99 tail latency).

3. **HYPOTHESIS-FIRST ACTIVE LEARNING GATE**:
   - In your initial chat response, you MUST prompt the learner for their working mental model before handing over the solution:
     *"Before we inspect the internal mechanics of [Topic], what is your initial intuition on [Concrete Dilemma]?"*
   - Capture their response in chat; this becomes Section 1 of their permanent active-learning study note upon sign-off.

4. **SINGLE-SOURCE REPOSITORY ENGINE**:
   - Dispatch scripts located at `~/.system-design-studio/skills/system-design-studio/scripts/` (or repository-local scripts if working inside the studio repo).

## Execution Sequence

1. **Resolve Topic & Settings**:
   - Target Topic: If `$ARGUMENTS` is provided (e.g. `0.1` or `topic.0.1.tcp-vs-udp`), resolve that topic from `CURRICULUM.md`. Otherwise, read `activeFocus.topicId` from `.system-design/CURSOR.md`.
   - Settings: Inspect `.system-design/settings.json` for `outputType` (`html` or `markdown`), `artifactStyle`, and `paths.lessonsDir`.

2. **Render Lesson Artifact**:
   - Compile via the studio lesson rendering engine:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/render-lesson.py \
       --topic-id <topic-id> \
       --format <html|markdown> \
       --style <theme>
     ```
   - Target path: `<project-root>/.system-design/lessons/<slug>.<ext>`
   - In **Antigravity**: Stage the artifact to `<appDataDir>/brain/<conversation-id>/<slug>.html` (or `.md`) and surface it in the chat for side-pane inspection.

3. **Mandatory Pre-Flight Quality Audit**:
   - Inspect the compiled artifact before signaling completion. Verify that:
     1. Zero unreplaced template tokens exist (no leaked `[concept]`, `{{...}}`, or theme labels).
     2. The simulator or diagram directly models the specific failure mode of the topic.
     3. Backward Anchor and Forward Hook accurately reflect the curriculum sequence.

4. **Present Interactive Artifact & Prompt Dialogue**:
   - Provide a direct markdown link: `[Open Interactive Lesson: <Topic>](file:///<path-to-lesson>)`.
   - Highlight the central architectural dilemma and invite the learner's initial hypothesis.
