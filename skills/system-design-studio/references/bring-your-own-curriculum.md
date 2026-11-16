# Bring-Your-Own-Curriculum (BYO) & Skill Customization Guide

## Overview

While System Design Studio ships with the authoritative **50-cluster canonical roadmap** (354 topics covering LLD, HLD, distributed systems, infrastructure, and mobile), it is fundamentally **curriculum-agnostic**.

Engineers, tech leads, interview coaches, and engineering teams can bring their own specialized roadmaps, internal architectures, or custom domains with zero code modifications.

---

## 1. Bringing Your Own Curriculum (Markdown Syllabus)

You can write any markdown syllabus in plain text and import it with 1 command. System Design Studio enforces a clean, deterministic 3-level taxonomy: **Tier (Level 1) > Cluster (Level 2) > Topic (Level 3) + Sign-Off Gate**.

### Syllabus Format Standard:
```markdown
# My Custom Engineering Curriculum

# Tier 1: Cloud-Native Resiliency & Service Meshes

## 1. [1.1] Service Mesh Architecture
- [ ] Envoy proxy architecture — thread model, listener filters, and clusters — *Tick off when: you can trace event loop dispatching without notes.*
- [ ] Mutual TLS (mTLS) — SPIFFE/SPIRE workload identities and session costs — *Tick off when: you can derive handshake overhead cold.*
- [ ] Circuit breaking & outlier detection — panic routing thresholds — *Tick off when: you can explain cascading failure mitigation cold.*

## 2. [1.2] Distributed Tracing & Telemetry
- [ ] Trace propagation — W3C TraceContext vs B3 headers — *Tick off when: you can contrast payload overhead and header injection.*

# Tier 2: Database Sharding & Global Coordination

## 3. [2.1] Consensus & Transactions
- [ ] Two-phase commit (2PC) vs Sagas — coordinator failure modes and compensation — *Tick off when: you can trace split-brain boundaries cold.*
- [ ] Raft leader leases — clock drift bounds and monotonic ticks — *Tick off when: you can derive lease safety invariants cold.*
```

### Import Command:
```bash
python3 skills/system-design-studio/scripts/import-curriculum.py \
  --input path/to/my-syllabus.md \
  --instance-dir .system-design \
  --title "Cloud-Native Resiliency & Sharding" \
  --auto-fix
```

The script automatically:
1. Validates the `Tier > Cluster > Topic` hierarchy (with line-numbered diagnostics or `--auto-fix`).
2. Parses clusters and topics into structured JSON objects.
3. Generates `.system-design/manifest.json` schema v3.2.
4. Generates `.system-design/CURRICULUM.md` with interactive checkboxes.
5. Initializes `.system-design/CURSOR.md` targeting Tier 1, Cluster 1, Topic 1 with pristine state.
6. Scaffolds `.system-design/lessons/` for HTML or Markdown artifacts.

---

## 2. Bring Your Own Flagship Domain

By default, the studio invents fresh fictional problems to prevent codebase leakage. However, if a learner or team wants all exercises grounded in their specific engineering vertical:

In `.system-design/CURSOR.md` and `manifest.json`:
```json
{
  "cursor": {
    "flagshipDomain": "High-Frequency Autonomous Drone Dispatch",
    ...
  }
}
```

When configured, the tutor anchors its primary traces and examples around that domain (e.g., flight telemetry, battery limits, packet loss over RF links) while selecting deliberate contrasting workloads (e.g., static financial ledgers) for comparison.

---

## 3. Customizing the HTML Lesson Simulator & Theme

All lesson artifacts are compiled from [`skills/system-design-studio/resources/lesson-template.html`](../resources/lesson-template.html).

You can customize:
1. **Color Themes & Ramps**: Supports Graphite, Ink, or Warm ramps directly via CSS variables.
2. **Interactive Simulators**: Inject custom JavaScript state machines or canvas animations via the `{{EMBEDDED_JAVASCRIPT}}` and `{{SIMULATOR_CANVAS}}` slots.
3. **Custom Invariant Matrices**: Adapt the table headers and comparison columns for specialized domain concerns (e.g., P99.9 Latency vs Hardware Cost vs Energy Budget).

---

## 4. Packaging as an Antigravity Plugin

To distribute this skill as an Antigravity plugin within your organization:
1. Ensure `plugin.json` at repository root points to `skills/system-design-studio`.
2. Install in your agent environment:
   ```bash
   agy plugin add /path/to/system-design-studio
   ```
3. Or distribute via the team's internal marketplace repository.
