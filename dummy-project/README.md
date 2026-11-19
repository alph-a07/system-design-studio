# System Design Studio — Mock Testing & Validation Project

This is a pre-configured, self-contained **dummy project** for local testing, validations, and interactive demonstrations of the System Design Studio dashboard and learning engine.

## 🎯 Mock Data Included

- **Curriculum Track**: `interview-sprint` (15 High-Yield Clusters, 114 Topics).
- **Progress State**:
  - `topic.0.1.tcp-vs-udp`: Completed (`status: "completed"`).
  - `topic.0.1.http-1-1-vs-http-2-vs-http-3`: Completed (`status: "completed"`).
  - `topic.0.1.tls-handshake-cost-and-session-resu`: Active Focus (`status: "in_progress"`).
  - Remaining topics: Unseen / Queued.
- **Rendered Lessons & Interactive Simulators**:
  - `0-1-tcp-vs-udp.html`: Interactive kernel socket buffer simulation with tactile packet drop controls.
  - `0-1-http-1-1-vs-http-2-vs-http-3.html`: Interactive HTTP/2 multiplexing vs QUIC independent stream visualizer.
- **Sidecar Highlight Annotations**:
  - Color-coded reader annotations (`.highlights.json`) on core invariants and sizing formulas.
- **Architecture Decision Records (ADRs)**:
  - `DECISIONS.md`: Logged ADR-001 and ADR-002 with trade-off defense and failure boundaries.
- **Revision Mode Flashcards**:
  - `revisions.json`: Auto-compiled revision cards for quick spaced retrieval.
- **Synthesized Study Notes**:
  - `notes/tier-0/cluster-0-1-.../`: Discussion-synthesized active learning study notes.

---

## 🚀 Launching the Dashboard

You can launch the dashboard for this dummy project using any of the following methods:

### Method 1: SDS CLI (Recommended)
```bash
./bin/sds dummy
```

### Method 2: Dedicated Launch Script
```bash
./launch-dummy-dashboard.sh
```

### Method 3: Standard SDS Dashboard Command
```bash
./bin/sds dashboard --instance-dir dummy-project/.system-design
```
*(If running while `cd`'d into `dummy-project`, running `sds dashboard` automatically detects this instance).*

---

## 🧪 Validating Instance Health
```bash
python3 skills/system-design-studio/scripts/verify-instance.py dummy-project/.system-design
```
