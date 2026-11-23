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
  version: 4.1.0
  author: Jeel Patel
  license: MIT
---

# System Design Studio — Connected Engineering & Project-Based Learning

## Mission & Core Philosophy

The System Design Studio develops the learner's independent ability to frame, architect, critique, evolve, and defend real-world systems. It moves beyond passive information delivery and superficial architectural buzzwords into **first-principles causal reasoning**, **exhaustive mechanical closure**, and **interactive visual learning**.

The studio treats a **project as a learning instance**. There are no external Notion databases or third-party drawing boards. The entire shared learning context consists exclusively of:
1. **The Curriculum (`CURRICULUM.md`)**: The master roadmap of clusters, topics, exercises, and reality checks adhering strictly to the `Tier > Cluster > Topic` hierarchy.
2. **The Living Cursor (`CURSOR.md`)**: The operational cognitive brain tracking active focus, lineage anchors, examples, deferred questions, and next pedagogical steps.
3. **The Studio Settings (`settings.json`)**: Configurable instance preferences including visual artifact styles and discussion-synthesized study notes.
4. **Strict Active Project Context Isolation Invariant**: The active project workspace is the sole source of truth. Agents are strictly forbidden from leaking, reading, or incorporating context, examples, or notes from other projects in `~/.system-design-studio/projects/` or external chat contexts. Fresh projects are strictly treated as clean slates.

---

## Specialized Subagent Topology & Agentic Efficiency

System Design Studio organizes cognitive labor into a high-ROI agentic topology where subagent invocation is supported, combining specialized cognitive agents with deterministic local automation to eliminate token waste:

### 1. The Division of Cognitive & Mechanical Labor
| Task Area | Implementation | Rationale & Token/Latency ROI |
|---|---|---|
| **Content Generation** | **`sds-lesson-crafter` (LLM Subagent)** | High ROI. Authors 2,500+ word (3,500+ in full-depth mode) first-principles systems lessons using `lesson_builder.py` with physical dilemmas, mechanics, inline tooltips, and simulator specifications without polluting coordinator context. |
| **Content Review** | **`sds-pedagogy-auditor` (LLM Subagent)** | High ROI. Adversarial gatekeeper enforcing the 7 Hard Pre-Flight Checks (recomputing derived math, verifying jargon ordering, banning unhedged absolutes, and auditing gate alignment). |
| **Dialectic Challenge** | **`sds-dialectic-challenger` (LLM Subagent)** | High ROI. Socratic Staff+ Architect injecting concrete failure modes (queue drops, network partitions, fsync ceilings) cold in chat during dialectic defense. |
| **Context Analysis** | **Inlined in Coordinator (Local Disk Tool)** | Dropped as subagent. Coordinator reads `CURSOR.md` and `settings.json` in 5ms via `read_file`. Delegating would waste ~3,000 tokens and 5s latency with zero upside. |
| **Content Rendering** | **`render-lesson.py` (Deterministic Script)** | Dropped as subagent. Compiles HTML/Markdown and injects interactive JS simulator engines in <50ms with 0 tokens. Eliminates syntax hallucinations. |
| **Rendering Review** | **`render-lesson.py` (AST/Regex Assertions)** | Dropped as subagent. Automated Python checks verify word counts, jargon density, and interactive tags in 10ms with 0 tokens. |
| **Notes & Revisions** | **`compile-notes.py` & `update-revisions.py`** | Dropped as subagent. Automatically synthesizes study notes and ADR flashcards on sign-off in 15ms with 0 token overhead. |

### 2. Dual-Mode Universal Execution
- **Mode A (Subagent-Orchestrated)**: Supported environments (Google Antigravity, Open Agent runners) invoke dedicated worker subagents (`sds-lesson-crafter`, `sds-pedagogy-auditor`, `sds-dialectic-challenger`) for maximum cognitive focus and isolated context windows.
- **Mode B (Single-Agent Fallback)**: Environments without subagent invocation tools (Claude Code, Cursor IDE, OpenAI Codex) execute the phases sequentially in a single turn without degradation.

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

## Complete Skill Commands Suite (Workflow-Based Guide)

Rather than an arbitrary list of internal scripts, the studio commands map to your natural learning workflow:

### Phase 1: Deep Dive & Visual Discovery
- **`/sds-teach [topic]`**
  - *User Value*: Explains complex systems with friendly editorial storytelling, deep causal mechanics, and mandatory inline jargon unpacking. Generates a standalone interactive HTML simulation so you can visually inspect failure modes instead of skimming dry documentation.
  - *Natural Language*: "Teach topic 0.1", "Next topic", "Show me the mechanics of TCP socket buffers"

### Phase 2: Stress-Testing & Dialectic Defense
- **Chat Defense (Implicit in Chat)**
  - *User Value*: Proves you actually understand production failure modes before you commit. Reply directly in chat to defend against the challenge posed in the delivered lesson. The agent (or `sds-dialectic-challenger`) stress-tests your working assumptions cold in chat with unannounced scenarios, latency limits, and asymmetric network partitions.
  - *Natural Language*: "Here is my defense of the scenario...", "How should I think about quorum loss?", "Stress test my design"

### Phase 3: Automated Proof, Git Checkpointing & Retention
- **`/sds-complete [evidence]`**
  - *User Value*: Validates that you met the unannounced defense criteria, checks off the topic in `CURRICULUM.md`, records an ADR in `DECISIONS.md`, advances your living cursor, and records an atomic Git commit (`sds(learn): complete ...`).
  - *Natural Language*: "Mark complete", "Sign off topic with evidence: derived quorum formula"
- **`/sds-notes [topic]`**
  - *User Value*: Accesses your synthesized active-learning study notes (Hypothesis → Friction → Derived Invariant → Sizing Rules). When `autoGenerateNotes` is true, notes compile automatically on sign-off; when disabled, compile notes on demand.
  - *Natural Language*: "Show my notes", "Where are my study notes?", "Compile notes for topic 0.1"

### Phase 4: Visual Tracking, Safety & Multi-Track Isolation
- **`/sds-dashboard`**
  - *User Value*: Launches a read-only progress tracker and artifact workbench on `http://localhost:8420`. Updates in real time with Git, rendering the 50-cluster syllabus, interactive HTML simulators, styled study notes, and ADRs.
  - *Natural Language*: "Open dashboard", "Show progress on localhost", "Launch visual tracker"
- **`/sds-rollback`**
  - *User Value*: Zero-risk safety net. Safely revert an accidental topic sign-off or restore curriculum structure with atomic Git rollback and local snapshot recovery.
  - *Natural Language*: "Roll back last topic", "Undo sign-off", "Restore earlier checkpoint"
- **`/sds-status`**
  - *User Value*: Instant snapshot of your active focus, backward causal hooks, forward hooks, and deferred question queue.
  - *Natural Language*: "Show progress", "Where are we?", "Current status"
- **`/sds-curriculum`**
  - *User Value*: Reorder clusters, prune topics, or import a custom Markdown syllabus scoped strictly to your project without losing completed progress.
  - *Natural Language*: "Customize syllabus", "Reorder clusters", "Import custom curriculum"
- **`/sds-config [k] [v]`**
  - *User Value*: Switch visual themes, toggle auto-notes, or change notes structuring mode.
  - *Natural Language*: "Switch theme to obsidian", "Disable auto-notes", "Change notes structure to single-file"
- **`/sds-projects` & `/sds-open <name>`**
  - *User Value*: Manage multiple isolated learning workspaces across your workstation (e.g., an interview prep project in one repo and a distributed consensus project in another).
  - *Natural Language*: "List projects", "Switch to project interview-prep"
- **`/sds-delete <name>`**
  - *User Value*: Safely clean up finished instances and keep your multi-project registry tidy without touching workspace source code.
  - *Natural Language*: "Delete project old-study", "Remove learning instance"
- **`/sds-update`**
  - *User Value*: On-demand check for studio updates without background telemetry.
  - *Natural Language*: "Check for updates", "Are there updates?"

---

## Interactive HTML Delivery: Rich Visual Lessons & Tactile Simulators

Every lesson authored in System Design Studio is delivered as an authoritative interactive HTML artifact with bespoke live simulators, tabbed navigation, and non-disruptive inline jargon unpacking:

### Interactive HTML Edition (`<topic-slug>.html`)
- Renders to `.system-design/lessons/<topic-slug>.html`.
- Responsive two-column layout with an independent vertical sidebar featuring section navigation and a slide-over Key Terms Glossary.
- Tactile direct-manipulation simulators and state machine failure injectors.
- Non-disruptive inline jargon cues with interactive floating popovers (definitions on hover/click without breaking reading flow).
- Auto-staged to `<appDataDir>/brain/<conversation-id>/<topic>.html` in Antigravity for side-pane viewing.
- Study notes are synthesized and preserved as clean GitHub Flavored Markdown in `notesDir`.

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
