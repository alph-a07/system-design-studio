#!/bin/sh
# System Design Studio — Universal Skill & Instance Updater (v4.1.1)
# Updates agent skills to latest release while strictly preserving:
# 1. User learning progress (manifest.json, CURSOR.md, CURRICULUM.md, DECISIONS.md)
# 2. Existing interactive lesson artifacts (lessons/*.html, lessons/*.md)
# 3. User custom settings & chosen visual preferences (via merge-settings.py)
# 4. Shell PATH configuration for 'sds' CLI across macOS, Linux, BSD, and Windows
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
GLOBAL_STUDIO_DIR="${SDS_GLOBAL_DIR:-$HOME_DIR/.system-design-studio}"
GLOBAL_BIN="${GLOBAL_STUDIO_DIR}/bin"

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
SOURCE_ROOT=""

# If inside developer repo
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/plugin.json" ] && [ -d "$SCRIPT_DIR/skills/$SKILL_NAME" ]; then
  SOURCE_ROOT="$SCRIPT_DIR"
  SOURCE_SKILLS_DIR="$(cd "$SCRIPT_DIR/skills" && pwd)"
  if [ -d "$SCRIPT_DIR/agents" ]; then
    SOURCE_AGENTS_DIR="$(cd "$SCRIPT_DIR/agents" && pwd)"
  fi
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../../plugin.json" ] && [ -d "$SCRIPT_DIR/../../skills/$SKILL_NAME" ]; then
  SOURCE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  SOURCE_SKILLS_DIR="$(cd "$SCRIPT_DIR/../../skills" && pwd)"
  if [ -d "$SCRIPT_DIR/../../agents" ]; then
    SOURCE_AGENTS_DIR="$(cd "$SCRIPT_DIR/../../agents" && pwd)"
  fi
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../../../plugin.json" ] && [ -d "$SCRIPT_DIR/../../$SKILL_NAME" ]; then
  SOURCE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
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
  SOURCE_ROOT="$TEMP_DIR/system-design-studio-main"
  SOURCE_SKILLS_DIR="$SOURCE_ROOT/skills"
  if [ -d "$SOURCE_ROOT/agents" ]; then
    SOURCE_AGENTS_DIR="$SOURCE_ROOT/agents"
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
$XDG_CONFIG/claude/skills
$HOME_DIR/.cursor/skills
$HOME_DIR/Library/Application Support/Cursor/User/skills
$XDG_CONFIG/Cursor/User/skills
$HOME_DIR/.codex/skills
$XDG_CONFIG/codex/skills
$GLOBAL_STUDIO_DIR/skills
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
$XDG_CONFIG/claude/agents
$HOME_DIR/.cursor/agents
$HOME_DIR/Library/Application Support/Cursor/User/agents
$XDG_CONFIG/Cursor/User/agents
$HOME_DIR/.codex/agents
$XDG_CONFIG/codex/agents
$GLOBAL_STUDIO_DIR/agents
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

# 3. Update CLI Binaries in ~/.system-design-studio/bin
echo "⚡ Updating CLI binaries..."
mkdir -p "$GLOBAL_BIN"
mkdir -p "$GLOBAL_STUDIO_DIR"

if [ -n "$SOURCE_ROOT" ] && [ -d "$SOURCE_ROOT/bin" ]; then
  cp -R "$SOURCE_ROOT/bin/"* "$GLOBAL_BIN/" 2>/dev/null || true
  chmod +x "$GLOBAL_BIN/sds" 2>/dev/null || true
fi

# Copy update scripts, plugin.json, and marketplace.json into global studio directory
if [ -n "$SOURCE_ROOT" ]; then
  [ -f "$SOURCE_ROOT/plugin.json" ] && cp "$SOURCE_ROOT/plugin.json" "$GLOBAL_STUDIO_DIR/plugin.json" 2>/dev/null || true
  [ -f "$SOURCE_ROOT/marketplace.json" ] && cp "$SOURCE_ROOT/marketplace.json" "$GLOBAL_STUDIO_DIR/marketplace.json" 2>/dev/null || true
  [ -f "$SOURCE_ROOT/update.sh" ] && cp "$SOURCE_ROOT/update.sh" "$GLOBAL_STUDIO_DIR/update.sh" 2>/dev/null || true
  [ -f "$SOURCE_ROOT/update.ps1" ] && cp "$SOURCE_ROOT/update.ps1" "$GLOBAL_STUDIO_DIR/update.ps1" 2>/dev/null || true
  chmod +x "$GLOBAL_STUDIO_DIR/update.sh" 2>/dev/null || true
fi

# Invalidate stale update-check caches so dashboard immediately reflects latest version
rm -f "$GLOBAL_STUDIO_DIR/.update-check.json" "$HOME_DIR/.system-design-studio-update.json" 2>/dev/null || true
[ -n "$INSTANCE_DIR" ] && rm -f "${INSTANCE_DIR}/.update-check.json" 2>/dev/null || true
rm -f ".system-design/.update-check.json" 2>/dev/null || true

# 4. Verify and configure shell PATH for 'sds'
configure_user_path() {
  target_bin="$1"
  [ -d "$target_bin" ] || return 0

  MODIFIED_PROFILES=""

  add_export_to_file() {
    profile_path="$1"
    [ -n "$profile_path" ] || return 0

    profile_dir="$(dirname "$profile_path")"
    [ -d "$profile_dir" ] || mkdir -p "$profile_dir" 2>/dev/null || return 0

    if [ -f "$profile_path" ] && grep -q "\.system-design-studio/bin" "$profile_path" 2>/dev/null; then
      return 0
    fi

    if [ -f "$profile_path" ]; then
      [ -n "$(tail -c 1 "$profile_path" 2>/dev/null)" ] && echo "" >> "$profile_path"
    fi

    cat <<'PATH_EOF' >> "$profile_path"

# System Design Studio CLI (sds)
export PATH="$HOME/.system-design-studio/bin:$PATH"
PATH_EOF

    MODIFIED_PROFILES="$MODIFIED_PROFILES $profile_path"
  }

  add_to_fish() {
    fish_conf_dir="$HOME_DIR/.config/fish/conf.d"
    if [ -d "$HOME_DIR/.config/fish" ] || command -v fish >/dev/null 2>&1; then
      mkdir -p "$fish_conf_dir" 2>/dev/null || return 0
      fish_sds_file="$fish_conf_dir/sds.fish"
      if [ ! -f "$fish_sds_file" ] || ! grep -q "\.system-design-studio/bin" "$fish_sds_file" 2>/dev/null; then
        cat <<'FISH_EOF' > "$fish_sds_file"
# System Design Studio CLI (sds)
if test -d "$HOME/.system-design-studio/bin"
    if not contains "$HOME/.system-design-studio/bin" $PATH
        set -gx PATH "$HOME/.system-design-studio/bin" $PATH
    end
end
FISH_EOF
        MODIFIED_PROFILES="$MODIFIED_PROFILES $fish_sds_file"
      fi
    fi
  }

  CURRENT_SHELL="$(basename "${SHELL:-}" 2>/dev/null || echo "")"

  # A. Zsh
  if [ "$PLATFORM" = "macos" ] || [ "$CURRENT_SHELL" = "zsh" ] || [ -f "$HOME_DIR/.zshrc" ]; then
    add_export_to_file "$HOME_DIR/.zshrc"
  fi

  # B. Bash
  if [ -f "$HOME_DIR/.bashrc" ] || [ "$CURRENT_SHELL" = "bash" ] || [ "$PLATFORM" = "linux" ] || [ "$PLATFORM" = "windows" ]; then
    add_export_to_file "$HOME_DIR/.bashrc"
  fi

  # macOS bash login shells
  if [ "$PLATFORM" = "macos" ] && { [ -f "$HOME_DIR/.bash_profile" ] || [ "$CURRENT_SHELL" = "bash" ]; }; then
    add_export_to_file "$HOME_DIR/.bash_profile"
  fi

  # Windows Git Bash / MSYS2
  if [ "$PLATFORM" = "windows" ]; then
    add_export_to_file "$HOME_DIR/.bash_profile"
  fi

  # Universal fallback ~/.profile
  if [ -f "$HOME_DIR/.profile" ] || [ "$PLATFORM" = "linux" ] || [ "$PLATFORM" = "bsd" ]; then
    add_export_to_file "$HOME_DIR/.profile"
  fi

  # C. Fish shell
  add_to_fish

  # D. Windows Native PATH
  if [ "$PLATFORM" = "windows" ]; then
    if command -v powershell.exe >/dev/null 2>&1; then
      WIN_TARGET_DIR="$(cygpath -w "$target_bin" 2>/dev/null || python3 -c "import os; print(os.path.abspath('$target_bin'))" 2>/dev/null || echo "")"
      if [ -n "$WIN_TARGET_DIR" ]; then
        powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
          \$target = '$WIN_TARGET_DIR'
          \$current = [Environment]::GetEnvironmentVariable('Path', 'User')
          if (\$current -split ';' -notcontains \$target) {
            \$new = if ([string]::IsNullOrEmpty(\$current)) { \$target } else { \"\$current;\$target\" }
            [Environment]::SetEnvironmentVariable('Path', \$new, 'User')
            Write-Output 'UPDATED_WIN_REGISTRY'
          }
        " 2>/dev/null | grep -q "UPDATED_WIN_REGISTRY" && {
          echo "   ✅ Added to Windows User Environment PATH registry"
        } || true
      fi
    fi
  fi

  # E. Standard Symlinks
  LOCAL_BIN="$HOME_DIR/.local/bin"
  if [ -d "$LOCAL_BIN" ] || [ -w "$HOME_DIR/.local" ]; then
    mkdir -p "$LOCAL_BIN" 2>/dev/null || true
    if [ -d "$LOCAL_BIN" ] && [ -w "$LOCAL_BIN" ]; then
      ln -sf "$target_bin/sds" "$LOCAL_BIN/sds" 2>/dev/null || true
    fi
  fi

  if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$target_bin/sds" "/usr/local/bin/sds" 2>/dev/null || true
  fi

  if [ -n "$MODIFIED_PROFILES" ]; then
    for prof in $MODIFIED_PROFILES; do
      echo "   ✅ Configured PATH in: $prof"
    done
  fi

  export PATH="$target_bin:$PATH"
}

configure_user_path "$GLOBAL_BIN"

# 5. Settings Merge & Local Instance Protection
if [ -d "$INSTANCE_DIR" ]; then
  echo ""
  echo "🔧 Local project instance found at '${INSTANCE_DIR}/':"
  
  SETTINGS_FILE="${INSTANCE_DIR}/settings.json"
  TEMPLATE_SETTINGS="${SOURCE_SKILL}/resources/settings-template.json"
  MERGE_SCRIPT="${SOURCE_SKILL}/scripts/merge-settings.py"

  if [ -f "$SETTINGS_FILE" ] && [ -f "$TEMPLATE_SETTINGS" ] && [ -f "$MERGE_SCRIPT" ]; then
    echo "   🔄 Merging settings.json to preserve user preferences..."
    python3 "$MERGE_SCRIPT" --current "$SETTINGS_FILE" --template "$TEMPLATE_SETTINGS" --output "$SETTINGS_FILE" 2>/dev/null || true
  elif [ ! -f "$SETTINGS_FILE" ] && [ -f "$TEMPLATE_SETTINGS" ]; then
    echo "   ✨ Adding settings.json from template..."
    cp "$TEMPLATE_SETTINGS" "$SETTINGS_FILE"
  fi

  # Run verification
  VERIFY_SCRIPT="${SOURCE_SKILL}/scripts/verify-instance.py"
  if [ -f "$VERIFY_SCRIPT" ]; then
    echo ""
    python3 "$VERIFY_SCRIPT" "$INSTANCE_DIR" 2>/dev/null || true
  fi
fi

echo ""
echo "=========================================================="
echo "🎉 System Design Studio updated across ${UPDATED_COUNT} agent location(s)!"
echo "   All learning progress and custom user settings were preserved."
echo "=========================================================="
