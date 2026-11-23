#!/bin/sh
# System Design Studio — Universal Agent Skill Uninstaller (v4.1.0)
# Safely eliminates the system-design-studio skill from all AI coding agents
# (Google Antigravity, Claude Code, Cursor IDE, OpenAI Codex).
#
# INVARIANT: This script ONLY removes agent skill files.
# Your project repositories, .system-design/ instances, study notes,
# and DECISIONS.md Architecture Decision Records are STRICTLY PRESERVED.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/uninstall.sh | bash
#   ./uninstall.sh [--purge] [--defaults|-y]

set -e
(set -o pipefail) 2>/dev/null && set -o pipefail || true

SKILL_NAME="system-design-studio"

echo "=========================================================="
echo "  System Design Studio — Skill Uninstaller Engine         "
echo "=========================================================="

HOME_DIR="${HOME:-}"
if [ -z "$HOME_DIR" ] && [ -n "${USERPROFILE:-}" ]; then
  HOME_DIR="$USERPROFILE"
fi

if [ -z "$HOME_DIR" ]; then
  echo "❌ Error: Could not determine user home directory." >&2
  exit 1
fi

XDG_CONFIG="${XDG_CONFIG_HOME:-$HOME_DIR/.config}"
GLOBAL_STUDIO_DIR="${SDS_GLOBAL_DIR:-$HOME_DIR/.system-design-studio}"

PURGE_GLOBAL_CONFIG=false
INTERACTIVE=true

for arg in "$@"; do
  case "$arg" in
    --purge)
      PURGE_GLOBAL_CONFIG=true
      ;;
    --defaults|--non-interactive|-y)
      INTERACTIVE=false
      ;;
    --help|-h)
      echo "System Design Studio Uninstaller"
      echo "Usage: uninstall.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --purge        Also remove ~/.system-design-studio/ global cache, CLI, and PATH entries"
      echo "  -y, --defaults Non-interactive, remove skill without confirmation prompt"
      echo ""
      echo "Note: Your local Git projects, notes, and .system-design/ folders are never deleted."
      exit 0
      ;;
  esac
done

# Check if terminal interaction is possible
TTY_IN=""
if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${CONTINUOUS_INTEGRATION:-}" ] || [ "$INTERACTIVE" = false ]; then
  INTERACTIVE=false
elif [ -t 0 ]; then
  TTY_IN="-"
elif [ -t 1 ] && (exec < /dev/tty) 2>/dev/null; then
  TTY_IN="/dev/tty"
else
  INTERACTIVE=false
fi

read_input() {
  if [ "$TTY_IN" = "/dev/tty" ]; then
    read -r "$1" < /dev/tty || true
  else
    read -r "$1" || true
  fi
}

# Potential Skill Target Directories across all AI coding agents
SKILL_PARENTS="
$HOME_DIR/.gemini/antigravity/skills
$HOME_DIR/.gemini/config/skills
$HOME_DIR/.agents/skills
$HOME_DIR/.claude/skills
$XDG_CONFIG/claude/skills
$HOME_DIR/.cursor/skills
$HOME_DIR/Library/Application Support/Cursor/User/skills
$XDG_CONFIG/Cursor/User/skills
$HOME_DIR/.codex/skills
$XDG_CONFIG/codex/skills
$GLOBAL_STUDIO_DIR/skills
"

ALL_TARGET_NAMES="system-design-studio sds-status sds-teach sds-discuss sds-complete sds-notes sds-projects sds-open sds-delete sds-curriculum sds-config sds-update sds-dashboard sds-rollback"

FOUND_LOCATIONS=""
for parent in $SKILL_PARENTS; do
  if [ -d "$parent" ]; then
    for item in $ALL_TARGET_NAMES; do
      if [ -d "$parent/$item" ]; then
        FOUND_LOCATIONS="$FOUND_LOCATIONS $parent/$item"
      fi
    done
  fi
done

if [ -z "$FOUND_LOCATIONS" ]; then
  echo "ℹ️  No active skill installations found in agent discovery paths."
else
  echo "🔍 Discovered active skill installations:"
  for loc in $FOUND_LOCATIONS; do
    echo "   • $loc"
  done
fi

echo ""
echo "🛡️  Safety Guarantee:"
echo "   This will ONLY remove the '$SKILL_NAME' skill package from your AI agents."
echo "   Your project repositories, .system-design/ folders, study notes, and"
echo "   DECISIONS.md records will remain 100% intact."
echo ""

if [ "$INTERACTIVE" = true ]; then
  printf "👉 Are you sure you want to remove the skill from all agents? [y/N]: "
  read_input confirm_uninstall
  case "$confirm_uninstall" in
    y*|Y*) ;;
    *)
      echo "❌ Uninstallation aborted by user."
      exit 0
      ;;
  esac
fi

REMOVED_COUNT=0
for loc in $FOUND_LOCATIONS; do
  if [ -d "$loc" ]; then
    rm -rf "$loc"
    echo "   🗑️  Removed: $loc"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
  fi
done

# Remove bin wrappers if present
if [ -d "$GLOBAL_STUDIO_DIR/bin" ]; then
  rm -f "$GLOBAL_STUDIO_DIR/bin/sds" "$GLOBAL_STUDIO_DIR/bin/sds.cmd" "$GLOBAL_STUDIO_DIR/bin/sds.ps1"
  echo "   🗑️  Removed CLI wrappers from $GLOBAL_STUDIO_DIR/bin"
fi

# Remove standard symlinks if pointing to sds
if [ -L "$HOME_DIR/.local/bin/sds" ]; then
  rm -f "$HOME_DIR/.local/bin/sds"
  echo "   🗑️  Removed symlink: $HOME_DIR/.local/bin/sds"
fi
if [ -L "/usr/local/bin/sds" ] && [ -w "/usr/local/bin/sds" ]; then
  rm -f "/usr/local/bin/sds"
  echo "   🗑️  Removed symlink: /usr/local/bin/sds"
fi

# Remove command markdown wrappers for Claude Code and Codex if present
if [ -d "$HOME_DIR/.claude/commands" ]; then
  for item in $ALL_TARGET_NAMES; do
    if [ -f "$HOME_DIR/.claude/commands/${item}.md" ]; then
      rm -f "$HOME_DIR/.claude/commands/${item}.md"
      echo "   🗑️  Removed command: $HOME_DIR/.claude/commands/${item}.md"
    fi
  done
fi
if [ -d "$HOME_DIR/.codex/prompts" ]; then
  for item in $ALL_TARGET_NAMES; do
    if [ -f "$HOME_DIR/.codex/prompts/${item}.md" ]; then
      rm -f "$HOME_DIR/.codex/prompts/${item}.md"
      echo "   🗑️  Removed prompt: $HOME_DIR/.codex/prompts/${item}.md"
    fi
  done
fi

# Optional global purge: clean ~/.system-design-studio and clean PATH entries from shell profiles
if [ "$PURGE_GLOBAL_CONFIG" = true ]; then
  echo ""
  echo "🧹 Purging global studio cache and shell PATH configurations..."

  clean_profile_path() {
    p_file="$1"
    [ -f "$p_file" ] || return 0
    if grep -q "\.system-design-studio/bin" "$p_file" 2>/dev/null; then
      if command -v python3 >/dev/null 2>&1; then
        python3 -c "
with open('$p_file', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
new_lines = []
skip_next = False
for line in lines:
    if '# System Design Studio CLI (sds)' in line:
        continue
    if '.system-design-studio/bin' in line:
        continue
    new_lines.append(line)
with open('$p_file', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
" 2>/dev/null || true
      else
        sed -i.bak '/\.system-design-studio\/bin/d' "$p_file" 2>/dev/null || true
        rm -f "${p_file}.bak" 2>/dev/null || true
      fi
      echo "   ✅ Cleaned PATH from: $p_file"
    fi
  }

  clean_profile_path "$HOME_DIR/.zshrc"
  clean_profile_path "$HOME_DIR/.bashrc"
  clean_profile_path "$HOME_DIR/.bash_profile"
  clean_profile_path "$HOME_DIR/.profile"

  # Fish shell
  fish_sds="$HOME_DIR/.config/fish/conf.d/sds.fish"
  if [ -f "$fish_sds" ]; then
    rm -f "$fish_sds"
    echo "   ✅ Removed fish configuration: $fish_sds"
  fi

  # Windows Registry PATH
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
      \$current = [Environment]::GetEnvironmentVariable('Path', 'User')
      if (\$current -match '\.system-design-studio') {
        \$filtered = (\$current -split ';' | Where-Object { \$_ -notmatch '\.system-design-studio' }) -join ';'
        [Environment]::SetEnvironmentVariable('Path', \$filtered, 'User')
        Write-Output 'CLEANED_WIN_PATH'
      }
    " 2>/dev/null | grep -q "CLEANED_WIN_PATH" && {
      echo "   ✅ Cleaned Windows User Environment PATH registry"
    } || true
  fi

  if [ -d "$GLOBAL_STUDIO_DIR" ]; then
    rm -rf "$GLOBAL_STUDIO_DIR"
    echo "   🗑️  Purged global directory: $GLOBAL_STUDIO_DIR"
  fi
fi

echo ""
echo "=========================================================="
echo "✅ Uninstallation Complete!"
echo "   • Removed skill package from $REMOVED_COUNT agent directory location(s)."
echo "   • Your personal project workspaces and notes were preserved."
echo "=========================================================="
