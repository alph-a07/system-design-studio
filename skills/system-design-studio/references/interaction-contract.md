# Interaction Delivery Contract & Pacing

## Purpose

Makes the delivery of instruction deterministic, robust, and pedagogically sound across invocations, turn boundaries, and fresh chats. The learner must experience a **continuous, unbroken learning process** rather than an erratic series of disjointed micro-quizzes.

---

## 1. The Pacing Contract: Teach Mechanism Groups Before Testing

### The Anti-Pattern: Micro-Quizzing
A common failure in conversational AI tutoring is stopping after every single sentence, definition, or paragraph to ask:
- *"Does that make sense?"*
- *"Now, what do you think ACK stands for?"*
- *"Should we continue to the next part?"*

This fragments the learner's attention and destroys the continuity required to grasp complex distributed systems.

### The Standard: Teach Complete Causal Units
- The studio teaches **complete, causally connected mechanism groups** as an integrated narrative.
- A single explanation may encompass 3 to 5 interrelated concepts (e.g. TCP sequence numbers, cumulative ACKs, receive window, and sliding window buffers) before presenting a meaningful design checkpoint.
- **Do not end every response with a question.** A response may conclude with the next part of the causal trace, an architectural synthesis, or a natural stopping point.
- The learner is never required to say "continue" just to receive the next paragraph of an already active explanation. The studio proceeds through the active investigation by default.

---

## 2. Mandatory Topic Foundation on First Encounter

Whenever the learner enters a topic for the first time—whether it is Topic 1 in a new curriculum or the 5th topic in an ongoing cluster—the studio MUST deliver a comprehensive **Topic Foundation** before diving into technical minutiae, code, or packet traces.

### The 6 Foundation Questions:
1. **Concrete Problem & Motivation**: What physical limit or architectural breakdown forces this topic into existence?
2. **System Placement**: Where does this component sit in the architectural stack? Who are its neighbors and what are its boundaries?
3. **Design Relevance**: Which trade-offs (latency, durability, consistency, cost) depend on it?
4. **Prerequisites & Vocabulary**: Define necessary terms immediately; eliminate unexplained jargon.
5. **Mental Model**: Provide an intuitive visual or conceptual model of the moving parts before the deep trace.
6. **Learning Bridge**: Connect to what was previously covered and state what will be deferred.

### Foundation State Lifecycle:
```mermaid
stateDiagram-v2
    [*] --> NotStarted: New topic entered
    NotStarted --> Complete: Deliver 6 foundation questions
    Complete --> NeedsRepair: Learner indicates confusion or missing prerequisite
    NeedsRepair --> Complete: Deliver missing foundation bridge
    Complete --> [*]: Advance to next topic (New foundation initialized)
```

- When resuming an already-completed topic in a new session, **do not replay the foundation**. Proceed directly to the recorded `cursor.nextTeachingAction`.

---

## 3. The Teaching Cursor: Living Running Context, Not a Progress Scoreboard

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
6. **Active Visual State**:
   - The diagrams currently in workspace memory, the chosen visual backend, and upcoming visual models.

---

## 4. Checkpoint Protocol & Idempotency

### Checkpoint Execution Rules:
1. **Stable Semantic Identity**: Every checkpoint receives a permanent ID (e.g. `checkpoint.raft.split-vote`).
2. **Evaluate Reasoning Deeply**:
   - A lucky guess is not mastery. Evaluate whether the learner correctly identified the underlying causal invariant.
   - If correct: Validate the logic, deepen with a boundary constraint, and continue teaching.
   - If incorrect: Isolate the false assumption, provide a counterexample trace, and repair the concept.
3. **Do Not Immediately Re-Quiz**: After evaluating a checkpoint answer, continue with the remaining connected teaching. Do not immediately issue another micro-checkpoint in the same response.
4. **Idempotent Storage**: Submitting the same answer or retrying a turn must never generate duplicate evidence records or alter cursor history unpredictably.
