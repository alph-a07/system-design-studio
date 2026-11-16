#!/bin/sh
# System Design Studio — Universal Skill & Instance Updater
# Updates agent skills to latest release while strictly preserving:
# 1. User learning progress (manifest.json, CURSOR.md, CURRICULUM.md, DECISIONS.md)
# 2. Existing interactive lesson artifacts (lessons/*.html)
# 3. User custom settings & chosen visual artifactStyle (via merge-settings.py)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.sh | bash
#   ./update.sh [--instance-dir <path>]

set -e
(set -o pipefail) 2>/dev/null && set -o pipefail || true

SKILL_NAME="system-design-studio"
REPO_URL="https://github.com/alph-a07/system-design-studio.git"
RAW_BASE="https://raw.githubusercontent.com/alph-a07/system-design-studio/main"
ARCHIVE_URL="https://github.com/alph-a07/system-design-studio/archive/refs/heads/main.tar.gz"

echo "=========================================================="
echo "    System Design Studio — Universal Update Engine        "
echo "=========================================================="

HOME_DIR="${HOME:-}"
if [ -z "$HOME_DIR" ] && [ -n "${USERPROFILE:-}" ]; then
  HOME_DIR="$USERPROFILE"
fi

INSTANCE_DIR=".system-design"
for arg in "$@"; do
  case "$arg" in
    --instance-dir=*)
      INSTANCE_DIR="${arg#*=}"
      ;;
  esac
done

# 1. Locate local source or fetch fresh archive
TEMP_DIR=""
cleanup() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT INT TERM

SCRIPT_PATH="${0:-}"
SCRIPT_DIR=""
if [ -n "$SCRIPT_PATH" ] && [ -f "$SCRIPT_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" 2>/dev/null && pwd || echo "")"
fi

SOURCE_SKILL=""
# If inside developer repo
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/plugin.json" ] && [ -d "$SCRIPT_DIR/skills/$SKILL_NAME" ]; then
  SOURCE_SKILL="$(cd "$SCRIPT_DIR/skills/$SKILL_NAME" && pwd)"
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../../plugin.json" ] && [ -d "$SCRIPT_DIR/../../skills/$SKILL_NAME" ]; then
  SOURCE_SKILL="$(cd "$SCRIPT_DIR/../../skills/$SKILL_NAME" && pwd)"
fi

if [ -z "$SOURCE_SKILL" ]; then
  TEMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'sds-update')"
  echo "📥 Fetching latest skill release from GitHub..."
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$ARCHIVE_URL" -o "$TEMP_DIR/sds.tar.gz"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TEMP_DIR/sds.tar.gz" "$ARCHIVE_URL"
  else
    echo "❌ Error: curl or wget is required to download updates." >&2
    exit 1
  fi

  tar -xzf "$TEMP_DIR/sds.tar.gz" -C "$TEMP_DIR"
  SOURCE_SKILL="$TEMP_DIR/system-design-studio-main/skills/$SKILL_NAME"
fi

if [ ! -f "$SOURCE_SKILL/SKILL.md" ]; then
  echo "❌ Error: Update payload could not be verified (SKILL.md missing)." >&2
  exit 1
fi

# 2. Update Installed Skills Across AI Agents
echo "📦 Updating agent skills..."
AGENT_TARGETS="
$HOME_DIR/.gemini/antigravity/skills
$HOME_DIR/.gemini/config/skills
$HOME_DIR/.agents/skills
$HOME_DIR/.claude/skills
$HOME_DIR/.cursor/skills
$HOME_DIR/.codex/skills
$HOME_DIR/.system-design-studio/skills
"

UPDATED_COUNT=0
for target_parent in $AGENT_TARGETS; do
  if [ -d "$target_parent" ]; then
    target_dir="${target_parent}/${SKILL_NAME}"
    mkdir -p "$target_parent"
    rm -rf "$target_dir"
    cp -R "$SOURCE_SKILL" "$target_dir"
    chmod -R u+rwX,go+rX "$target_dir" 2>/dev/null || true
    chmod +x "$target_dir/scripts/"*.sh "$target_dir/scripts/"*.py 2>/dev/null || true
    echo "   ✅ Updated at ${target_dir}"
    UPDATED_COUNT=$((UPDATED_COUNT + 1))
  fi
done

# 3. Settings Merge & Local Instance Protection
if [ -d "$INSTANCE_DIR" ]; then
  echo ""
  echo "🔧 Local project instance found at '${INSTANCE_DIR}/':"
  
  SETTINGS_FILE="${INSTANCE_DIR}/settings.json"
  TEMPLATE_SETTINGS="${SOURCE_SKILL}/resources/settings-template.json"
  MERGE_SCRIPT="${SOURCE_SKILL}/scripts/merge-settings.py"

  if [ -f "$SETTINGS_FILE" ] && [ -f "$TEMPLATE_SETTINGS" ] && [ -f "$MERGE_SCRIPT" ]; then
    echo "   🔄 Merging settings.json to preserve user preferences..."
    python3 "$MERGE_SCRIPT" --current "$SETTINGS_FILE" --template "$TEMPLATE_SETTINGS" --output "$SETTINGS_FILE"
  elif [ ! -f "$SETTINGS_FILE" ] && [ -f "$TEMPLATE_SETTINGS" ]; then
    echo "   ✨ Adding settings.json from template..."
    cp "$TEMPLATE_SETTINGS" "$SETTINGS_FILE"
  fi

  # Run verification
  VERIFY_SCRIPT="${SOURCE_SKILL}/scripts/verify-instance.py"
  if [ -f "$VERIFY_SCRIPT" ]; then
    echo ""
    python3 "$VERIFY_SCRIPT" "$INSTANCE_DIR"
  fi
fi

echo ""
echo "=========================================================="
echo "🎉 System Design Studio updated across ${UPDATED_COUNT} agent location(s)!"
echo "   All learning progress and custom user settings were preserved."
echo "=========================================================="
