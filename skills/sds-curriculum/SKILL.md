---
name: sds-curriculum
description: Inspect, customize, or reorder curriculum tracks or import BYO syllabus in System Design Studio.
compatibility: Universal (Antigravity, Claude Code, Cursor, Codex)
metadata:
  version: 3.2.0
---

# /sds-curriculum

Inspect active syllabus, restructure cluster priorities, prune topics, or import a custom Markdown syllabus adhering to the 3-level taxonomy (`Tier > Cluster > Topic`).

## Instructions

1. **Inspect active syllabus**:
   - Read `.system-design/CURRICULUM.md` and `.system-design/manifest.json`.
   - List active tier, current cluster, and topic distribution.
2. **Handle customization or BYO import**:
   - If importing a custom Markdown syllabus:
     ```bash
     python3 ~/.system-design-studio/skills/system-design-studio/scripts/import-curriculum.py \
       --input <syllabus-file.md> \
       --instance-dir .system-design
     ```
   - Validate 3-level hierarchy: `# Tier <N>`, `## <Order>. [<Code>] <Cluster>`, `- [ ] <Topic> — *Tick off when:*`.
