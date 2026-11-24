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

---

## 5. Built-in Active Reading Highlighter & Annotation Tool

Starting in **v3.3.0**, all interactive HTML lesson artifacts feature an embedded, non-destructive **Highlighter & Annotation Tool**:

### Architecture & Capabilities:
- **Zero Configuration**: Embedded directly into the artifact shell; runs automatically without manual setup or dependencies.
- **Atomic Block Slicing Engine**: Highlighting never breaks HTML layout, drops text, or displaces formatting tags (`<strong>`, `<em>`, `<code>`). Selections spanning across paragraphs, inline tags, or tables slice cleanly per block.
- **Dual-Layer Zero-Latency Persistence**:
  1. **Primary Layer**: Synchronous `localStorage` cache guarantees 0ms instantaneous restoration on page reloads with zero flicker.
  2. **Secondary Layer**: Background asynchronous sync to `highlight_server.py` writes sidecar annotations to `<artifact>.highlights.json` on disk.
- **Cohesive Group Hover**: Hovering over any segment of a multi-line or cross-tag highlight simultaneously lights up the entire highlighted passage.
- **Click-to-Annotate**: Click any highlight to view, add, edit, or delete notes.
- **Adaptive Theming**: Uses semantic CSS variables with translucent alpha blends and `color: inherit` for optimal WCAG contrast in all 5 visual theme modes.
- **Keyboard Shortcuts**: `1`–`5` (swatch colors), `H` (apply highlight), `N` (open note dialog), `Esc` (dismiss).

---

## 6. The Explainer's Quality Contract (Enforced Quality Invariants)

All generated lesson artifacts are programmatically audited against the following six pedagogical laws before release:

1. **Anti-Compression & Explainer Depth (Ban the Cheat Sheet)**:
   - A lesson must NEVER read like a compressed engineer's cheat sheet, summary table, or bullet-point review.
   - For any topic introducing architectural primitives or protocols with prerequisites, the lesson MUST provide 2,500–3,500 words of progressive, unfolding narrative prose. Concepts must have breathing room: physical dilemma ➔ mental model ➔ internal mechanics & step-by-step trace ➔ failure modes & costs ➔ production reality ➔ self evaluation gate.

2. **Zero-Orphaned Jargon Law**:
   - Every domain acronym, protocol keyword, or systems buzzword introduced MUST be accompanied by an immediate plain-English translation callout (`<div class="jargon-card">`) right where it appears.
   - Plain English FIRST, systems label second: Describe the concept in intuitive everyday terms before stamping it with its formal technical moniker. Ban dense noun-stacking (e.g. replace *"monotonic ordering"* with *"strictly in-order sequence"*; replace *"stateless boundary-preserving datagram"* with *"standalone message with clear boundaries"*).
   - Eliminate melodramatic purple prose (*"blistering"*, *"into the void"*, *"worthless garbage"*); maintain a clear, authoritative, lucid tone.

3. **The Dilemma-Resolution & Cognitive Closure Law**:
   - Section 1 must introduce a tangible engineering friction/dilemma (e.g., Stop-and-Wait vs Blasting; synchronous disk writes vs durability; polling overhead vs idle connection limits).
   - Section 3 MUST formally resolve that dilemma step-by-step with concrete mechanics (e.g., sliding window, pipelining, WAL append, multiplexing). It is strictly forbidden to state that a protocol "conquers" a dilemma without teaching *how*.
   - Section 3 MUST explicitly derive what that resolution *costs* (e.g., Head-of-Line blocking stalls, memory buffers, cwnd backoff).

4. **Pruning the Irrelevant (Laser Focus on Core Causality)**:
   - Exclude trivia that increases cognitive load without serving the core topic or target depth `[concept][mechanics][contrast][trap]`. (e.g., Do not dissect 20-byte binary packet headers or list exotic TCP socket flags when teaching TCP vs UDP; focus laser-sharp on why reliability costs latency and why real-time media chooses UDP).

5. **Strict 1:1 Sign-Off Gate Alignment**:
   - Section 5's Self Evaluation scenario MUST directly test the explicit `— *Tick off when:*` line for that topic from `CURRICULUM.md`, allowing the learner to conclude on their terms when they have internal closure.
   - Never inject out-of-scope stretch scenarios requiring untaught advanced domain knowledge (e.g., requiring cellular bufferbloat / queueing theory for an introductory transport lesson).

6. **Real-World Production Nuance & Grounded Accuracy**:
   - Never present naive caricatures of engineering solutions (e.g., claiming real-time media "just drops frames"). Teach the real production mechanisms: Jitter Buffers, Packet Loss Concealment (PLC), Forward Error Correction (FEC), and Selective NACKs.
   - Never claim a protocol "guarantees" physical properties it cannot control (e.g., "UDP guarantees low latency" ➔ clarify that UDP avoids kernel queue stalls, but cannot alter physical network transit times).

7. **Article Self-Consistency & Factual Rigor (Auditing the Article Against Itself)**:
   - **Derived Numbers Audit**: Recompute every derived calculation against physical formulas. Maintain exactly one running numerical example per article.
   - **Example-to-Mechanism Coherence**: Scenarios must never contradict mechanisms taught in the same piece (e.g., secondary index scans and bookmark lookups).
   - **Scoped Claims (No Unhedged Absolutes)**: Ban unhedged absolutes (*"literally cannot"*, *"passes through all firewalls"*, *"guarantees zero latency"*, *"eliminated all stalls"*). State physical boundaries and fallbacks explicitly.
   - **Term Ordering Invariant**: Terms must never be referenced before their defining jargon card.
   - **Clean Browser-Native Unicode**: Use clean Unicode (`O(log N)`, `≈ 24`, `×`, `≤`) rather than uncompiled LaTeX syntax in HTML.
   - **Label & Identifier Coherence**: All IDs and labels must match 1:1 between prose, diagrams, and simulator.
   - **Self-Contained Sign-Off Prompts**: Prompts must only require what was taught, or be marked as `[Stretch Exploration]`.
   - **Post-Edit Regression & Orphaned-Term Verification**:
     - *Audit Removed Boxes*: When a jargon box is removed or merged, grep the entire piece for all terms previously defined in that box to ensure no technical terms are left dangling undefined.
     - *Audit Notation Leakage*: Prevent protocol-specific numbering conventions (e.g. odd HTTP/2 stream IDs) from bleeding into older protocol examples (e.g. sequential HTTP/1.1 requests #1, #2, #3).
     - *Tipping-Point Arithmetic Rigor*: Any tipping point (e.g. query planner abandoning an index, bandwidth-delay window sizing) must be derived using the article's own stated latencies, sizes, and throughputs.

---

## 8. Tactile Simulators & Direct Manipulation Architecture (v4.1+)

Starting in **v4.1.0**, interactive failure simulators are freed from rigid schema constraints and authored as direct interactive HTML nodes (`SimulatorHtmlNode`, `builder.add_simulator_html(html, script=...)`), unlocking 100% agent creativity while enforcing automated pre-flight quality invariants:

### Automated Pre-Flight Simulator Quality Audits:
1. **Direct Manipulation Controls**: Every simulator must contain at least two physical controls:
   - An **Action Trigger** (e.g., `Transmit`, `Step`, `Insert Key`, `Query`).
   - A **Failure Injection Toggle** (e.g., `Drop Packet #2`, `Sever Partition`, `Corrupt Block`, `Expire Key`).
2. **DOM-to-JavaScript Identifier Coherence**: Every DOM element ID queried in JavaScript (`getElementById`, `querySelector('#...')`) is verified to exist in the rendered HTML markup.
3. **Headless Script Syntax Verification**: JavaScript logic is validated via headless Node.js syntax checking (`node -e`) before file emission.
4. **Causal Telemetry Log Wiring**: Simulators with an event log (`#sim-log`) must actively write simulation events to the log in JavaScript.
5. **Live Telemetry Gauges**: Quantitative metric counters (`id="tel-..."` or `id="metric-..."`) display real-time physical metrics (latency, drop rates, queue depth, throughput).

---

## 9. Responsive Collision-Aware Inline Jargon Popovers

Lessons feature non-disruptive inline jargon unpackers (`<span class="jargon-tooltip-wrapper">`):
- **Collision-Aware Dynamic Flipping**: Popovers measure their bounding rectangle (`card.offsetHeight`) dynamically. If vertical space above is insufficient (`spaceAbove < cardHeight + safetyMargin`), the card flips below (`popover-below`).
- **Container-Aware Boundary Clamping**: Popovers dynamically calculate visible container viewport bounds (`lesson-main-viewport` and window edges). The card's horizontal position is clamped to guarantee it never extends past the container's left edge (preventing cut-offs against the sidebar) or right edge, while automatically clamping `max-width` on mobile screens.
- **High-Z-Index & Boundary Hugging**: Styled with `z-index: 9999` and `max-height: calc(100vh - 48px); overflow-y: auto;` to eliminate scroll container clipping and prevent text obscuration.
- **Leaked Markdown Sanitization**: Automated preprocessing (`clean_markdown_leaks_in_html`) ensures markdown bold syntax (`**`) never leaks raw asterisks around inline tooltips or in paragraph text.
- **Sole Authoritative Lesson Medium**: Lessons are delivered strictly as interactive HTML artifacts (`<slug>.html`), while study notes remain in GitHub Flavored Markdown (`notesDir`).



