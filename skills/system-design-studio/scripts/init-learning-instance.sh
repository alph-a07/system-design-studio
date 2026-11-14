#!/usr/bin/env bash
# Initialize a project as a System Design Studio Learning Instance
set -euo pipefail

INSTANCE_DIR=".system-design"
LESSONS_DIR="${INSTANCE_DIR}/lessons"
CURRICULUM_TITLE="${1:-System Design Roadmap — LLD, HLD & Mobile}"
RAW_BASE="https://raw.githubusercontent.com/alph-a07/system-design-studio/main/skills/system-design-studio/resources"

echo "🚀 Initializing System Design Studio Learning Instance..."

mkdir -p "${LESSONS_DIR}"

SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
RESOURCES_DIR="${SCRIPT_DIR}/../resources"

fetch_or_copy() {
  local filename="$1"
  local target_path="$2"

  if [[ -n "${SCRIPT_DIR}" && -f "${RESOURCES_DIR}/${filename}" ]]; then
    cp "${RESOURCES_DIR}/${filename}" "${target_path}"
  else
    echo "   📥 Fetching ${filename} from GitHub..."
    curl -fsSL "${RAW_BASE}/${filename}" -o "${target_path}"
  fi
}

# 1. CURRICULUM.md
fetch_or_copy "CURRICULUM-template.md" "${INSTANCE_DIR}/CURRICULUM.md"

# 2. manifest.json
fetch_or_copy "manifest-template.json" "${INSTANCE_DIR}/manifest.json"

# 3. CURSOR.md
fetch_or_copy "CURSOR-template.md" "${INSTANCE_DIR}/CURSOR.md"

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
