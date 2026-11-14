#!/usr/bin/env bash
# System Design Studio — Universal Agent Skill Installer
# Installs system-design-studio into selected coding agents on your machine.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash -s -- --all
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash -s -- --antigravity --claude --cursor --codex

set -euo pipefail

REPO_URL="https://github.com/alph-a07/system-design-studio.git"
RAW_BASE="https://raw.githubusercontent.com/alph-a07/system-design-studio/main"
SKILL_NAME="system-design-studio"

echo "=========================================================="
echo "  System Design Studio — Universal Agent Skill Installer  "
echo "=========================================================="

# Parse flags or detect installed agents
INSTALL_ALL=false
INSTALL_ANTIGRAVITY=false
INSTALL_CLAUDE=false
INSTALL_CURSOR=false
INSTALL_CODEX=false

if [[ $# -gt 0 ]]; then
  for arg in "$@"; do
    case "$arg" in
      --all|-a)
        INSTALL_ALL=true
        ;;
      --antigravity|--gemini)
        INSTALL_ANTIGRAVITY=true
        ;;
      --claude)
        INSTALL_CLAUDE=true
        ;;
      --cursor)
        INSTALL_CURSOR=true
        ;;
      --codex)
        INSTALL_CODEX=true
        ;;
      --help|-h)
        echo "Usage: install.sh [--all] [--antigravity] [--claude] [--cursor] [--codex]"
        exit 0
        ;;
    esac
  done
else
  # Auto-detect or default to all agents found on machine
  if [[ -d "$HOME/.gemini" || -d "$HOME/.agents" ]]; then
    INSTALL_ANTIGRAVITY=true
  fi
  if [[ -d "$HOME/.claude" ]]; then
    INSTALL_CLAUDE=true
  fi
  if [[ -d "$HOME/.cursor" || -d "$HOME/Library/Application Support/Cursor" || -d "$HOME/.cursorrules" ]]; then
    INSTALL_CURSOR=true
  fi
  if [[ -d "$HOME/.codex" ]]; then
    INSTALL_CODEX=true
  fi

  # If none explicitly detected, install for all universal paths
  if ! $INSTALL_ANTIGRAVITY && ! $INSTALL_CLAUDE && ! $INSTALL_CURSOR && ! $INSTALL_CODEX; then
    INSTALL_ALL=true
  fi
fi

if $INSTALL_ALL; then
  INSTALL_ANTIGRAVITY=true
  INSTALL_CLAUDE=true
  INSTALL_CURSOR=true
  INSTALL_CODEX=true
fi

# Stage temporary clone or use local repository if running locally
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
TEMP_DIR=""

if [[ -n "$SCRIPT_DIR" && -d "$SCRIPT_DIR/skills/$SKILL_NAME" ]]; then
  echo "📂 Using local skill package from $SCRIPT_DIR..."
  SOURCE_SKILL="$SCRIPT_DIR/skills/$SKILL_NAME"
else
  TEMP_DIR=$(mktemp -d)
  cleanup() {
    [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
  }
  trap cleanup EXIT

  echo "📥 Fetching canonical skill package from GitHub..."
  git clone --depth 1 --quiet "$REPO_URL" "$TEMP_DIR/repo"
  SOURCE_SKILL="$TEMP_DIR/repo/skills/$SKILL_NAME"
fi

install_to_path() {
  local target_dir="$1"
  local agent_name="$2"
  echo "📦 Installing for ${agent_name}..."
  mkdir -p "$target_dir"
  rm -rf "${target_dir}/${SKILL_NAME}"
  cp -R "$SOURCE_SKILL" "${target_dir}/${SKILL_NAME}"
  echo "   ✅ Placed at ${target_dir}/${SKILL_NAME}"
}

# 1. Google Antigravity
if $INSTALL_ANTIGRAVITY; then
  install_to_path "$HOME/.gemini/antigravity/skills" "Google Antigravity (~/.gemini/antigravity/skills)"
  # Also link or install into global config if ~/.gemini/config exists
  if [[ -d "$HOME/.gemini/config" ]]; then
    install_to_path "$HOME/.gemini/config/skills" "Antigravity Global Config (~/.gemini/config/skills)"
  fi
  # Also support ~/.agents/skills (workspace/user agent standard)
  if [[ -d "$HOME/.agents" ]]; then
    install_to_path "$HOME/.agents/skills" "Agent Skills Standard (~/.agents/skills)"
  fi
fi

# 2. Anthropic Claude Code
if $INSTALL_CLAUDE; then
  install_to_path "$HOME/.claude/skills" "Claude Code (~/.claude/skills)"
fi

# 3. Cursor IDE
if $INSTALL_CURSOR; then
  # Global cursor user directory or local .cursorrules template
  install_to_path "$HOME/.cursor/skills" "Cursor IDE Global (~/.cursor/skills)"
  echo "   💡 In your project workspace, ensure .cursorrules includes:"
  echo "      curl -fsSL ${RAW_BASE}/templates/.cursorrules >> .cursorrules"
fi

# 4. OpenAI Codex / CLI Agents
if $INSTALL_CODEX; then
  install_to_path "$HOME/.codex/skills" "OpenAI Codex (~/.codex/skills)"
fi

echo ""
echo "🎉 System Design Studio skill is successfully installed and ready!"
echo ""
echo "🚀 How it works in any chat:"
echo "   1. Open a new chat in any supported AI coding agent (Antigravity, Claude, Cursor, Codex)."
echo "   2. Ask: 'Let\'s learn system design' or 'Review topic 0.1'."
echo "   3. On first use, the skill automatically initializes the hidden '.system-design/'"
echo "      folder at the workspace root to track your progress in CURSOR.md."
echo "=========================================================="
