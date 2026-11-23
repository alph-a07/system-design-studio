# Project-Based Learning Instance Architecture

## The Core Concept: Project = Learning Instance

In the System Design Studio, **a project workspace IS a learning instance**.

There are no external Notion accounts, cloud databases, or third-party drawing boards. Study notes are reader-personal and kept wherever the learner prefers. The shared engineering context is completely self-contained in the project repository:

```text
my-learning-instance/
├── .git/                          # Standard version control
├── .system-design/                # Studio instance state
│   ├── manifest.json              # Canonical machine-readable state
│   ├── settings.json              # Studio preferences & directory paths
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

## Configurable Directory Paths & Notes (`settings.json`)

By default, studio files reside under `.system-design/` and notes in `notes/`. If your project or workspace requires custom storage locations (e.g. keeping notes in an external Obsidian vault or lessons in `docs/lessons`), configure paths in `.system-design/settings.json`:

```json
{
  "$schemaVersion": "3.2",
  "projectId": "my-project",
  "track": "interview-sprint",
  "artifactStyle": "slate-clean",
  "outputType": "html",
  "autoGenerateNotes": true,
  "notesStructure": "per-topic",
  "paths": {
    "instanceDir": ".system-design",
    "cursorDir": ".system-design",
    "lessonsDir": ".system-design/lessons",
    "notesDir": "notes"
  }
}
```

- **`paths.notesDir`**: Custom directory where discussion-synthesized markdown study notes are stored.
- **`notesStructure`**: Compilation mode: `per-topic` (default), `per-cluster`, `per-tier`, or `single-file`.
- **`outputType`**: `html` (interactive HTML lesson artifacts with live simulators).
- **`paths.cursorDir`**: Directory where `CURSOR.md` is saved and read.
- **`paths.lessonsDir`**: Directory where generated lesson artifacts are saved.
- **`paths.instanceDir`**: Root instance state directory for `manifest.json`, `settings.json`, and updates.

All studio scripts (`render-lesson.py`, `advance-cursor.py`, `verify-instance.py`, `sync-status.py`, `update.sh`) automatically detect and respect these configured directory preferences.

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
