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
while [ $# -gt 0 ]; do
  case "$1" in
    --instance-dir=*)
      INSTANCE_DIR="${1#*=}"
      ;;
    --instance-dir)
      shift; INSTANCE_DIR="$1"
      ;;
  esac
  shift
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

SOURCE_SKILLS_DIR=""
SOURCE_AGENTS_DIR=""
# If inside developer repo
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/plugin.json" ] && [ -d "$SCRIPT_DIR/skills/$SKILL_NAME" ]; then
  SOURCE_SKILLS_DIR="$(cd "$SCRIPT_DIR/skills" && pwd)"
  if [ -d "$SCRIPT_DIR/agents" ]; then
    SOURCE_AGENTS_DIR="$(cd "$SCRIPT_DIR/agents" && pwd)"
  fi
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../../plugin.json" ] && [ -d "$SCRIPT_DIR/../../skills/$SKILL_NAME" ]; then
  SOURCE_SKILLS_DIR="$(cd "$SCRIPT_DIR/../../skills" && pwd)"
  if [ -d "$SCRIPT_DIR/../../agents" ]; then
    SOURCE_AGENTS_DIR="$(cd "$SCRIPT_DIR/../../agents" && pwd)"
  fi
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../../../plugin.json" ] && [ -d "$SCRIPT_DIR/../../$SKILL_NAME" ]; then
  SOURCE_SKILLS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
  if [ -d "$SCRIPT_DIR/../../../agents" ]; then
    SOURCE_AGENTS_DIR="$(cd "$SCRIPT_DIR/../../../agents" && pwd)"
  fi
fi

if [ -z "$SOURCE_SKILLS_DIR" ]; then
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
  SOURCE_SKILLS_DIR="$TEMP_DIR/system-design-studio-main/skills"
  if [ -d "$TEMP_DIR/system-design-studio-main/agents" ]; then
    SOURCE_AGENTS_DIR="$TEMP_DIR/system-design-studio-main/agents"
  fi
fi

SOURCE_SKILL="${SOURCE_SKILLS_DIR}/${SKILL_NAME}"

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
    cp -R "$SOURCE_SKILLS_DIR/$SKILL_NAME" "$target_dir"
    chmod -R u+rwX,go+rX "$target_dir" 2>/dev/null || true
    chmod +x "$target_dir/scripts/"*.sh "$target_dir/scripts/"*.py 2>/dev/null || true

    # Also update all companion sds-* command skills
    companion_count=0
    for cmd_dir in "$SOURCE_SKILLS_DIR"/sds-*; do
      if [ -d "$cmd_dir" ]; then
        cmd_name="$(basename "$cmd_dir")"
        rm -rf "${target_parent}/${cmd_name}"
        cp -R "$cmd_dir" "${target_parent}/${cmd_name}"
        chmod -R u+rwX,go+rX "${target_parent}/${cmd_name}" 2>/dev/null || true
        companion_count=$((companion_count + 1))
      fi
    done

    echo "   ✅ Updated at ${target_dir} (+ ${companion_count} in-chat commands)"
    UPDATED_COUNT=$((UPDATED_COUNT + 1))
  fi
done

# Update specialized subagents across agent locations
AGENT_SUBDIRS="
$HOME_DIR/.gemini/antigravity/agents
$HOME_DIR/.gemini/config/agents
$HOME_DIR/.agents/agents
$HOME_DIR/.claude/agents
$HOME_DIR/.cursor/agents
$HOME_DIR/.codex/agents
$HOME_DIR/.system-design-studio/agents
"

if [ -n "$SOURCE_AGENTS_DIR" ] && [ -d "$SOURCE_AGENTS_DIR" ]; then
  echo "🤖 Updating specialized subagents..."
  for target_agent_parent in $AGENT_SUBDIRS; do
    if [ -d "$target_agent_parent" ]; then
      cp -R "${SOURCE_AGENTS_DIR}"/* "$target_agent_parent/" 2>/dev/null || true
      chmod -R u+rwX,go+rX "$target_agent_parent" 2>/dev/null || true
      echo "   ✅ Updated subagents at ${target_agent_parent}"
    fi
  done
fi

# Also update Claude Code and Codex commands if present
if [ -d "$HOME_DIR/.claude/commands" ]; then
  for cmd_dir in "$SOURCE_SKILLS_DIR"/sds-*; do
    if [ -d "$cmd_dir" ] && [ -f "$cmd_dir/SKILL.md" ]; then
      cmd_name="$(basename "$cmd_dir")"
      cp "$cmd_dir/SKILL.md" "$HOME_DIR/.claude/commands/${cmd_name}.md" 2>/dev/null || true
    fi
  done
fi

if [ -d "$HOME_DIR/.codex/prompts" ]; then
  for cmd_dir in "$SOURCE_SKILLS_DIR"/sds-*; do
    if [ -d "$cmd_dir" ] && [ -f "$cmd_dir/SKILL.md" ]; then
      cmd_name="$(basename "$cmd_dir")"
      cp "$cmd_dir/SKILL.md" "$HOME_DIR/.codex/prompts/${cmd_name}.md" 2>/dev/null || true
    fi
  done
fi

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
