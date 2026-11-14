#!/bin/sh
# System Design Studio — Learning Instance Initializer
# Scaffolds .system-design/ state directory in current project workspace.
# Fully POSIX sh compliant for macOS, Linux, BSD, and Windows (Git Bash/WSL).
set -e
(set -o pipefail) 2>/dev/null && set -o pipefail || true

INSTANCE_DIR=".system-design"
LESSONS_DIR="${INSTANCE_DIR}/lessons"
CURRICULUM_TITLE="${1:-System Design Roadmap — LLD, HLD & Mobile}"
RAW_BASE="https://raw.githubusercontent.com/alph-a07/system-design-studio/main/skills/system-design-studio/resources"

echo "🚀 Initializing System Design Studio Learning Instance..."

mkdir -p "${LESSONS_DIR}"

# Locate resources directory relative to script or fallback to remote download
SCRIPT_PATH="${0:-}"
SCRIPT_DIR=""
if [ -n "$SCRIPT_PATH" ] && [ -f "$SCRIPT_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" 2>/dev/null && pwd || echo "")"
fi
RESOURCES_DIR="${SCRIPT_DIR}/../resources"

fetch_or_copy() {
  filename="$1"
  target_path="$2"

  if [ -n "${SCRIPT_DIR}" ] && [ -f "${RESOURCES_DIR}/${filename}" ]; then
    cp "${RESOURCES_DIR}/${filename}" "${target_path}"
  elif command -v curl >/dev/null 2>&1; then
    echo "   📥 Fetching ${filename} from GitHub..."
    curl -fsSL "${RAW_BASE}/${filename}" -o "${target_path}"
  elif command -v wget >/dev/null 2>&1; then
    echo "   📥 Fetching ${filename} from GitHub (wget)..."
    wget -qO "${target_path}" "${RAW_BASE}/${filename}"
  else
    echo "❌ Error: curl or wget is required to fetch ${filename}" >&2
    exit 1
  fi
}

# 1. CURRICULUM.md
fetch_or_copy "CURRICULUM-template.md" "${INSTANCE_DIR}/CURRICULUM.md"

# 2. manifest.json
fetch_or_copy "manifest-template.json" "${INSTANCE_DIR}/manifest.json"

# 3. CURSOR.md
fetch_or_copy "CURSOR-template.md" "${INSTANCE_DIR}/CURSOR.md"

# 4. settings.json (merge if already present to preserve user preferences)
if [ -f "${INSTANCE_DIR}/settings.json" ]; then
  TEMP_TPL="$(mktemp 2>/dev/null || echo "${INSTANCE_DIR}/.settings.tpl.json")"
  fetch_or_copy "settings-template.json" "${TEMP_TPL}"
  if [ -n "${SCRIPT_DIR}" ] && [ -f "${SCRIPT_DIR}/merge-settings.py" ]; then
    python3 "${SCRIPT_DIR}/merge-settings.py" --current "${INSTANCE_DIR}/settings.json" --template "${TEMP_TPL}" --output "${INSTANCE_DIR}/settings.json"
  fi
  rm -f "${TEMP_TPL}" 2>/dev/null || true
else
  fetch_or_copy "settings-template.json" "${INSTANCE_DIR}/settings.json"
fi

# 5. Generate initial DECISIONS.md
cat <<EOF > "${INSTANCE_DIR}/DECISIONS.md"
# Architecture Decision Records (ADRs)

*No decisions accepted yet. Decisions will be recorded as architectural trade-offs are evaluated and defended in workshops.*
EOF

chmod -R u+rwX,go+rX "${INSTANCE_DIR}" 2>/dev/null || true

echo "✅ Learning instance initialized at ${INSTANCE_DIR}/"
echo "   - Manifest:   ${INSTANCE_DIR}/manifest.json"
echo "   - Cursor:     ${INSTANCE_DIR}/CURSOR.md"
echo "   - Curriculum: ${INSTANCE_DIR}/CURRICULUM.md"
echo "   - Settings:   ${INSTANCE_DIR}/settings.json"
echo "   - Decisions:  ${INSTANCE_DIR}/DECISIONS.md"
echo "   - Lessons:    ${LESSONS_DIR}/"
