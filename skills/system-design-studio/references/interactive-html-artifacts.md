# Interactive HTML Lesson Artifacts & Visual Pedagogy

## Overview

In the System Design Studio, external drawing boards (such as tldraw or Excalidraw) and external documentation systems (such as Notion) are **not used**. 

Instead, **interactive, beautifully crafted HTML artifacts** serve as the complete visual and pedagogical medium. Every substantive topic is delivered as a self-contained, modern HTML artifact featuring:
- Causal, narrative storytelling (no flat bullet points).
- Interactive step-through simulators (e.g. simulating packet loss, head-of-line blocking, quorum voting, cache stampedes).
- Tailored SVG / CSS diagrams and sequence timelines.
- Real-world workload contrast cards.
- Integrated engineering challenges and interactive accordions.

---

## 1. Storage & Placement

Every topic artifact is saved in two locations:
1. **Conversation Artifact Directory**: `<appDataDir>/brain/<conversation-id>/<topic-slug>.html` (renders in the host environment's side pane with `UserFacing: true`).
2. **Project Learning Instance**: `.system-design/lessons/<topic-slug>.html` (committed to git as part of the learner's personal repository).

---

## 2. Design Standards & Typography

- **CSS Framework**: Tailwind CSS via the allowlisted CDN:
  ```html
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  ```
- **Semantic Theme Variables**:
  - Backgrounds: `bg-[var(--background)]`, `bg-[var(--card)]`
  - Borders: `border-[var(--border)]`, `border-[var(--card-border)]`
  - Text: `text-[var(--foreground)]`, `text-[var(--muted-foreground)]`
  - Accents: `bg-[var(--primary)]`, `text-[var(--primary)]`, `text-blue-500`, `text-emerald-500`, `text-rose-500`
- **Component Anatomy**:
  - **Hero Header**: Tier, Cluster code, Topic name, target depth badges (`[concept] [mechanics] [contrast] [trap]`).
  - **Causal Narrative**: Grounded in physical realities (speed of light, hardware I/O, packet buffer bloat).
  - **Interactive Simulation**: Step-by-step trace with toggleable modes and animated state chips.
  - **Workload Contrast**: Side-by-side analysis of two opposing systems (e.g. Financial Ledger vs WebRTC Voice).
  - **Invariant Matrix**: Clean comparison table outlining guarantees vs non-guarantees.
  - **Engineering Reality Check**: Bounded architectural problem with revealable solution.
