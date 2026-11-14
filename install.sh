#!/bin/sh
# System Design Studio — Universal Agent Skill Installer
# Compatible with macOS, Linux (Debian, Ubuntu, Fedora, Arch, Alpine), BSD, and Windows (Git Bash/WSL).
# Works across POSIX sh, dash, ash, bash (3.2+), and zsh.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | sh
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | sh -s -- --all
#   ./install.sh [--all] [--antigravity] [--claude] [--cursor] [--codex]

set -e
(set -o pipefail) 2>/dev/null && set -o pipefail || true

REPO_URL="https://github.com/alph-a07/system-design-studio.git"
ARCHIVE_URL="https://github.com/alph-a07/system-design-studio/archive/refs/heads/main.tar.gz"
RAW_BASE="https://raw.githubusercontent.com/alph-a07/system-design-studio/main"
SKILL_NAME="system-design-studio"

echo "=========================================================="
echo "  System Design Studio — Universal Agent Skill Installer  "
echo "=========================================================="

# 1. Resolve Operating System & Base Directories
OS_TYPE="$(uname -s 2>/dev/null || echo "Unknown")"
case "$OS_TYPE" in
  Darwin*)  PLATFORM="macos" ;;
  Linux*)   PLATFORM="linux" ;;
  CYGWIN*|MINGW*|MSYS*) PLATFORM="windows" ;;
  FreeBSD*|OpenBSD*|NetBSD*) PLATFORM="bsd" ;;
  *)        PLATFORM="unix" ;;
esac

HOME_DIR="${HOME:-}"
if [ -z "$HOME_DIR" ] && [ -n "${USERPROFILE:-}" ]; then
  HOME_DIR="$USERPROFILE"
fi

if [ -z "$HOME_DIR" ]; then
  echo "❌ Error: Could not determine user home directory." >&2
  exit 1
fi

XDG_CONFIG="${XDG_CONFIG_HOME:-$HOME_DIR/.config}"

# 2. Parse Flags or Auto-Detect Active Coding Agents
INSTALL_ALL=false
INSTALL_ANTIGRAVITY=false
INSTALL_CLAUDE=false
INSTALL_CURSOR=false
INSTALL_CODEX=false
MANUAL_SELECTION=false

for arg in "$@"; do
  case "$arg" in
    --all|-a)
      INSTALL_ALL=true
      MANUAL_SELECTION=true
      ;;
    --antigravity|--gemini)
      INSTALL_ANTIGRAVITY=true
      MANUAL_SELECTION=true
      ;;
    --claude)
      INSTALL_CLAUDE=true
      MANUAL_SELECTION=true
      ;;
    --cursor)
      INSTALL_CURSOR=true
      MANUAL_SELECTION=true
      ;;
    --codex)
      INSTALL_CODEX=true
      MANUAL_SELECTION=true
      ;;
    --help|-h)
      echo "System Design Studio Installer"
      echo "Usage: install.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --all, -a         Install for all supported AI agents"
      echo "  --antigravity     Install for Google Antigravity"
      echo "  --claude          Install for Anthropic Claude Code"
      echo "  --cursor          Install for Cursor IDE"
      echo "  --codex           Install for OpenAI Codex"
      echo "  --help, -h        Show this help message"
      echo ""
      echo "When no options are supplied, installer auto-detects active agents on your machine."
      exit 0
      ;;
    *)
      # Ignore unrecognized args
      ;;
  esac
done

if [ "$MANUAL_SELECTION" = false ]; then
  echo "🔍 Auto-detecting AI coding agents on this system (${PLATFORM})..."

  # Check Antigravity / Gemini
  if command -v agy >/dev/null 2>&1 || command -v gemini >/dev/null 2>&1 || [ -d "$HOME_DIR/.gemini" ] || [ -d "$HOME_DIR/.agents" ]; then
    INSTALL_ANTIGRAVITY=true
    echo "   Found Google Antigravity / Gemini CLI"
  fi

  # Check Claude Code
  if command -v claude >/dev/null 2>&1 || [ -d "$HOME_DIR/.claude" ] || [ -d "$XDG_CONFIG/claude" ]; then
    INSTALL_CLAUDE=true
    echo "   Found Anthropic Claude Code"
  fi

  # Check Cursor
  if command -v cursor >/dev/null 2>&1 || [ -d "$HOME_DIR/.cursor" ] || [ -d "$HOME_DIR/Library/Application Support/Cursor" ] || [ -d "$XDG_CONFIG/Cursor" ] || [ -f ".cursorrules" ] || [ -d ".cursor" ]; then
    INSTALL_CURSOR=true
    echo "   Found Cursor IDE"
  fi

  # Check Codex
  if command -v codex >/dev/null 2>&1 || [ -d "$HOME_DIR/.codex" ] || [ -d "$XDG_CONFIG/codex" ]; then
    INSTALL_CODEX=true
    echo "   Found OpenAI Codex"
  fi

  # If none detected, default to universal installation for all agents
  if [ "$INSTALL_ANTIGRAVITY" = false ] && [ "$INSTALL_CLAUDE" = false ] && [ "$INSTALL_CURSOR" = false ] && [ "$INSTALL_CODEX" = false ]; then
    echo "   No agent profiles specifically detected; installing universal skill across all paths."
    INSTALL_ALL=true
  fi
fi

if [ "$INSTALL_ALL" = true ]; then
  INSTALL_ANTIGRAVITY=true
  INSTALL_CLAUDE=true
  INSTALL_CURSOR=true
  INSTALL_CODEX=true
fi

# 3. Locate or Fetch Skill Files
SCRIPT_PATH="${0:-}"
SCRIPT_DIR=""
if [ -n "$SCRIPT_PATH" ] && [ -f "$SCRIPT_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" 2>/dev/null && pwd || echo "")"
fi
SOURCE_SKILL=""
TEMP_DIR=""

cleanup() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT INT TERM

if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/skills/$SKILL_NAME" ] && [ -f "$SCRIPT_DIR/skills/$SKILL_NAME/SKILL.md" ]; then
  echo "📂 Using local skill source from ${SCRIPT_DIR}..."
  SOURCE_SKILL="$SCRIPT_DIR/skills/$SKILL_NAME"
else
  TEMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'sds_install.XXXXXX' 2>/dev/null || echo "/tmp/sds_install_$$")"
  mkdir -p "$TEMP_DIR"

  if command -v git >/dev/null 2>&1; then
    echo "📥 Cloning skill package from GitHub via git..."
    git clone --depth 1 --quiet "$REPO_URL" "$TEMP_DIR/repo"
    SOURCE_SKILL="$TEMP_DIR/repo/skills/$SKILL_NAME"
  elif command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    echo "📥 Fetching skill package from GitHub via curl & tar..."
    mkdir -p "$TEMP_DIR/archive"
    curl -fsSL "$ARCHIVE_URL" | tar -xz -C "$TEMP_DIR/archive"
    SOURCE_SKILL="$TEMP_DIR/archive/system-design-studio-main/skills/$SKILL_NAME"
  elif command -v wget >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    echo "📥 Fetching skill package from GitHub via wget & tar..."
    mkdir -p "$TEMP_DIR/archive"
    wget -qO- "$ARCHIVE_URL" | tar -xz -C "$TEMP_DIR/archive"
    SOURCE_SKILL="$TEMP_DIR/archive/system-design-studio-main/skills/$SKILL_NAME"
  else
    echo "❌ Error: git, curl, or wget with tar is required to install System Design Studio." >&2
    exit 1
  fi
fi

if [ ! -f "$SOURCE_SKILL/SKILL.md" ]; then
  echo "❌ Error: Skill package could not be verified (SKILL.md missing in source)." >&2
  exit 1
fi

# 4. Helper Function to Install to Path
install_to_path() {
  target_parent="$1"
  agent_label="$2"

  target_dir="${target_parent}/${SKILL_NAME}"
  echo "📦 Installing for ${agent_label}..."
  mkdir -p "$target_parent"
  rm -rf "$target_dir"
  cp -R "$SOURCE_SKILL" "$target_dir"
  chmod -R u+rwX,go+rX "$target_dir" 2>/dev/null || true
  chmod +x "$target_dir/scripts/"*.sh 2>/dev/null || true

  if [ -f "$target_dir/SKILL.md" ]; then
    echo "   ✅ Verified at ${target_dir}"
  else
    echo "   ⚠️ Warning: Installation check failed at ${target_dir}" >&2
  fi
}

echo ""

# 5. Execute Installations
INSTALLED_COUNT=0

# A. Google Antigravity & Agent Open Standards
if [ "$INSTALL_ANTIGRAVITY" = true ]; then
  install_to_path "$HOME_DIR/.gemini/antigravity/skills" "Google Antigravity (~/.gemini/antigravity/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  # Also install in ~/.gemini/config/skills if config exists or was targeted
  if [ -d "$HOME_DIR/.gemini/config" ] || [ "$INSTALL_ALL" = true ]; then
    install_to_path "$HOME_DIR/.gemini/config/skills" "Antigravity Global Config (~/.gemini/config/skills)"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi

  # Vendor-neutral open agent skills standard
  install_to_path "$HOME_DIR/.agents/skills" "Agent Skills Open Standard (~/.agents/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
fi

# B. Anthropic Claude Code
if [ "$INSTALL_CLAUDE" = true ]; then
  install_to_path "$HOME_DIR/.claude/skills" "Claude Code (~/.claude/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  # On Linux with XDG
  if [ "$PLATFORM" = "linux" ] && [ -d "$XDG_CONFIG/claude" ]; then
    install_to_path "$XDG_CONFIG/claude/skills" "Claude Code XDG (~/.config/claude/skills)"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

# C. Cursor IDE
if [ "$INSTALL_CURSOR" = true ]; then
  install_to_path "$HOME_DIR/.cursor/skills" "Cursor IDE Global (~/.cursor/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  # macOS App Support path if exists
  if [ "$PLATFORM" = "macos" ] && [ -d "$HOME_DIR/Library/Application Support/Cursor" ]; then
    install_to_path "$HOME_DIR/Library/Application Support/Cursor/User/skills" "Cursor User Library"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi

  # Linux XDG path if exists
  if [ "$PLATFORM" = "linux" ] && [ -d "$XDG_CONFIG/Cursor" ]; then
    install_to_path "$XDG_CONFIG/Cursor/User/skills" "Cursor User XDG"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi

  # Windows AppData path if exists
  if [ -n "${APPDATA:-}" ] && [ -d "$APPDATA/Cursor" ]; then
    install_to_path "$APPDATA/Cursor/User/skills" "Cursor Windows AppData"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

# D. OpenAI Codex / CLI Agents
if [ "$INSTALL_CODEX" = true ]; then
  install_to_path "$HOME_DIR/.codex/skills" "OpenAI Codex (~/.codex/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  if [ "$PLATFORM" = "linux" ] && [ -d "$XDG_CONFIG/codex" ]; then
    install_to_path "$XDG_CONFIG/codex/skills" "OpenAI Codex XDG"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

# E. Windows specific fallback path resolution (if USERPROFILE differs from HOME)
if [ -n "${USERPROFILE:-}" ] && [ "$USERPROFILE" != "$HOME_DIR" ]; then
  if [ "$INSTALL_ANTIGRAVITY" = true ] && [ -d "$USERPROFILE/.gemini" ]; then
    install_to_path "$USERPROFILE/.gemini/antigravity/skills" "Windows User Antigravity"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
  if [ "$INSTALL_CLAUDE" = true ] && [ -d "$USERPROFILE/.claude" ]; then
    install_to_path "$USERPROFILE/.claude/skills" "Windows User Claude"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

echo ""
echo "=========================================================="
echo "🎉 System Design Studio skill installed across ${INSTALLED_COUNT} agent location(s)!"
echo "=========================================================="
echo ""
echo "🚀 Ready to use in any chat thread:"
echo "   1. Open any AI coding agent (Antigravity, Claude Code, Cursor, Codex)."
echo "   2. Ask: 'Let\'s learn system design' or 'Review topic 0.1'."
echo "   3. First prompt automatically scaffolds '.system-design/' at project root"
echo "      to track your syllabus progress and cognitive state in CURSOR.md."
echo ""
echo "💡 Cursor Users: To guarantee workspace context in Cursor, you can also run:"
echo "   curl -fsSL ${RAW_BASE}/templates/.cursorrules >> .cursorrules"
echo "=========================================================="
