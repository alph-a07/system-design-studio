---
name: sds-teach
description: Deliver the next or specified interactive system design lesson artifact in System Design Studio.
argument-hint: "[topic]"
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.3.1
---

# /sds-teach — Interactive System Design Lesson Engine

Deliver an immersive, first-principles system design lesson artifact featuring tactile simulators (HTML) or visual diagrams (Markdown) based on instance settings.

## Mandatory Architectural & Pedagogical Invariants

1. **EXPLANATIONS OVER STATEMENTS ("THE EXPLAINER'S CONTRACT")**:
   - The reader must experience *getting explained → understanding*, never *read raw data → struggle to process → understand*. We do the reading, synthesizing, and cognitive heavy lifting for them to deliver direct, crystal-clear explanations.
   - Never just state that a mechanism exists or list its properties. Walk the reader step-by-step through *why* it was invented, the tangible friction engineers faced, the intuitive real-world mental model (non-leaky analogies), and what happens step-by-step under the hood.

2. **EDITORIAL COHESION & VOICE ("TOP-TIER TECH ESSAY / SUBSTACK VIBE")**:
   - The artifact MUST NOT read or look like a dry API reference, cold wiki page, or RFC manual.
   - It MUST read like an acclaimed, beautifully written engineering deep-dive essay (Dan Luu / Bartosz Ciechanowski / Julia Evans vibe): conversational yet rigorous, narrative-driven, connecting each puzzle piece into one overarching architectural story.
   - Use engaging section narratives, smooth conceptual transitions, and authorial guidance (*"Let's pause here, because this is where everyone gets tripped up...", "Wait, why couldn't we just...?"*).

3. **MANDATORY JARGON UNPACKING (ZERO ORPHANED BUZZWORDS)**:
   - Readers must NEVER have to leave the page or open a search engine to look up an acronym or buzzword while reading.
   - Every domain acronym, protocol keyword, or systems buzzword introduced (e.g. *Head-of-Line Blocking*, *Middlebox*, *Ossification*, *RTT*, *BDP*, *TCP 3-Way Handshake*, *4-Tuple*, *ALPN*, *Alt-Svc*, *P99*) MUST be accompanied by an immediate plain-English translation callout (`<div class="jargon-card">` or inline micro-pill) right where it appears.
   - Plain English FIRST, systems label second: Describe the concept in intuitive everyday terms before stamping it with its formal technical term. Ban dense noun-stacking (e.g., replace *"monotonic ordering"* with *"strictly in-order sequence"*; replace *"stateless boundary-preserving datagram"* with *"standalone message with clear boundaries"*).
   - Eliminate melodramatic purple prose (*"blistering"*, *"into the void"*, *"worthless garbage"*); maintain a clear, authoritative, lucid tone.

4. **ANTI-COMPRESSION & EXPLAINER DEPTH INVARIANT (BAN THE CHEAT SHEET)**:
   - A lesson must NEVER read like a compressed engineer's cheat sheet, summary table, or bullet-point review.
   - For any topic introducing architectural primitives or protocols with prerequisites, the lesson MUST provide 2,500–3,500 words of progressive, unfolding narrative prose. Concepts must have breathing room: physical dilemma ➔ mental model ➔ internal mechanics & step-by-step trace ➔ failure modes & costs ➔ production reality ➔ defense gate.

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

## Execution Sequence

1. **Resolve Topic & Settings**:
   - Target Topic: If `$ARGUMENTS` is provided (e.g. `0.1` or `topic.0.1.tcp-vs-udp`), resolve that topic from `CURRICULUM.md`. Otherwise, read `activeFocus.topicId` from `.system-design/CURSOR.md`.
   - Settings: Inspect `.system-design/settings.json` for `outputType` (`html` or `markdown`), `artifactStyle`, and `paths.lessonsDir`.

2. **Render Lesson Artifact**:
   - For bespoke topics, craft the lesson payload JSON following the pedagogical invariants and compile via the studio lesson rendering engine:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/render-lesson.py \
       --topic-id <topic-id> \
       --format <html|markdown> \
       --style <theme> \
       --data-file <payload.json>
     ```
     *(If a reference fixture exists in `resources/examples/lessons/`, `--data-file` can be omitted).*
   - Target path: `<project-root>/.system-design/lessons/<slug>.<ext>`
   - In **Antigravity**: Stage the artifact to `<appDataDir>/brain/<conversation-id>/<slug>.html` (or `.md`) and surface it in the chat for side-pane inspection.

3. **Mandatory Pre-Flight Quality Audit**:
   - Inspect the compiled artifact before signaling completion. Verify that:
     1. Tone check: Does this feel like an engaging, beautifully written tech essay rather than a documentation page?
     2. Explainer check: Does it explain the *why* and mechanical causality rather than merely listing facts?
     3. Jargon check: Are all buzzwords and acronyms unpacked in immediate plain-English callouts?
     4. Zero unreplaced template tokens exist (no leaked `[concept]`, `{{...}}`, or theme labels).
     5. The simulator or diagram directly models the specific failure mode of the topic.
     6. Backward Anchor and Forward Hook accurately reflect the curriculum sequence.

4. **Present Interactive Artifact & Prompt Dialogue**:
   - Provide a direct markdown link: `[Open Interactive Lesson: <Topic>](file:///<path-to-lesson>)`.
   - Highlight the central architectural dilemma and invite the learner's initial hypothesis.
