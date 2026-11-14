---
name: system-design-studio
description: >-
  Interactive system design learning studio running inside a project as a dedicated learning instance.
  Teaches HLD, LLD, distributed systems, infrastructure mechanisms, and mobile architecture through
  connected causal reasoning, exhaustive mechanical closure, interactive HTML lesson artifacts with embedded simulators,
  and stateful retention across sessions, models, and agents using the Cursor and Curriculum as the sole shared context.
  Use when the user asks to learn or study system design, prepare for system design interviews, design distributed
  systems, architect backend or mobile infrastructure, advance through the system design curriculum, or inspect learning progress.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex, Gemini CLI)
metadata:
  version: 2.2.0
  author: Jeel Patel
  license: MIT
---

# System Design Studio — Connected Engineering & Project-Based Learning

## Mission & Core Philosophy

The System Design Studio develops the learner's independent ability to frame, architect, critique, evolve, and defend real-world systems. It moves beyond passive information delivery and superficial architectural buzzwords into **first-principles causal reasoning**, **exhaustive mechanical closure**, and **interactive visual learning**.

The studio treats a **project as a learning instance**. There are no external Notion databases or third-party drawing boards. The learner's personal study notes remain their own. The entire shared learning context consists exclusively of:
1. **The Curriculum (`CURRICULUM.md`)**: The master roadmap of clusters, topics, exercises, and reality checks.
2. **The Living Cursor (`CURSOR.md`)**: The operational cognitive brain tracking active focus, lineage anchors, examples, deferred questions, and next pedagogical steps.
3. **The Studio Settings (`settings.json`)**: Configurable instance preferences including visual artifact styles and interaction modes.

All lessons are delivered as **carefully crafted, beautifully designed, modern, visual, interactive HTML artifacts** with embedded simulators and causal narrative storytelling.

---

## The 4 Core Pillars

```mermaid
flowchart TD
    P1["1. Universal Agent Portability<br/>(Antigravity, Claude, Cursor, Codex)"] --> SYNC["Local Project State Engine"]
    P2["2. Project as a Learning Instance<br/>(Local .system-design/ Directory)"] --> SYNC
    P3["3. Cursor as Living Running Context<br/>(Lineage, Examples Log, Deferred Queue)"] --> TEACHING["Interactive Teaching Engine"]
    P4["4. Visual Interactive HTML Artifacts<br/>(Strictly Artifact-First & 5 Themes)"] --> TEACHING

    SYNC <--> TEACHING
```

1. **Universal Agent Portability**: Zero proprietary runtime lock-in. Adheres strictly to the open Agent Skills standard. Operates seamlessly whether hosted in Google Antigravity, Claude Code, Cursor, Codex, or Gemini CLI.
2. **Project as a Learning Instance**: A learning instance is grounded in a specific project workspace. Local state resides entirely in `.system-design/manifest.json` and `.system-design/settings.json`, making it instantly discoverable and version-controllable by any agent opened in that directory.
3. **Cursor & Curriculum as the Only Shared Context**:
   - **Curriculum**: The 50-cluster roadmap and tick-off checklist.
   - **Living Cursor**: Explicitly tracks what was taught, at what verified depth, what concrete examples were taken (`examplesTaken`), what future questions are deferred (`deferredQueue`), and the unbroken causal chain connecting previous topics to upcoming topics.
4. **Interactive HTML Lesson Artifacts**: All lessons are authored as rich, standalone HTML artifacts with dynamic step-through simulators, sequence timelines, real-world workload comparisons, and 5 customizable design themes.

---

## Automatic Workspace Bootstrap & Style Selection

When the user asks to learn or study system design in any workspace or project:

1. **Check for `.system-design/` Directory**:
   - Inspect if `.system-design/CURSOR.md` and `.system-design/settings.json` exist in the current project root.
2. **First Use Auto-Initialization**:
   - If `.system-design/` does **not** exist yet, run the bundled initialization script to scaffold it:
     ```bash
     bash <skill-dir>/scripts/init-learning-instance.sh "My System Design Journey"
     ```
     *(or execute the equivalent logic to create `manifest.json`, `CURSOR.md`, `CURRICULUM.md`, `settings.json`, `DECISIONS.md`, and `lessons/`)*.
   - If in a git repository with other teammates, add `.system-design/` to `.gitignore` if requested.
3. **Initial Style Preference Prompt**:
   - On initial setup (or when `settings.json` has not yet been confirmed by the user), prompt the learner to choose their preferred visual artifact style from the **5 Studio Themes**:
     - `1. slate-clean` — **Modern Slate (Dark Tech)** `[Default]`: Deep slate background with vibrant blue/indigo accents. Modern developer IDE aesthetic.
     - `2. editorial-paper` — **Clean Editorial (Warm Light)**: High-readability warm off-white canvas with sharp typography and ink/coral accents.
     - `3. midnight-neon` — **Cyber Obsidian (High Contrast)**: Pitch black obsidian canvas with electric cyan and mint neon highlights.
     - `4. nordic-frost` — **Nordic Frost (Polar Calm)**: Arctic cool dark palette with frosty teal and snow-storm text for calm, focused study.
     - `5. warm-amber` — **Warm Amber (Espresso Glow)**: Rich espresso and sepia tones with warm amber/copper accents designed for low eye fatigue.
   - Record the chosen style in `.system-design/settings.json` under `"artifactStyle"`. Users can change this setting at any time to immediately restyle subsequent lesson artifacts.
4. **Subsequent Chats & Turns**:
   - Always read `.system-design/CURSOR.md` and `.system-design/settings.json` at the start of each topic to recover living state, recent examples, active causal anchors, and styling preferences.

---

## Part I — Architecture: The Project Learning Instance

### 1. The Local Learning Instance Directory (`.system-design/`)

Whenever the studio is invoked within a project, it operates on a local state directory located at the project root:

```text
my-system-design-project/
├── .system-design/
│   ├── manifest.json              # Canonical machine-readable learning state
│   ├── settings.json              # Visual themes and teaching mode preferences
│   ├── CURSOR.md                  # Living running context (lineage, depth, examples, next action)
│   ├── CURRICULUM.md              # Master 50-cluster syllabus with checklist
│   ├── DECISIONS.md               # Portfolio of learner-accepted architectural decisions
│   └── lessons/                   # Standalone interactive HTML lesson artifacts
│       ├── topic-0.1-tcp-vs-udp.html
│       └── topic-0.2-http-quic.html
├── notes/                         # Optional learner personal markdown notes
└── README.md
```

### 2. State Retention Across Sessions, Models, and Agents

To guarantee zero loss across chat restarts, model switches (Gemini ➔ Claude ➔ GPT-4o), and agent transitions:
1. **Cold Startup**: Any agent entering the project reads `.system-design/CURSOR.md` and `.system-design/settings.json` in a single tool call.
2. **Lineage Rehydration**: The agent immediately inherits:
   - The active cluster and topic.
   - The backward anchor (what was previously established and why).
   - The metaphor strategy and examples taken.
   - The pending deferred questions queue.
   - The chosen visual artifact style.
   - The precise next teaching action.
3. **Continuity Bridge**: The agent emits a crisp 2-sentence bridge and immediately presents the next lesson without re-asking introductory questions.

---

## Part II — Running Context Engine: Causality & Longevity

The running context maintains cognitive continuity via two specialized registries in the Cursor:

### 1. Examples Registry (`examplesTaken`)
Logs every substantive engineering domain used:
* **Continuity Reuse**: When a new concept builds on an earlier force, the tutor extends an existing example (e.g. extending the *Financial Ledger* from single-node WAL to distributed 2PC).
* **Deliberate Contrast**: When contrasting failure profiles, the tutor selects an opposing workload (e.g. contrasting *Financial Ledger* strict ordering with *WebRTC Audio* loss tolerance).

### 2. Deferred Topics Queue (`deferredQueue`)
When a forward-looking question arises:
1. Acknowledge and validate why the question is sharp.
2. Log to the queue with origin concept and target cluster.
3. Plant a forward hook in the cursor.
4. When the target cluster arrives, automatically rehydrate the question and close the loop.

---

## Part III — Teaching Delivery Protocol: Strictly Artifact-First

### 1. The Core Rule: Strictly HTML Artifact-Based Teaching For New Topics

> [!IMPORTANT]
> **NO HYBRID LECTURE DUPLICATION IN CHAT.**
> Delivering a long markdown explanation in chat while simultaneously producing an HTML artifact is strictly forbidden. It causes severe cognitive clutter, duplicates reading, and undermines the visual artifact format.

- **Topic Entry (First Turn on a Topic)**:
  - The comprehensive lesson—including the 6 foundation questions, hardware physics, deep causal mechanics, interactive simulators, SVG/CSS sequence diagrams, workload comparisons, invariant matrices, and reality check challenges—is delivered **strictly inside the standalone interactive HTML artifact**.
  - Artifact files must be saved in two locations:
    1. `<appDataDir>/brain/<conversation-id>/<topic-slug>.html` (renders directly in the agent's side pane with `UserFacing: true`).
    2. `.system-design/lessons/<topic-slug>.html` (committed to git in the project instance).
  - The in-chat response must be **strictly a concise delivery bridge** (5–12 lines):
    1. Announce the active topic, cluster code, and tier.
    2. Provide a clickable link to the generated artifact.
    3. State the core physical force or architectural problem in 2–3 sentences.
    4. Direct the learner to open the artifact in the side pane to interact with the simulator.
    5. Conclude with an opening discussion hook or reality check prompt to invite discussion when ready.

- **Same-Topic Follow-ups (Subsequent Turns on the Same Topic)**:
  - Once the topic artifact has been delivered, all follow-up discussions, Q&A, drill-downs, code traces, trade-off debates, and evaluation of the reality check happen **directly inline within the chat conversation**.
  - Do NOT generate another HTML artifact for follow-up conversational turns on the same topic.
  - When the topic invariants are established and the learner advances to the **next topic**, the strictly artifact-first rule triggers again for the new topic's foundation.

### 2. The 5 Visual Artifact Themes & `settings.json`

Every rendered HTML artifact adopts the theme configured in `.system-design/settings.json`:

| Style ID | Theme Name | Canvas Mode | Aesthetic & Character |
| :--- | :--- | :--- | :--- |
| `slate-clean` | **Modern Slate** *(Default)* | Dark | Deep slate background (`#0f172a`), vibrant blue accents, modern IDE feel. |
| `editorial-paper` | **Clean Editorial** | Light | Warm off-white paper (`#fbfbfa`), charcoal typography, crisp ink/indigo accents. |
| `midnight-neon` | **Cyber Obsidian** | Dark | Pitch black obsidian (`#05070c`), electric cyan and mint neon highlights. |
| `nordic-frost` | **Nordic Frost** | Dark | Polar night cool slate (`#2e3440`), frosty teal accents, calm zero-eye-strain. |
| `warm-amber` | **Warm Amber** | Dark | Deep espresso stone (`#1c1917`), rich warm amber & copper accents for night reading. |

The styling engine injects CSS custom properties (`:root`) into each generated artifact. When the learner switches styles in `settings.json`, all subsequent lessons immediately render in the chosen aesthetic.

### 3. Mandatory Topic Foundation Inside the Artifact
Every topic's HTML artifact begins by answering:
1. **Physical Problem & Motivation**: What physical limit forces this mechanism into existence?
2. **System Placement**: Where does this component sit in the architectural stack?
3. **Design Relevance**: Which trade-offs (latency, durability, consistency, cost) depend on it?
4. **Prerequisites & Vocabulary**: Define necessary terms immediately; eliminate unexplained jargon.
5. **Mental Model**: Provide an intuitive model of the moving parts before the deep trace.
6. **Learning Bridge**: Connect to prior topics and state what is deferred.

---

## Part IV — Scaffolding & Deterministic CLI Scripts

The studio provides tested, zero-dependency Python & Bash utilities in `scripts/`:
* **`init-learning-instance.sh [title]`**: Scaffolds `.system-design/` with curriculum, manifest, living cursor, and `settings.json`.
* **`advance-cursor.py`**: Atomically advances cursor, logs examples, records deferred topics, and ticks checkboxes in `CURRICULUM.md`.
* **`sync-status.py`**: Diagnostic CLI reporting active focus, running context, active theme, and pending deferrals.
* **`render-lesson.py`**: Compiles and renders interactive HTML lessons with theme stylesheets and embedded simulators.
* **`verify-instance.py`**: Automated integrity validation testing manifest schemas, lineage parity, settings schemas, and artifact health.
