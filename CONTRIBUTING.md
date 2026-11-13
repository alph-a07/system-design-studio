# Contributing to System Design Studio

Thank you for your interest in contributing to **System Design Studio**! We welcome contributions that expand our canonical curriculum, refine interactive HTML simulators, improve multi-agent portability, or add new BYO capabilities.

---

## 🏛️ Guiding Invariants

Before writing code or opening a PR, please note the non-negotiable architectural invariants:

1. **Pure Local State (Zero Cloud Lock-in)**:
   - State lives strictly in `.system-design/` in the user's project.
   - Never introduce dependencies on Notion, cloud databases, or third-party drawing boards.
   - Learner notes belong 100% to the reader.
2. **Cursor & Curriculum as Sole Shared Context**:
   - `CURRICULUM.md` is the master syllabus with verified ticks.
   - `CURSOR.md` is the operational cognitive brain tracking active focus, examples, deferred questions, and causal lineage.
3. **Interactive Visual HTML Pedagogy**:
   - Lessons must be delivered as interactive HTML artifacts with embedded step-through simulators, workload comparisons, and reality checks.
   - Avoid flat walls of bullet points.
4. **Universal Agent Portability**:
   - The skill must work across Google Antigravity, Claude Code, Cursor, Codex, and Gemini CLI.
   - CLI scripts must use Python standard library only (no `pip install` requirements).

---

## 🛠️ Local Development & Testing

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alph-a07/system-design-studio.git
   cd system-design-studio
   ```

2. **Verify the active instance and scripts**:
   ```bash
   chmod +x skills/system-design-studio/scripts/*
   python3 skills/system-design-studio/scripts/verify-instance.py
   ```

3. **Test fresh scaffolding**:
   ```bash
   mkdir -p /tmp/test-instance && cd /tmp/test-instance
   /path/to/skills/system-design-studio/scripts/init-learning-instance.sh "Test Scaffolding"
   python3 /path/to/skills/system-design-studio/scripts/verify-instance.py .system-design
   ```

4. **Test BYO curriculum import**:
   ```bash
   python3 /path/to/skills/system-design-studio/scripts/import-curriculum.py \
     --input /path/to/skills/system-design-studio/resources/custom-curriculum-example.md \
     --instance-dir /tmp/test-instance/.system-design
   python3 /path/to/skills/system-design-studio/scripts/verify-instance.py /tmp/test-instance/.system-design
   ```

---

## 📝 Submitting a Pull Request

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-simulator
   ```
2. Verify all checks pass locally:
   ```bash
   python3 skills/system-design-studio/scripts/verify-instance.py
   ```
3. Push to your fork and submit a Pull Request.
4. Follow the provided PR template.
