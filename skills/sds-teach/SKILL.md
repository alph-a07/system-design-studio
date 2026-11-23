---
name: sds-teach
description: Deliver the next or specified interactive system design lesson artifact in System Design Studio.
argument-hint: "[topic] [--full-depth]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 4.0.0
---

# /sds-teach — Interactive System Design Lesson Engine

Deliver an immersive, first-principles system design lesson artifact featuring tactile simulators (HTML) and visual diagrams (Markdown) deterministically compiled from structured causal JSON payloads.

## Subagent Architecture & Agentic Efficiency

To ensure the highest cognitive quality without polluting coordinator dialog history, `/sds-teach` employs a specialized subagent topology where supported, with deterministic scripts handling mechanical rendering:

```
┌────────────────────────────────────────────────────────┐
│                   Coordinator Agent                    │
│   • Inline context resolution (active project only)    │
│   • Zero lecture in chat (strict 5-12 line bridge)     │
│   • Hypothesis-first dialogue prompt                   │
└───────────────┬────────────────────────▲───────────────┘
                │                        │
       1. Invoke (prompt)        3. Audit result (file path)
                │                        │
                ▼                        │
┌──────────────────────────────┐         │
│      sds-lesson-crafter      │         │
│   • 2,500+ word deep essay   │         │
│   • Dilemma-resolution trace │         │
│   • Inline jargon tooltips   │         │
│   • Tactile simulator spec   │         │
│   • Writes .generated-*.json │         │
└───────────────┬──────────────┘         │
                │                        │
       2. Audit payload on disk          │
                ▼                        │
┌──────────────────────────────┐         │
│     sds-pedagogy-auditor     │─────────┘
│   • Adversarial math check   │
│   • Jargon order verification│
│   • Sign-off gate alignment  │
└──────────────────────────────┘
                │
         4. Compiled by deterministic script
                ▼
┌──────────────────────────────┐
│       render-lesson.py       │ ──► .system-design/lessons/<slug>.html
│   • Dual HTML & Markdown out │ ──► .system-design/lessons/<slug>.md
│   • Regex/AST verification   │ ──► Auto-stages to conversation brain
└──────────────────────────────┘
```

### Token-Efficiency & Architectural Pruning Rationale

To prevent token waste and latency degradation, tasks are partitioned strictly by cognitive ROI:
- **`sds-lesson-crafter` (KEPT - LLM Subagent)**: High-ROI creative & causal authoring. Writes the 2,500+ word JSON payload directly to `.system-design/lessons/.generated-<slug>.json`, keeping massive raw JSON strings out of the coordinator's dialog context.
- **`sds-pedagogy-auditor` (KEPT - LLM Subagent)**: High-ROI adversarial critique. Prevents authoring confirmation bias by verifying math, term ordering, and gate alignment directly against the file on disk.
- **Context Analyzer (DROPPED - Inlined in Coordinator)**: Reading `CURSOR.md` and `settings.json` takes 5ms via `read_file`. Delegating to a subagent would waste ~3,000 tokens and 5s latency.
- **Content Renderer & Reviewer (DROPPED - Script-Automated)**: `render-lesson.py` compiles both HTML/JS and Markdown editions deterministically in <50ms with 0 token cost.
- **Notes & Revision Makers (DROPPED - Script-Automated)**: `compile-notes.py` and `update-revisions.py` handle disk formatting deterministically on sign-off with 0 token waste.

---

## Mandatory Architectural & Pedagogical Invariants

0. **STRICT ACTIVE PROJECT CONTEXT ISOLATION (ZERO CROSS-PROJECT LEAKAGE)**:
   - Under NO circumstances may any agent (coordinator or subagent) read, search, infer, or incorporate context, examples, history, notes, or code from other chats, workspaces, or projects in `~/.system-design-studio/projects/`.
   - All context MUST strictly come from the active project workspace: `.system-design/CURSOR.md`, `.system-design/CURRICULUM.md`, `.system-design/DECISIONS.md`, and `.system-design/manifest.json`.
   - If the active project has zero completed topics, treat it as a pristine clean slate. Do NOT invent prior knowledge or import examples from external projects.

0b. **DETERMINISTIC FLAGSHIP GUARDRAILS & COORDINATOR DELIVERY SEPARATION**:
   - Flagship models (e.g. Claude 3.7 / 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro) are STRICTLY FORBIDDEN from generating or outputting lesson text, summaries, or lectures in the coordinator chat turn.
   - The coordinator turn MUST be strictly a 5–12 line delivery bridge containing:
     1. Topic Title and Hierarchy (`Tier` -> `Cluster`)
     2. Clickable links to both delivered formats: `[Open Interactive Lesson (HTML)](file:///...)` and `[Open Complete Notes (Markdown)](file:///...)`
     3. The opening Hypothesis Dilemma / Architectural Defense Challenge question to prompt the learner's thinking and invite dialectic defense directly in chat.
   - NEVER duplicate or summarize the lesson body in chat. The lesson belongs exclusively in the delivered artifacts.

---

## Mandatory Architectural & Pedagogical Invariants

1. **EXPLANATIONS OVER STATEMENTS ("THE EXPLAINER'S CONTRACT")**:
   - The reader must experience *getting explained → understanding*, never *read raw data → struggle to process → understand*. We do the reading, synthesizing, and cognitive heavy lifting for them to deliver direct, crystal-clear explanations.
   - Never just state that a mechanism exists or list its properties. Walk the reader step-by-step through *why* it was invented, the tangible friction engineers faced, the intuitive real-world mental model (non-leaky analogies), and what happens step-by-step under the hood.

2. **EDITORIAL COHESION & VOICE ("TOP-TIER TECH ESSAY / SUBSTACK VIBE")**:
   - The artifact MUST NOT read or look like a dry API reference, cold wiki page, or RFC manual.
   - It MUST read like an acclaimed, beautifully written engineering deep-dive essay (Dan Luu / Bartosz Ciechanowski / Julia Evans vibe): conversational yet rigorous, narrative-driven, connecting each puzzle piece into one overarching architectural story.
   - Use engaging section narratives, smooth conceptual transitions, and authorial guidance (*"Let's pause here, because this is where everyone gets tripped up...", "Wait, why couldn't we just...?"*).

3. **MANDATORY JARGON UNPACKING AS INLINE TOOLTIPS (ZERO ORPHANED BUZZWORDS)**:
   - Readers must NEVER have to leave the page or open a search engine to look up an acronym or buzzword while reading.
   - Unpack domain acronyms, protocol keywords, and systems buzzwords (e.g. *Head-of-Line Blocking*, *Middlebox*, *Ossification*, *RTT*, *BDP*, *TCP 3-Way Handshake*, *4-Tuple*, *ALPN*, *Alt-Svc*, *P99*) primarily as **inline tooltips** (`<span class="jargon-tooltip-wrapper"><span class="jargon-inline-cue" onclick="toggleJargonTooltip(this, event)">Term</span><span class="jargon-popover-card">...</span></span>` or generated via `lesson_builder.build_jargon_tooltip(...)`) directly inside the sentence where the term appears.
   - This keeps the reading narrative fluid and unbroken, while providing a wide 80% popover on hover/click, automatically indexed into the HTML Glossary Drawer and compiled into a clean section glossary in Markdown.
   - Plain English FIRST, systems label second: Describe the concept in intuitive everyday terms before stamping it with its formal technical term. Ban dense noun-stacking (e.g., replace *"monotonic ordering"* with *"strictly in-order sequence"*; replace *"stateless boundary-preserving datagram"* with *"standalone message with clear boundaries"*).
   - Eliminate melodramatic purple prose (*"blistering"*, *"into the void"*, *"worthless garbage"*); maintain a clear, authoritative, lucid tone.

4. **ANTI-COMPRESSION & EXPLAINER DEPTH INVARIANT (BAN THE CHEAT SHEET)**:
   - A lesson must NEVER read like a compressed engineer's cheat sheet, summary table, or bullet-point review.
   - **Standard Mode**: 2,500–3,500 words of progressive, unfolding narrative prose. Concepts must have breathing room: physical dilemma ➔ mental model ➔ internal mechanics & step-by-step trace ➔ failure modes & costs ➔ production reality ➔ defense gate.
   - **Full-Depth Mode (`--full-depth`)**: When requested on-demand, go to the absolute internal bottom depth of the topic: trace every abstraction down to OS kernel buffer queues, POSIX syscalls (`read()`, `write()`, `epoll()`, `fsync()`), memory registers, hardware flash/silicon layers, and physical wire propagation limits. Target 3,500–5,000+ words.

5. **THE DILEMMA-RESOLUTION & COGNITIVE CLOSURE LAW**:
   - Section 1 must introduce a tangible engineering friction/dilemma (e.g., Stop-and-Wait vs Blasting; synchronous disk writes vs durability; polling overhead vs idle connection limits).
   - Section 3 MUST formally resolve that dilemma step-by-step with concrete mechanics (e.g., sliding window, pipelining, WAL append, multiplexing). It is strictly forbidden to state that a protocol "conquers" a dilemma without teaching *how*.
   - Section 3 MUST explicitly derive what that resolution *costs* (e.g., Head-of-Line blocking stalls, memory buffers, cwnd backoff).

6. **PRUNING THE IRRELEVANT (LASER FOCUS ON CORE CAUSALITY)**:
   - Exclude trivia that increases cognitive load without serving the core topic or target depth `[concept][mechanics][contrast][trap]`. (e.g., Do not dissect 20-byte binary packet headers or list exotic TCP socket flags when teaching TCP vs UDP; focus laser-sharp on why reliability costs latency and why real-time media chooses UDP).

7. **STRICT 1:1 SIGN-OFF GATE ALIGNMENT**:
   - Section 5's architectural defense challenge MUST directly test the explicit `— *Tick off when:*` line for that topic from `CURRICULUM.md`.
   - Never inject out-of-scope stretch scenarios requiring untaught advanced domain knowledge (e.g., requiring cellular bufferbloat / queueing theory for an introductory transport lesson).

8. **REAL-WORLD PRODUCTION NUANCE (BEYOND NAIVE TRADEOFFS)**:
   - Never present naive caricatures of engineering solutions (e.g., claiming real-time media "just drops frames"). Teach the real production mechanisms: Jitter Buffers, Packet Loss Concealment (PLC), Forward Error Correction (FEC), and Selective NACKs.
   - Never claim a protocol "guarantees" physical properties it cannot control (e.g., "UDP guarantees low latency" ➔ clarify that UDP avoids kernel queue stalls, but cannot alter physical network transit times).

9. **ARTICLE SELF-CONSISTENCY & FACTUAL RIGOR (AUDITING THE ARTICLE AGAINST ITSELF)**:
   - **Derived Numbers Audit**: Recompute every derived calculation against physical formulas. Maintain exactly one running numerical example per article without shifting parameters.
   - **Example-to-Mechanism Coherence**: Ensure scenarios do not contradict mechanisms taught in the same piece (e.g., if secondary indexes require bookmark lookups, a range scan on a secondary index cannot claim to avoid clustered index reads unless explicitly modeled as a covering index).
   - **Scoped Claims (No Unhedged Absolutes)**: Ban unhedged absolutes (*"literally cannot"*, *"passes through all firewalls"*, *"guarantees zero latency"*, *"eliminated all stalls"*). State physical boundaries and real-world exceptions explicitly (e.g., enterprise middleboxes blocking UDP 443; in-stream ordering still holding in HTTP/3).
   - **Term Ordering Invariant**: Terms must never be referenced before their defining jargon card.
   - **Clean Browser-Native Unicode**: In HTML mode, render mathematical notation with clean Unicode (`O(log N)`, `≈ 24`, `×`, `≤`) rather than uncompiled LaTeX tokens (`$O(1)$`, `\approx`).
   - **Label & Identifier Coherence**: Stream numbers, IDs, and labels must match 1:1 across prose, diagrams, and simulators (e.g., adhering to protocol standards such as HTTP/2 client-initiated streams being odd-numbered).
   - **Self-Contained Sign-Off Prompts**: Challenges must be fully answerable from the lesson's taught concepts, or explicitly marked as `[Stretch Exploration]`.

10. **STRICT PROHIBITION OF GENERIC BOILERPLATE**:
   - You MUST NOT deliver abstract or mad-libs template text (such as *"The system maintains dual kernel/storage states"*).
   - Every lesson MUST be deeply grounded in the physical reality of the topic: exact protocol headers, byte sizes, physical network propagation limits, kernel queue boundaries, OS socket syscalls, and hardware invariants.

10. **TACTILE INTERACTIVE SIMULATOR CONTRACT (HTML MODE)**:
   - In HTML mode, the simulator MUST NOT be a passive 3-click mock.
   - It MUST provide real-time interactive manipulation of the topic's core failure mode (e.g., toggling packet drops to demonstrate Head-of-Line blocking in the kernel receive queue, comparing TCP stalls vs UDP pass-through, and visualizing P99 tail latency).

11. **HYPOTHESIS-FIRST ACTIVE LEARNING GATE**:
   - In your initial chat response, you MUST prompt the learner for their working mental model before handing over the solution:
     *"Before we inspect the internal mechanics of [Topic], what is your initial intuition on [Concrete Dilemma]?"*
   - Capture their response in chat; this becomes Section 1 of their permanent active-learning study note upon sign-off.

12. **AUTOMATED PRE-FLIGHT QUALITY AUDIT (ZERO-REGRESSION GATEWAY)**:
   - Every compiled lesson artifact is audited automatically by `render-lesson.py`:
     1. Narrative word count (>= 2,000 words; blocks premature compression).
     2. Jargon unpacking density (>= 3 `<div class="jargon-card">` callouts).
     3. Section 1 dilemma presence & Section 3 mechanical resolution.
     4. Curriculum sign-off gate alignment against `CURRICULUM.md`.
     5. Rejection of melodramatic fluff or leaked template tokens.

13. **SINGLE-SOURCE REPOSITORY ENGINE**:
   - Dispatch scripts located at `~/.system-design-studio/skills/system-design-studio/scripts/` (or repository-local scripts if working inside the studio repo).

14. **READ-ONLY STUDIO ENGINE & ZERO-VCS LEAKAGE**:
   - The studio repository (`system-design-studio`) is an invariant software engine. You MUST NOT edit `render-lesson.py` or commit lesson content into the studio repository.
   - All authored lessons live exclusively in the learner's project instance (`.system-design/lessons/`).
   - When generating custom lessons, author the structured payload (narrative prose, analogies, jargon unpackers, and tactile simulator) and pass it to `render-lesson.py` via `--data-file <json>` or `--data '<json>'` (or stdin). Never hardcode lessons into Python scripts.

15. **POST-EDIT REGRESSION & ORPHANED-TERM VERIFICATION PASS**:
   - After making any edit or refinement to a lesson artifact:
     1. **Audit Deleted or Renamed Explanatory Boxes**: Grep the entire lesson text for every technical term that was previously introduced in a removed, merged, or renamed card (e.g. sequential vs. random I/O, FCP). Ensure those terms are either restored with clear definitions or rephrased if left dangling without context.
     2. **Audit Protocol Notation Leakage**: Ensure notation or identifier conventions introduced for one protocol/version (e.g. odd-numbered stream IDs in HTTP/2) do not bleed backward or forward into adjacent discussions of different protocols (e.g. HTTP/1.1 pipelined requests, which lack stream IDs and must be numbered sequentially as #1, #2, #3).
     3. **Verify Tipping-Point & Arithmetic Thresholds**: Recompute any performance tipping points (e.g. query planner scan thresholds, bandwidth-delay products, or receive window limits) against physical hardware and network formulas, rather than asserting arbitrary cutoffs.

## 🚨 MANDATORY EXECUTION PROTOCOL: SUBAGENT DELEGATION & ZERO STATIC SERVING

When executing `/sds-teach`:

1. **SUBAGENT INVOCATION IS REQUIRED**:
   - In Antigravity (and any environment where `invoke_subagent` is available in your tool set), you MUST invoke `sds-lesson-crafter` via `invoke_subagent`.
   - You are STRICTLY FORBIDDEN from generating or compiling a lesson in the coordinator turn without delegating to `sds-lesson-crafter`.
   - Never skip subagents to take a shortcut. The user expects full autonomous subagent collaboration.

2. **SECTION EXAMPLES ARE FOR CALIBRATION ONLY — NEVER SERVED DIRECTLY**:
   - The snippet files in `resources/examples/sections/*.json` and `resources/examples/ui-components.json` are SECTION-WISE REFERENCE BLUEPRINTS ONLY across diverse topics. They demonstrate dilemma formulation, simulator specifications, and inline tooltip mechanics.
   - You are STRICTLY FORBIDDEN from passing files in `resources/examples/` directly to `render-lesson.py`. `render-lesson.py` will actively abort with an error if you attempt to do so.
   - The lesson payload passed to `render-lesson.py` MUST be a freshly authored JSON payload created by `sds-lesson-crafter` that is personalized to:
     a) The user's active curriculum track (e.g. `full-mastery` vs `interview-sprint`).
     b) Topics already completed by this learner (building on them without re-explaining).
     c) Topics deferred with anchor notes (addressing known gaps).
     d) The learner's initial hypothesis on the central dilemma.
     e) Backward anchors and forward hooks in the curriculum chain.

## Execution Sequence

### Step 1: Inlined Context Resolution & Hypothesis Gate (Coordinator)
- **Target Topic & Full-Depth**:
  - Check `$ARGUMENTS` for `--full-depth` flag or user request for exhaustive internal depth.
  - Resolve topic ID from `$ARGUMENTS` (stripping flags) or read `activeFocus.topicId` from `.system-design/CURSOR.md`.
- **Curriculum Context**: Read `CURRICULUM.md` to extract:
  - Active Track name
  - Tier & Cluster name
  - Specific `— *Tick off when:*` sign-off condition
  - Backward anchor topic & forward hook topic
- **Learner Progress & History**: Read `.system-design/CURSOR.md`:
  - `completedTopics` (established mental models to build upon)
  - `deferredQueue` (known gaps or parked questions)
  - `examplesTaken` (established real-world metaphors to maintain continuity)
- **Reference Section Snippets**:
  - The subagent can inspect `~/.system-design-studio/skills/system-design-studio/resources/examples/sections/` and `ui-components.json` for component formatting and section tone calibration.
- **Learner Hypothesis Prompt**:
  - In your chat turn, prompt the learner for their initial working hypothesis on the topic's core dilemma before handing over the solution:
    *"Before we inspect the internal mechanics of [Topic], what is your initial intuition on [Concrete Dilemma]?"*

### Step 2: Mandatory Subagent Delegation (`sds-lesson-crafter`)
- Call `invoke_subagent`:
  ```json
  {
    "TypeName": "sds-lesson-crafter",
    "Role": "Deep Causal Lesson Author",
    "Prompt": "<Comprehensive prompt containing topic details, curriculum track, full_depth flag (if --full-depth requested), completed topics to reference (from active project ONLY), and instructions to use lesson_builder.py. Instruct subagent to write JSON directly to .system-design/lessons/.generated-<slug>.json>"
  }
  ```
- The subagent crafts a completely fresh structured lesson payload (2,500+ words standard, or 3,500–5,000+ words if `--full-depth`) using the shipped builder script (`from lesson_builder import LessonBuilder...`), unpacking jargons primarily as inline tooltips, and saves it directly to `.system-design/lessons/.generated-<slug>.json`.
- The subagent returns a concise status message with word count, file path, and the central dilemma.

### Step 3: Adversarial Pedagogical Audit (`sds-pedagogy-auditor`)
- Invoke `sds-pedagogy-auditor` pointing to `.system-design/lessons/.generated-<slug>.json` to verify derived math, term ordering, inline tooltip usage, and 1:1 sign-off gate alignment.
- Crafter amends payload file on disk if any flaws are flagged until `APPROVED`.

### Step 4: Deterministic Compilation (`render-lesson.py`)
- Compile via `render-lesson.py` (which simultaneously emits both HTML and Markdown, applies full-depth badges if requested, and syncs cursor status to `delivered`):
  ```bash
  python3 ~/.system-design-studio/skills/system-design-studio/scripts/render-lesson.py \
    --topic-id <topic-id> \
    --style <theme> \
    [--full-depth] \
    --data-file <project-dir>/.system-design/lessons/.generated-<slug>.json
  ```

### Step 5: Clean Delivery Bridge (Coordinator)
- Deliver a concise 5–12 line response in chat (NEVER dump lecture text):
  1. Topic Title and Hierarchy (`Tier` ➔ `Cluster`)
  2. Clickable links to both formats:
     - `[Open Interactive Lesson (HTML)](file:///<path-to-lesson.html>)`
     - `[Open Complete Notes (Markdown)](file:///<path-to-lesson.md>)`
  3. The Opening Hypothesis Dilemma / Defense Challenge prompt:
     *"Before we dissect the underlying mechanics, consider this core dilemma: [Concrete Dilemma from Lesson]. How would you approach this, or what physical constraint makes naive solutions fail? Review the artifact and defend your thesis directly in chat."*

---

### Universal Fallback (Only in runtimes without `invoke_subagent`)
If and ONLY IF running in a non-subagent CLI (e.g. vanilla terminal script runner):
1. The coordinator acts as both author and auditor sequentially.
2. Author the full custom JSON payload in-context following all 15 invariants.
3. Save the payload to `.system-design/lessons/.generated-<slug>.json`.
4. Compile with `render-lesson.py --data-file <path>`. NEVER point to `resources/examples/`.
