# System Design Studio Skill Package

`skills/system-design-studio/` is an agentic skill adhering to the open [Agent Skills](https://agentskills.io) standard. It equips AI coding agents to teach distributed systems architecture through first-principles causal reasoning, Git-backed living state, and interactive visual simulators.

---

## Directory Architecture

```text
skills/system-design-studio/
├── SKILL.md                 # Agent instruction contract (read on skill invocation)
├── README.md                # This skill package reference manual
├── scripts/                 # Standalone zero-dependency Python & Bash tooling
│   ├── init-learning-instance.sh   # Scaffolds fresh .system-design/ workspace
│   ├── advance-cursor.py           # Idempotently advances active focus and ticks curriculum
│   ├── sync-status.py              # Reports live cognitive status and causal anchors
│   ├── verify-instance.py          # Verifies directory schema and lineage integrity
│   ├── render-lesson.py            # Compiles interactive HTML teaching artifacts
│   ├── manage-projects.py          # Multi-project registry, active switching & safe deletion
│   ├── merge-settings.py           # Lossless settings migration across version upgrades
│   └── import-curriculum.py        # Imports custom Markdown syllabi into manifest
├── references/              # Architectural specs and pedagogical references
│   ├── project-learning-instance.md   # Filesystem contract & zero-cloud invariants
│   ├── running-context-engine.md      # CURSOR.md state structure & lineage rules
│   ├── first-principles-pedagogy.md   # Hardware physics & causal teaching method
│   ├── connected-closure-method.md    # Multi-session continuity & backward hooks
│   ├── interactive-html-artifacts.md  # HTML lesson rendering & simulator spec
│   ├── context-manifest-spec.md       # manifest.json v2.0 schema specification
│   ├── interaction-contract.md        # Tutor response template & turn lifecycle
│   ├── fresh-fictional-problems.md    # Domain rotation & examplesTaken registry
│   └── bring-your-own-curriculum.md   # Markdown syllabus importer specification
└── resources/               # Scaffolding templates
    ├── manifest-template.json         # Canonical 50-cluster, 354-topic manifest
    ├── CURSOR-template.md             # Baseline living state cursor
    ├── CURRICULUM-template.md         # 50-cluster Markdown checklist
    ├── lesson-template.html           # Standalone simulator & artifact shell
    └── custom-curriculum-example.md   # Example markdown syllabus for testing BYO
```

---

## CLI Utilities Reference

All scripts in `scripts/` require only standard Python 3.10+ (no third-party pip dependencies) and standard Bash:

### 1. Initialize Instance
Scaffolds a `.system-design/` directory in the current working directory:
```bash
bash skills/system-design-studio/scripts/init-learning-instance.sh "My Systems Architecture Path"
```

### 2. Verify Instance Health
Audits `.system-design/` for schema compliance, unlinked topics, and missing cursor fields:
```bash
python3 skills/system-design-studio/scripts/verify-instance.py .system-design
```

### 3. Check Live Status & Telemetry
Reports active topic, progress percentage, examples log, and deferred questions:
```bash
python3 skills/system-design-studio/scripts/sync-status.py .system-design
```

### 4. Advance Active Topic
Transitions active topic from `in-progress` to `mastered`, logs real-world examples, and anchors causal physics:
```bash
python3 skills/system-design-studio/scripts/advance-cursor.py \
  --complete-topic topic.0.1.tcp-vs-udp \
  --evidence "Learner traced socket buffer head-of-line blocking under packet loss" \
  --log-example-domain "Financial Ledger" \
  --log-example-scenario "Idempotency retry on TCP timeout" \
  --next-topic-id topic.0.1.http-1-1-vs-http-2-vs-http-3 \
  --next-action "Establish topic foundation for HTTP multiplexing"
```

### 5. Multi-Project Registry & Safe Deletion
Lists registered instances, switches active learning context, inspects notes, or safely removes projects:
```bash
# List all registered instances and progress
python3 skills/system-design-studio/scripts/manage-projects.py list

# Switch active project context
python3 skills/system-design-studio/scripts/manage-projects.py switch <project-id>

# List generated study notes for project
python3 skills/system-design-studio/scripts/manage-projects.py notes [project-id]

# Safely delete project instance (strictly preserves user files & notes by default)
python3 skills/system-design-studio/scripts/manage-projects.py delete <project-id> [--dry-run] [-f]
```

### 6. Import Custom Syllabus (BYO)
Transforms any external Markdown curriculum into an indexed `.system-design/` instance:
```bash
python3 skills/system-design-studio/scripts/import-curriculum.py \
  --input custom-syllabus.md \
  --instance-dir .system-design \
  --title "High-Frequency Trading Architecture"
```

### 7. Lossless Settings Migration
Safely merges updated settings schema with user preferences without erasing customizations:
```bash
python3 skills/system-design-studio/scripts/merge-settings.py \
  --instance-dir .system-design \
  --defaults skills/system-design-studio/resources/settings-defaults.json
```

---

## Agent Integration

When installed in an agent environment (Google Antigravity, Claude Code, Cursor, Codex, Gemini CLI):
1. The agent reads `SKILL.md` to learn the teaching contract.
2. On every user turn within a project containing `.system-design/`, the agent reads `.system-design/CURSOR.md` first.
3. The agent anchors discussions in physical hardware limits (CPU, DRAM, SSD, WAN latency).
4. Substantive lessons are rendered as standalone interactive HTML artifacts saved to `.system-design/lessons/`.
