# Interactive HTML Lesson Artifacts & Visual Pedagogy

## Overview

In the System Design Studio, external drawing boards (such as tldraw or Excalidraw) and external documentation systems (such as Notion) are **not used**. 

Instead, **interactive, beautifully crafted HTML artifacts** serve as the exclusive visual and pedagogical delivery medium for new topics:
- **Strictly Artifact-First on Topic Entry**: The entire lesson, foundation, and simulator live in the artifact. The in-chat response is merely a concise 5–10 line delivery bridge.
- **Inline Follow-up Discussions**: Subsequent exploration, Q&A, and reality check evaluations happen directly in the chat.
- **5 Selectable Visual Styles**: Customizable through `.system-design/settings.json`.

Every substantive topic is delivered as a self-contained, modern HTML artifact featuring:
- Causal, narrative storytelling (no flat bullet points).
- Interactive step-through simulators (e.g. simulating packet loss, head-of-line blocking, quorum voting, cache stampedes).
- Tailored SVG / CSS diagrams and sequence timelines.
- Real-world workload contrast cards.
- Invariant matrices (guarantees vs non-guarantees).
- Integrated engineering challenges and interactive accordions.

---

## 1. Storage & Placement

Every topic artifact is saved in two locations:
1. **Conversation Artifact Directory**: `<appDataDir>/brain/<conversation-id>/<topic-slug>.html` (renders in the host environment's side pane with `UserFacing: true`).
2. **Project Learning Instance**: Saved to the path configured in `.system-design/settings.json` under `paths.lessonsDir` (defaults to `.system-design/lessons/<topic-slug>.html`, committed to git as part of the learner's personal repository).

---

## 2. The 5 Visual Theme Variants

Artifact styling is driven by `.system-design/settings.json`. The renderer injects corresponding `:root` CSS variables and classes:

### 1. `slate-clean` (Modern Slate / Dark Tech) — *Default*
- **Aesthetic**: Modern developer IDE & cloud console.
- **Variables**:
  - `--background`: `#0f172a` (Deep Slate 900)
  - `--card`: `#1e293b` (Slate 800)
  - `--card-border` / `--border`: `#334155` (Slate 700)
  - `--foreground`: `#f8fafc` (Slate 50)
  - `--muted-foreground`: `#94a3b8` (Slate 400)
  - `--primary`: `#3b82f6` (Vibrant Blue 500)

### 2. `editorial-paper` (Clean Editorial / Warm Light)
- **Aesthetic**: High-readability warm off-white paper canvas with sharp editorial typography and ink/coral accents.
- **Variables**:
  - `--background`: `#fbfbfa` (Warm Paper)
  - `--card`: `#ffffff` (Pure White Card)
  - `--card-border` / `--border`: `#e4e4e7` (Zinc 200)
  - `--foreground`: `#18181b` (Charcoal / Zinc 900)
  - `--muted-foreground`: `#71717a` (Zinc 500)
  - `--primary`: `#2563eb` (Indigo Ink)

### 3. `midnight-neon` (Cyber Obsidian / High Contrast)
- **Aesthetic**: Pitch black obsidian canvas with electric cyan and mint neon highlights; futuristic HUD feel.
- **Variables**:
  - `--background`: `#05070c` (Obsidian Void)
  - `--card`: `#0d1117` (Deep Obsidian Card)
  - `--card-border` / `--border`: `#21262d` (Subtle Glow Border)
  - `--foreground`: `#f1f5f9` (Crisp Light)
  - `--muted-foreground`: `#8b949e` (Dim Muted)
  - `--primary`: `#06b6d4` (Electric Cyan Neon)

### 4. `nordic-frost` (Nordic Frost / Polar Calm)
- **Aesthetic**: Arctic cool dark palette with frosty teal and snow-storm text for calm, focused study.
- **Variables**:
  - `--background`: `#2e3440` (Polar Night)
  - `--card`: `#3b4252` (Polar Night Card)
  - `--card-border` / `--border`: `#4c566a` / `#434c5e`
  - `--foreground`: `#eceff4` (Snow Storm)
  - `--muted-foreground`: `#d8dee9` (Frost Gray)
  - `--primary`: `#88c0d0` (Frost Teal)

### 5. `warm-amber` (Warm Amber / Espresso Glow)
- **Aesthetic**: Rich espresso and sepia tones with warm amber/copper accents designed for low eye fatigue during nighttime study.
- **Variables**:
  - `--background`: `#1c1917` (Stone / Espresso 900)
  - `--card`: `#292524` (Warm Espresso Card)
  - `--card-border` / `--border`: `#44403c`
  - `--foreground`: `#fafaf9` (Warm Cream)
  - `--muted-foreground`: `#a8a29e`
  - `--primary`: `#f59e0b` (Amber Gold 500)

---

## 3. Configuration via `settings.json`

The active style is controlled by `.system-design/settings.json`:
```json
{
  "$schemaVersion": "2.0",
  "artifactStyle": "slate-clean",
  "availableStyles": [
    { "id": "slate-clean", "name": "Modern Slate (Dark Tech)", "theme": "dark" },
    { "id": "editorial-paper", "name": "Clean Editorial (Warm Light)", "theme": "light" },
    { "id": "midnight-neon", "name": "Cyber Obsidian (High Contrast)", "theme": "dark" },
    { "id": "nordic-frost", "name": "Nordic Frost (Polar Calm)", "theme": "dark" },
    { "id": "warm-amber", "name": "Warm Amber (Espresso Glow)", "theme": "dark" }
  ],
  "deliveryMode": "strictly-artifact-first",
  "inlineDiscussions": true
}
```

The learner can modify this file or request a style change at any point. All subsequent lesson artifacts reflect the updated style immediately.

---

## 4. Progressive Disclosure Narrative Structure (Strictly Non-Coverage-Based)

Every interactive lesson artifact is structured as **one continuous, cohesive discussion with unique information and progressive disclosure**.

> [!IMPORTANT]
> **NO REPETITIVE COVERAGE SILOS**:
> Lessons must **never** be organized into coverage-based silos (e.g. "Brief Overview", "Foundation Cards", "Deep Explanations", followed by a redundant "Summary Table"). Concepts, constraints, and vocabulary are introduced progressively only when the narrative naturally requires them to solve the next obstacle.
>
> **NO ARTIFICIAL SECTION INDEXING**:
> Sections are **NOT** indexed with category names or numbers (e.g., do not title sections "01. Foundation", "02. Deep Explanations", or "The WHYs"). Instead, the agent uses topic-driven narrative headings that tell the ongoing engineering story.
>
> **NO SEGREGATED SIMULATOR SECTION**:
> Interactive components, live state sandboxes, or sequence simulators have **no dedicated or isolated section**. They are embedded inline wherever the mechanism is being explained, giving the learner tactile exploration right when they encounter the moving parts.

### The 5 Pedagogical Narrative Phases:

1. **Phase 1: Background Context & The Forcing Problem (The WHYs & optional WHENs)**:
   - Sets the foundation of the problem when the active topic was absent.
   - Answers: *What broken state, throughput collapse, or physical constraint forced this mechanism into existence?*
   - Ensures **exhaustive closure of WHY** right here.
   - Introduces a central, concrete engineering dilemma that can persist throughout the lesson to anchor subsequent explanations.

2. **Phase 2: The Active Topic & Surrounding Landscape (The WHATs & optional WHEREs)**:
   - Assumes the topic is completely new to the reader unless `CURSOR.md` indicates previous grounding.
   - Covers WHAT the active mechanism actually is, its core boundaries, and WHERE it sits in the architectural stack.
   - Ensures **exhaustive closure of WHAT and WHERE**.
   - *(Note: WHENs and WHEREs can be flexibly and interchangeably balanced across Phase 1 and Phase 2 contextually).*

3. **Phase 3: Internal Mechanics, Invariants & Causality (The HOWs & WHYs of HOWs)**:
   - Exhaustive breakdown of how the mechanism works internally step-by-step (buffer states, queue lifecycles, message/packet contracts).
   - Explains **why it works that way specifically**, and **why alternative designs fail or cause catastrophic unintended consequences**.
   - Delivers a digestible, crystal-clear mechanical grasp.
   - **Inline Interactive Simulator**: The live interactive simulation canvas or visual trace widget is embedded directly here inline, letting the reader step through the state machine and fault injection in real time.

4. **Phase 4: Mental Model Synthesis & Production Grounding**:
   - Bundles all preceding mechanics into a unified, lasting mental model.
   - Builds direct correlation to real-world production workloads and architectural patterns (e.g., contrasting *Strict Durability Ledger* vs *Bounded-Latency Media Stream* with an explicit invariant matrix).

5. **Phase 5: Contextual Sign-Off Verification Gate**:
   - Leaves the reader with one or more contextual engineering scenarios / challenges without pre-baked answers.
   - Tests the unprompted tick-off criteria from `CURRICULUM.md`. The learner defends their analysis and breakdown in chat to achieve sign-off.
