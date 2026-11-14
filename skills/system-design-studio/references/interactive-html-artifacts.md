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

## 4. The 6-Part Component Anatomy

Every interactive lesson artifact follows an invariant 6-part component anatomy engineered for exhaustive mechanical closure:

1. **Hero Header**:
   - Tier badge, Cluster code, Topic formal title, depth markers (`[concept] [mechanics] [contrast] [trap]`), and active theme indicator.
2. **Topic Foundation & Mental Model (The Orientation)**:
   - Answers the 6 Foundation Questions: Physical Problem & Motivation, System Placement (OSI/Stack), Design Relevance, Prerequisites & Vocabulary, Intuitive Mental Model, and Pedagogical Bridge.
3. **Digestible Explanations: The Whys & Hows (Exhaustive Mechanical Closure)**:
   - **Dedicated pedagogical space** ensuring no black boxes remain:
     - **The "Why"**: The underlying physical dilemma, why naive alternatives fail, and why this specific architecture was forced into existence.
     - **The "How"**: Internal causal mechanics, actors and boundaries, data packet/record layouts, kernel/storage buffer states (`Send-Q`/`Recv-Q`), sequential execution traces, and failure domain boundaries.
     - **Visual Mechanism Diagrams**: Inline SVG / CSS sequence or flowchart diagrams illustrating state transitions.
     - **Invariant Boundaries**: Explicit distinction between what is mathematically guaranteed vs what is intentionally non-guaranteed.
4. **Interactive Execution Simulator**:
   - Dynamic sandbox with toggleable protocols/modes, live fault injection (packet drop, node partition, buffer saturation), animated data chips, and telemetry metrics (latency, jitter, queue depth).
5. **Workload Contrast & Invariant Matrix**:
   - Side-by-side contrast of two opposing production workloads (e.g. *Financial Ledger* vs *WebRTC Real-time Voice*).
   - Structured invariant comparison matrix evaluating dimensions such as ordering, setup overhead, loss tolerance, and recovery costs.
6. **Final Sign-Off Challenge (Unassisted Verification Gate)**:
   - Bounded, realistic architectural failure scenario testing the topic's tick-off criteria **left deliberately without an answer or reveal toggle**. The learner analyzes and defends their breakdown in chat; sign-off status is evaluated strictly on the reader's independent reasoning.
