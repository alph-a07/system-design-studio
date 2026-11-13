#!/usr/bin/env bash
# Initialize a project as a System Design Studio Learning Instance
set -euo pipefail

INSTANCE_DIR=".system-design"
LESSONS_DIR="${INSTANCE_DIR}/lessons"
CURRICULUM_TITLE="${1:-System Design Mastery Roadmap — LLD, HLD & Mobile}"

echo "🚀 Initializing System Design Studio Learning Instance..."

mkdir -p "${LESSONS_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCES_DIR="${SCRIPT_DIR}/../resources"

# 1. Copy CURRICULUM.md
if [[ -f "${RESOURCES_DIR}/CURRICULUM-template.md" ]]; then
  cp "${RESOURCES_DIR}/CURRICULUM-template.md" "${INSTANCE_DIR}/CURRICULUM.md"
fi

# 2. Copy or generate manifest.json
if [[ -f "${RESOURCES_DIR}/manifest-template.json" ]]; then
  cp "${RESOURCES_DIR}/manifest-template.json" "${INSTANCE_DIR}/manifest.json"
fi

# 3. Copy or generate CURSOR.md
if [[ -f "${RESOURCES_DIR}/CURSOR-template.md" ]]; then
  cp "${RESOURCES_DIR}/CURSOR-template.md" "${INSTANCE_DIR}/CURSOR.md"
fi

# 4. Generate initial DECISIONS.md
cat <<EOF > "${INSTANCE_DIR}/DECISIONS.md"
# Architecture Decision Records (ADRs)

*No decisions accepted yet. Decisions will be recorded as architectural trade-offs are evaluated and defended in workshops.*
EOF

chmod +x "${INSTANCE_DIR}/manifest.json" 2>/dev/null || true

echo "✅ Learning instance initialized at ${INSTANCE_DIR}/"
echo "   - Manifest:   ${INSTANCE_DIR}/manifest.json"
echo "   - Cursor:     ${INSTANCE_DIR}/CURSOR.md"
echo "   - Curriculum: ${INSTANCE_DIR}/CURRICULUM.md"
echo "   - Decisions:  ${INSTANCE_DIR}/DECISIONS.md"
echo "   - Lessons:    ${LESSONS_DIR}/"
