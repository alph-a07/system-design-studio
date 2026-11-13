# Project-Based Learning Instance Architecture

## The Core Concept: Project = Learning Instance

In the System Design Studio, **a project workspace IS a learning instance**.

There are no external Notion accounts, cloud databases, or third-party drawing boards. Study notes are reader-personal and kept wherever the learner prefers. The shared engineering context is completely self-contained in the project repository:

```text
my-learning-instance/
├── .git/                          # Standard version control
├── .system-design/                # Studio instance state
│   ├── manifest.json              # Canonical machine-readable state
│   ├── CURSOR.md                  # Living running context (brain of the instance)
│   ├── CURRICULUM.md              # Living syllabus with mastery markers
│   ├── DECISIONS.md               # Accepted ADRs (Architecture Decision Records)
│   └── lessons/                   # Standalone interactive HTML lesson artifacts
│       ├── topic-0.1-tcp-vs-udp.html
│       └── topic-0.2-http-quic.html
├── notes/                         # Optional personal markdown study notes
└── README.md
```

---

## The Two Shared Context Anchors

The entire studio operates on exactly two shared artifacts:

### 1. The Curriculum (`CURRICULUM.md`)
- Authoritative 50-cluster roadmap.
- Every topic states its own tick-off rule.
- Tracks verified completion checkboxes (`- [x]`).

### 2. The Living Cursor (`CURSOR.md`)
- The operational cognitive brain of the instance.
- Tracks active focus, target depth, cluster reality checks, causal lineage (backward anchor and forward hook), examples registry (`examplesTaken`), deferred queue (`deferredQueue`), and the immediate next teaching action.
- Ensures seamless continuity across sessions, models, and agents.

---

## Portable & Zero-Dependency

Because `.system-design/` is local plain-text JSON, Markdown, and HTML:
- Any agent (Antigravity, Claude Code, Cursor, Codex) reads the state in 1 local tool call.
- The entire learning journey can be committed to GitHub/GitLab with standard `git commit`.
- Fully functional offline with zero cloud tokens or external connectors.
