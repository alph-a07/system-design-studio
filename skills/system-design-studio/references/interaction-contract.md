# Interaction Delivery Contract & Pacing

## Purpose

Makes the delivery of instruction deterministic, robust, and pedagogically sound across invocations, turn boundaries, and fresh chats. The learner experiences a **continuous, unbroken learning process** rather than an erratic series of disjointed micro-quizzes or cognitive clutter from duplicated text.

---

## 1. The Delivery Contract: Strictly Artifact-First on Topic Entry, Inline for Follow-ups

### The Anti-Pattern: Hybrid Lecture Duplication
A major failure mode in AI tutoring is the **Hybrid Dump**: generating an interactive HTML artifact and simultaneously spewing 500 lines of markdown duplicating the exact same foundation, diagrams, and tables inline in the chat. 

This causes:
- Severe cognitive fatigue and visual clutter.
- Ambiguity over where the learner should look (the side pane or the chat).
- Devaluation of the interactive HTML medium.

### The Standard: Pure Separation of Concerns
1. **Topic Entry (First Turn on a Topic)**:
   - The entire comprehensive lesson—including the 6 foundation questions, hardware physics, causal mechanics, interactive simulators, workload contrast cards, invariant matrix, and reality check—is delivered **strictly inside the standalone interactive HTML artifact**.
   - The in-chat response must be **strictly a concise delivery bridge** (5–12 lines):
     1. Acknowledge the active topic, cluster code, and tier.
     2. Provide a direct clickable link to the generated artifact in `<appDataDir>/brain/<conversation-id>/<topic-slug>.html` (and `.system-design/lessons/<topic-slug>.html`).
     3. State the core physical force or architectural problem in 2–3 sentences.
     4. Direct the learner to open the artifact in the side pane to interact with the simulator.
     5. Conclude with an opening discussion hook or reality check prompt to invite discussion when ready.
   - **Do not output the lesson body, foundation text, or ascii tables inline in the chat on topic launch.**

2. **Same-Topic Follow-ups (Subsequent Turns on the Same Topic)**:
   - Once the topic artifact has been delivered, all follow-up discussions, Q&A, drill-downs, code traces, trade-off debates, and evaluation of the reality check happen **directly inline within the chat conversation**.
   - Do NOT generate another HTML artifact for follow-up conversational turns on the same topic.
   - The conversation flows naturally in chat: the learner asks questions, proposes designs, or answers the reality check; the tutor evaluates reasoning, stress-tests edge cases, and provides causal closure directly in chat.

3. **Advancement to Next Topic**:
   - Only when the current topic invariants are verified and mastered does the tutor advance the cursor (`advance-cursor.py`) and trigger the strictly HTML artifact delivery rule again for the next topic's foundation.

---

## 2. Artifact Visual Styles & User Preference

During workspace bootstrap or initial setup, the studio prompts the user to select their preferred visual theme for lesson artifacts from the **5 Studio Themes**:
1. `slate-clean` — **Modern Slate (Dark Tech)** `[Default]`: Deep slate background (`#0f172a`), vibrant blue/indigo accents. Modern developer IDE aesthetic.
2. `editorial-paper` — **Clean Editorial (Warm Light)**: High-readability warm off-white canvas (`#fbfbfa`) with sharp typography and ink/coral accents.
3. `midnight-neon` — **Cyber Obsidian (High Contrast)**: Pitch black obsidian canvas (`#05070c`) with electric cyan and mint neon highlights.
4. `nordic-frost` — **Nordic Frost (Polar Calm)**: Arctic cool dark palette (`#2e3440`) with frosty teal and snow-storm text for calm, focused study.
5. `warm-amber` — **Warm Amber (Espresso Glow)**: Rich espresso and sepia tones (`#1c1917`) with warm amber/copper accents designed for low eye fatigue.

The selected style is stored in `.system-design/settings.json`:
```json
{
  "$schemaVersion": "2.0",
  "artifactStyle": "slate-clean",
  "deliveryMode": "strictly-artifact-first",
  "inlineDiscussions": true
}
```
Learners can modify `.system-design/settings.json` at any time to switch themes. The renderer (`render-lesson.py`) automatically respects this preference.

---

## 3. The Pacing Contract: Teach Complete Causal Units Before Testing

### The Anti-Pattern: Micro-Quizzing
A common failure in conversational AI tutoring is stopping after every single sentence, definition, or paragraph to ask:
- *"Does that make sense?"*
- *"Now, what do you think ACK stands for?"*
- *"Should we continue to the next part?"*

This fragments the learner's attention and destroys the continuity required to grasp complex distributed systems.

### The Standard: Teach Complete Causal Units
- The studio teaches **complete, causally connected mechanism groups** as an integrated narrative inside the artifact.
- A single explanation encompasses 3 to 5 interrelated concepts (e.g. TCP sequence numbers, cumulative ACKs, receive window, and sliding window buffers) before presenting a meaningful design checkpoint.
- **Do not end every response with a generic question.** A response may conclude with the next part of the causal trace, an architectural synthesis, or a natural stopping point.
- The learner is never required to say "continue" just to receive the next paragraph of an already active explanation. The studio proceeds through the active investigation by default.

---

## 4. Mandatory Topic Foundation Inside the Artifact

Whenever the learner enters a topic for the first time—whether it is Topic 1 in a new curriculum or the 5th topic in an ongoing cluster—the studio MUST embed a comprehensive **Topic Foundation** inside the generated HTML artifact before diving into technical minutiae, code, or packet traces.

### The 6 Foundation Questions (Authored inside the Artifact):
1. **Concrete Problem & Motivation**: What physical limit or architectural breakdown forces this topic into existence?
2. **System Placement**: Where does this component sit in the architectural stack? Who are its neighbors and what are its boundaries?
3. **Design Relevance**: Which trade-offs (latency, durability, consistency, cost) depend on it?
4. **Prerequisites & Vocabulary**: Define necessary terms immediately; eliminate unexplained jargon.
5. **Mental Model**: Provide an intuitive visual or conceptual model of the moving parts before the deep trace.
6. **Learning Bridge**: Connect to what was previously covered and state what will be deferred.

---

## 5. The Teaching Cursor: Living Running Context, Not a Progress Scoreboard

The **Teaching Cursor** is maintained in `.system-design/CURSOR.md` and `manifest.json`.

**The cursor is not merely a progress tracker or completed-topic counter.** It is the **living running context and operational cognitive brain** of the learning instance. It guarantees that any agent, model, or session resumption maintains deep conceptual continuity by explicitly preserving:

1. **Active Focus & Immediate Horizon**:
   - Current Tier, Cluster, Cluster Depth Target, and the Reality Checks that must be answered cold.
   - Active Topic, Target Depth, Foundation Status (`not-started`, `complete`, `needs-repair`), and Mechanism Group.
   - Precise Next Teaching Action with its underlying causal goal.
2. **Connected Cognitive Lineage (Causal Anchors)**:
   - **Backward Anchor**: Where we came from, what foundation was established, and why the current topic is necessary.
   - **Active Mechanism**: The core causal tension and invariant being examined.
   - **Forward Hook**: What remains incomplete that the next topic will resolve.
3. **Examples Registry & Metaphor Continuity (`examplesTaken`)**:
   - The concrete domain scenarios in play (e.g. *Financial Ledger* vs *Live WebRTC Audio*).
   - Whether the tutor is extending an existing domain or deliberately contrasting with an opposing workload.
4. **Deferred Topics Queue (`deferredQueue`)**:
   - Forward questions asked by the learner that are parked with explicit anchor notes, ready to be rehydrated when their target milestone arrives.
5. **Depth & Invariant Audit**:
   - The verified depth achieved (`[concept]`, `[mechanics]`, `[contrast]`, `[pattern]`, `[trap]`) rather than surface familiarity.
   - Diagnosed misconceptions or unresolved foundations that require repair.

---

## 6. Checkpoint Protocol & Idempotency

### Checkpoint Execution Rules:
1. **Stable Semantic Identity**: Every checkpoint receives a permanent ID (e.g. `checkpoint.raft.split-vote`).
2. **Evaluate Reasoning Deeply**:
   - A lucky guess is not mastery. Evaluate whether the learner correctly identified the underlying causal invariant.
   - If correct: Validate the logic, deepen with a boundary constraint, and continue teaching.
   - If incorrect: Isolate the false assumption, provide a counterexample trace, and repair the concept.
3. **Do Not Immediately Re-Quiz**: After evaluating a checkpoint answer, continue with the remaining connected teaching. Do not immediately issue another micro-checkpoint in the same response.
4. **Idempotent Storage**: Submitting the same answer or retrying a turn must never generate duplicate evidence records or alter cursor history unpredictably.
