---
name: system-design-studio
description: >-
  Interactive system design learning studio running inside a project as a dedicated learning instance.
  Teaches HLD, LLD, distributed systems, infrastructure mechanisms, and mobile architecture through
  connected causal reasoning, exhaustive mechanical closure, interactive HTML or Markdown lesson artifacts,
  and stateful retention across sessions, models, and agents using the Cursor and Curriculum as the sole shared context.
  Use when the user asks to learn or study system design, prepare for system design interviews, design distributed
  systems, architect backend or mobile infrastructure, advance through the system design curriculum, or inspect learning progress.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex, Gemini CLI)
metadata:
  version: 3.2.0
  author: Jeel Patel
  license: MIT
---

# System Design Studio — Connected Engineering & Project-Based Learning

## Mission & Core Philosophy

The System Design Studio develops the learner's independent ability to frame, architect, critique, evolve, and defend real-world systems. It moves beyond passive information delivery and superficial architectural buzzwords into **first-principles causal reasoning**, **exhaustive mechanical closure**, and **interactive visual learning**.

The studio treats a **project as a learning instance**. There are no external Notion databases or third-party drawing boards. The entire shared learning context consists exclusively of:
1. **The Curriculum (`CURRICULUM.md`)**: The master roadmap of clusters, topics, exercises, and reality checks adhering strictly to the `Tier > Cluster > Topic` hierarchy.
2. **The Living Cursor (`CURSOR.md`)**: The operational cognitive brain tracking active focus, lineage anchors, examples, deferred questions, and next pedagogical steps.
3. **The Studio Settings (`settings.json`)**: Configurable instance preferences including visual artifact styles, output format (`html` vs `markdown`), and discussion-synthesized study notes.

---

## The User-Script Boundary: "Two Scripts, Then Pure Chat"

System Design Studio enforces a strict boundary between host setup and learning delivery:

1. **Terminal Phase (Exactly 2 Scripts)**:
   - **`install.sh`**: One-time global machine setup configuring global preferences (`~/.system-design-studio/config.json`) and linking skills to coding agents.
   - **`init-learning-instance.sh`**: Scaffolds a project learning instance (in default `~/.system-design-studio/projects/<name>` or custom workspace, with chosen curriculum track and project-scoped notes).
   - *(Optional: `update.sh` is run only when updates are announced and desired)*.
2. **Chat Phase (100% Skill Command Driven)**:
   - **Zero Terminal Interventions**: Once a project is initialized, the learner **never needs to drop to a terminal or run python scripts manually**.
   - All interactions—teaching, debating, sign-off verification, note browsing, curriculum tuning, and project switching—are executed natively through custom `/sds-*` skill commands or natural language conversation.
   - The AI agent automatically dispatches the bundled engine scripts under the hood via standard tool execution (`run_command`, `Bash`, or terminal tools) transparently.

---

## Complete Skill Commands Suite (In-Chat)

Every command works natively across all agents (Antigravity, Claude Code, Cursor, Codex):

| Skill Command | Natural Language Trigger | Agent Action & Internal Script Dispatched |
| :--- | :--- | :--- |
| **`/sds-teach [topic]`** | "Teach topic 0.1", "Next topic" | Reads cursor/settings. If `outputType == "markdown"`, runs `render-lesson.py --format markdown`; if `outputType == "html"`, runs `render-lesson.py --format html`. Prompts the learner for their initial intuition or working hypothesis before diving into internal mechanics. |
| **`/sds-discuss`** | "Here is my defense of the scenario...", "How should I think about..." | Active Learning Dialectic: Stress-tests the learner's hypothesis. For senior engineers, probes cold failure modes and latency math. For junior/hesitant engineers, provides Socratic scaffolding questions. Traces where the model breaks. |
| **`/sds-complete [ev]`** | "Mark complete", "Sign off topic" | Runs `advance-cursor.py --complete-topic <id> --evidence <ev> --hypothesis <hypo> --discussion-summary <summary>`. Ticks `CURRICULUM.md`, logs ADR in `DECISIONS.md`, and compiles active-learning study note. |
| **`/sds-projects`** | "Show all projects", "List projects" | Runs `manage-projects.py list`. Displays an overview table of all registered machine projects, locations, tracks, and progress. |
| **`/sds-open <name>`** | "Switch to project X" | Runs `manage-projects.py switch <id>`. Switches active project context. |
| **`/sds-notes [topic]`** | "Show my notes", "Where are my notes?" | Runs `manage-projects.py notes`. Lists all generated study notes for the active project with direct clickable links (`file:///...`). |
| **`/sds-curriculum`** | "Customize syllabus", "Reorder topics" | Runs `configure-curriculum.py` or guides curriculum restructuring from chat. |
| **`/sds-config [k] [v]`**| "Switch theme to obsidian", "Change output to markdown" | Runs `merge-settings.py` or updates `.system-design/settings.json` dynamically for subsequent lessons. |
| **`/sds-update`** | "Check for updates", "Are there updates?" | Runs `check-updates.py --force`. If an update is available, displays alert and prompts user to run `update.sh` in their terminal. |
| **`/sds-status`** | "Show progress", "Where are we?" | Runs `sync-status.py`. Displays active topic, track, progress percentage, and cognitive state. |

---

## Dual Output Format Engine: HTML vs. Markdown

The learner chooses how lesson artifacts are authored via `settings.json` (`outputType: "html" | "markdown"`):

### 1. HTML Output Mode (`outputType: "html"`)
- Renders to `.system-design/lessons/<topic-slug>.html`.
- Standalone HTML artifact styled with one of the 5 CSS themes (`slate-clean`, `editorial-paper`, `midnight-neon`, `nordic-frost`, `warm-amber`).
- Features inline interactive JavaScript simulators, state machines, and real-time failure injection.
- Staged to `<appDataDir>/brain/<conversation-id>/<topic>.html` in Antigravity for side-pane viewing.

### 2. Markdown Output Mode (`outputType: "markdown"`)
- Renders to `.system-design/lessons/<topic-slug>.md`.
- Pure GitHub-Flavored Markdown: zero JavaScript, no browser engine dependencies.
- Ideal for terminal-centric workflows, Neovim, Obsidian, and e-ink/markdown readers.
- Replaces JavaScript simulators with:
  1. **Mermaid sequence & state diagrams** detailing protocol and state transitions.
  2. **ASCII hardware state charts** tracing buffer queues and packet serialization step-by-step.
  3. **Structured comparison tables & formulas** directly in markdown syntax.
- Preserves the unanswered contextual sign-off challenge at the end for chat defense.

---

## Active Learning Cognitive Abstraction & Project-Scoped Notes

Notes are **strictly project-specific** and governed by **what the learner understood through active learning**, NOT what was taught (no boilerplate textbook summaries). They reside in the project's configured `notesDir` (default: `<project-root>/notes/` or custom external paths like Obsidian vaults).

When a topic is completed (`/sds-complete`), the note generation engine abstracts the learner's understanding starting from their initial hypothesis through the friction of the Socratic dialectic before conclusion:
1. **Initial Intuition & Working Hypothesis**: The naive model, pattern, or assumption the learner brought to the topic before constraint analysis.
2. **Dialectic & Friction Encountered**: The Socratic stress-test, failure modes (e.g., asymmetric partitions, head-of-line blocking), and edge cases where the initial hypothesis broke down in chat.
3. **Derived Invariant (The 'Aha!' Synthesis)**: The non-negotiable physical or mathematical law proved cold by the learner unassisted (the verified sign-off claim).
4. **Personal Rule of Thumb & Sizing Reality**: Actionable engineering decision rules and concrete hardware/network bounds (Little's Law, Bandwidth-Delay Product, quorum intersection math) the learner can deploy under pressure.

The compilation mode is controlled by `"notesStructure"` in `settings.json`:
- **`per-topic`** *(Default)*: Atomic markdown file per topic (`notes/<tier>/<cluster>/<topic>.md`).
- **`per-cluster`**: Consolidated markdown file per cluster (`notes/<tier>/<cluster>.md`) with topic sections.
- **`per-tier`**: Consolidated markdown file per tier (`notes/tier-<N>-<tier-name>.md`).
- **`single-file`**: Monolithic master study guide (`notes/SYSTEM-DESIGN-NOTES.md`) with auto-generated Table of Contents.

---

## Strict Curriculum Taxonomy Enforcement (`Tier > Cluster > Topic`)

To guarantee deterministic cognitive lineage, living cursor tracking, and automated note compilation, **all curricula must strictly conform to the 3-level taxonomy**:

```text
# Tier <N>: <Tier Title>                                  (Level 1)
## <Order>. [<Code>] <Cluster Title>                      (Level 2)
- [ ] <Topic Title> — <Specification> — *Tick off when:*  (Level 3)
```

1. **Curated Goal Tracks**:
   - **`interview-sprint`**: Short-Term Interview Sprint (2–4 weeks / ~35 high-yield topics across Tiers 0, 1, 2).
   - **`distributed-systems`**: Distributed Systems & Storage Deep-Dive (6–12 weeks / ~85 topics across Tiers 0, 2).
   - **`staff-architect`**: Staff+ / Principal Architecture & System Defense (~60 topics across Tiers 0, 2, 4).
   - **`mobile-offline`**: Mobile & Offline-First Systems (3–6 weeks / ~45 topics across Tiers 0, 3).
   - **`full-mastery`**: The complete 50-cluster, 354-topic syllabus across all 5 engineering tiers.
2. **Bring Your Own (BYO) Markdown Syllabus**:
   - Imported via `import-curriculum.py --input <file.md>`.
   - Validates that every topic belongs to a cluster, every cluster belongs to a tier, and every topic contains a sign-off gate (`— *Tick off when:*`).
   - If syntax errors occur, reports line-numbered diagnostics with `--auto-fix` normalization support.

---

## On-Demand Update Policy

- **Zero Automatic Background Checks**: To maximize performance and privacy, updates are never checked silently during daily learning sessions.
- **On-Demand Check via `/sds-update`**:
  - The agent runs `python3 <skill-dir>/scripts/check-updates.py --force`.
  - If a new version is available, the agent presents a clean notification asking the user to run the update command:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash
    ```
  - The update updates installed skill files and merges settings keys via `merge-settings.py` without touching project progress, living cursors, or user study notes.

---

## Zero-Risk Skill Uninstallation

If the user wishes to remove the skill from their AI agents:
```bash
curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/uninstall.sh | bash
```
- **Invariant**: The uninstaller eliminates the skill **only** from all coding agents (Antigravity, Claude Code, Cursor, Codex).
- **Preservation Guarantee**: All personal project repositories, `.system-design/` progress state, living cursors, synthesized study notes, and `DECISIONS.md` records are **100% preserved**.

---

## Multi-Project Management & Registry

All projects on the machine are indexed in `~/.system-design-studio/projects.json`:
- **Default Projects**: Reside in `~/.system-design-studio/projects/<name>/`.
- **Custom Projects**: Reside anywhere on disk (e.g., existing git repositories).
- **Navigation in Chat**:
  - `/sds-projects`: Displays all projects, locations, active tracks, and progress.
  - `/sds-open <id>`: Switches active context to that project.
  - `/sds-notes`: Immediately displays clickable links to notes generated in the active project.
