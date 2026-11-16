#!/bin/sh
# System Design Studio — Universal Agent Skill Installer (v3.2)
# Configures global studio preferences (~/.system-design-studio/config.json)
# and installs skill packages across AI coding agents (Antigravity, Claude, Cursor, Codex).
# Compatible with macOS, Linux, BSD, and Windows (Git Bash/WSL).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash
#   ./install.sh [--theme <theme>] [--output <html|markdown>] [--notes <true|false>] [--defaults]

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
GLOBAL_STUDIO_DIR="${SDS_GLOBAL_DIR:-$HOME_DIR/.system-design-studio}"
GLOBAL_CONFIG="${GLOBAL_STUDIO_DIR}/config.json"
GLOBAL_PROJECTS="${GLOBAL_STUDIO_DIR}/projects.json"
GLOBAL_BIN="${GLOBAL_STUDIO_DIR}/bin"

# 2. Defaults for Global Settings
THEME_STYLE="slate-clean"
OUTPUT_FORMAT="html"
AUTO_NOTES="true"
NOTES_STRUCTURE="per-topic"
INTERACTIVE=true
MANUAL_AGENT_SELECTION=false

INSTALL_ALL=false
INSTALL_ANTIGRAVITY=false
INSTALL_CLAUDE=false
INSTALL_CURSOR=false
INSTALL_CODEX=false

# Check existing global config to inherit prior choices
if [ -f "$GLOBAL_CONFIG" ] && command -v python3 >/dev/null 2>&1; then
  THEME_STYLE="$(python3 -c "import json; print(json.load(open('$GLOBAL_CONFIG')).get('artifactStyle', 'slate-clean'))" 2>/dev/null || echo "slate-clean")"
  OUTPUT_FORMAT="$(python3 -c "import json; print(json.load(open('$GLOBAL_CONFIG')).get('outputType', 'html'))" 2>/dev/null || echo "html")"
  NOTES_STRUCTURE="$(python3 -c "import json; print(json.load(open('$GLOBAL_CONFIG')).get('notesStructure', 'per-topic'))" 2>/dev/null || echo "per-topic")"
  AUTO_NOTES="$(python3 -c "import json; print(str(json.load(open('$GLOBAL_CONFIG')).get('autoGenerateNotes', True)).lower())" 2>/dev/null || echo "true")"
fi

# Parse Flags
for arg in "$@"; do
  case "$arg" in
    --all|-a)
      INSTALL_ALL=true
      MANUAL_AGENT_SELECTION=true
      ;;
    --antigravity|--gemini)
      INSTALL_ANTIGRAVITY=true
      MANUAL_AGENT_SELECTION=true
      ;;
    --claude)
      INSTALL_CLAUDE=true
      MANUAL_AGENT_SELECTION=true
      ;;
    --cursor)
      INSTALL_CURSOR=true
      MANUAL_AGENT_SELECTION=true
      ;;
    --codex)
      INSTALL_CODEX=true
      MANUAL_AGENT_SELECTION=true
      ;;
    --theme=*)
      THEME_STYLE="${arg#*=}"
      ;;
    --output=*)
      OUTPUT_FORMAT="${arg#*=}"
      ;;
    --notes=*)
      AUTO_NOTES="${arg#*=}"
      ;;
    --notes-structure=*)
      NOTES_STRUCTURE="${arg#*=}"
      ;;
    --defaults|--non-interactive|-y)
      INTERACTIVE=false
      ;;
    --help|-h)
      echo "System Design Studio Installer"
      echo "Usage: install.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --theme <id>             slate-clean, editorial-paper, midnight-neon, nordic-frost, warm-amber"
      echo "  --output <type>          html (interactive simulators) | markdown (clean text with Mermaid/ASCII)"
      echo "  --notes <bool>           true | false (auto-generate discussion notes on completion)"
      echo "  --notes-structure <str>  per-topic | per-cluster | per-tier | single-file"
      echo "  --all, -a                Install for all supported AI agents"
      echo "  --antigravity            Install for Google Antigravity"
      echo "  --claude                 Install for Anthropic Claude Code"
      echo "  --cursor                 Install for Cursor IDE"
      echo "  --codex                  Install for OpenAI Codex"
      echo "  --defaults, -y           Use recommended defaults without prompting"
      exit 0
      ;;
    *)
      ;;
  esac
done

# Check if terminal interaction is possible (direct TTY or redirected via /dev/tty)
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

# 3. Interactive Global Configuration Wizard
if [ "$INTERACTIVE" = true ]; then
  echo ""
  echo "⚙️  System Design Studio Global Preferences Setup"
  echo "----------------------------------------------------------"
  
  echo "🎨 Select Default Artifact Visual Theme:"
  echo "   [1] Modern Slate (Dark Tech) [Default]"
  echo "   [2] Clean Editorial (Warm Light Paper)"
  echo "   [3] Cyber Obsidian (High Contrast Neon)"
  echo "   [4] Nordic Frost (Polar Calm Dark)"
  echo "   [5] Warm Amber (Espresso Glow)"
  printf "   Choose theme [1]: "
  read_input input_theme
  case "$input_theme" in
    2) THEME_STYLE="editorial-paper" ;;
    3) THEME_STYLE="midnight-neon" ;;
    4) THEME_STYLE="nordic-frost" ;;
    5) THEME_STYLE="warm-amber" ;;
    *) THEME_STYLE="slate-clean" ;;
  esac

  echo ""
  echo "📄 Select Default Lesson Output Format:"
  echo "   [1] Interactive HTML (Tactile JS Simulators & Visual HUD) [Recommended]"
  echo "   [2] Clean Markdown (Zero-JS pure Markdown with Mermaid diagrams & ASCII charts)"
  printf "   Choose format [1]: "
  read_input input_fmt
  case "$input_fmt" in
    2) OUTPUT_FORMAT="markdown" ;;
    *) OUTPUT_FORMAT="html" ;;
  esac

  echo ""
  echo "📝 Auto-Generate Discussion-Synthesized Study Notes on Sign-off?"
  echo "   [1] Enabled (Synthesizes chat defense, edge cases & formulas on completion) [Default]"
  echo "   [2] Disabled"
  printf "   Enable notes [1]: "
  read_input input_notes
  case "$input_notes" in
    2) AUTO_NOTES="false" ;;
    *) AUTO_NOTES="true" ;;
  esac

  if [ "$AUTO_NOTES" = "true" ]; then
    echo ""
    echo "🗂️  Default Notes Structuring Strategy:"
    echo "   [1] Per-Topic Files (notes/<tier>/<cluster>/<topic>.md) [Default]"
    echo "   [2] Per-Cluster Files (notes/<tier>/<cluster>.md)"
    echo "   [3] Per-Tier Files (notes/tier-<N>.md)"
    echo "   [4] Single Master File (notes/SYSTEM-DESIGN-NOTES.md)"
    printf "   Choose structuring [1]: "
    read_input input_struct
    case "$input_struct" in
      2) NOTES_STRUCTURE="per-cluster" ;;
      3) NOTES_STRUCTURE="per-tier" ;;
      4) NOTES_STRUCTURE="single-file" ;;
      *) NOTES_STRUCTURE="per-topic" ;;
    esac
  fi
fi

# 4. Save Global Settings & Initialize Machine Root Directory
mkdir -p "$GLOBAL_STUDIO_DIR"
mkdir -p "$GLOBAL_STUDIO_DIR/projects"
mkdir -p "$GLOBAL_BIN"

cat <<EOF > "$GLOBAL_CONFIG"
{
  "\$schemaVersion": "3.2",
  "artifactStyle": "${THEME_STYLE}",
  "outputType": "${OUTPUT_FORMAT}",
  "autoGenerateNotes": ${AUTO_NOTES},
  "notesStructure": "${NOTES_STRUCTURE}",
  "defaultTrack": "full-mastery"
}
EOF

if [ ! -f "$GLOBAL_PROJECTS" ]; then
  cat <<EOF > "$GLOBAL_PROJECTS"
{
  "\$schemaVersion": "3.2",
  "activeProjectId": null,
  "projects": []
}
EOF
fi

echo ""
echo "💾 Global preferences saved to ${GLOBAL_CONFIG}"

# 5. Agent Detection
if [ "$MANUAL_AGENT_SELECTION" = false ]; then
  echo "🔍 Auto-detecting AI coding agents on this system (${PLATFORM})..."

  if command -v agy >/dev/null 2>&1 || command -v gemini >/dev/null 2>&1 || [ -d "$HOME_DIR/.gemini" ] || [ -d "$HOME_DIR/.agents" ]; then
    INSTALL_ANTIGRAVITY=true
    echo "   Found Google Antigravity / Gemini CLI"
  fi

  if command -v claude >/dev/null 2>&1 || [ -d "$HOME_DIR/.claude" ] || [ -d "$XDG_CONFIG/claude" ]; then
    INSTALL_CLAUDE=true
    echo "   Found Anthropic Claude Code"
  fi

  if command -v cursor >/dev/null 2>&1 || [ -d "$HOME_DIR/.cursor" ] || [ -d "$HOME_DIR/Library/Application Support/Cursor" ] || [ -d "$XDG_CONFIG/Cursor" ] || [ -f ".cursorrules" ] || [ -d ".cursor" ]; then
    INSTALL_CURSOR=true
    echo "   Found Cursor IDE"
  fi

  if command -v codex >/dev/null 2>&1 || [ -d "$HOME_DIR/.codex" ] || [ -d "$XDG_CONFIG/codex" ]; then
    INSTALL_CODEX=true
    echo "   Found OpenAI Codex"
  fi

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

# 6. Locate or Fetch Skill Files
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
  SOURCE_SKILLS_DIR="$SCRIPT_DIR/skills"
else
  TEMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'sds_install.XXXXXX' 2>/dev/null || echo "/tmp/sds_install_$$")"
  mkdir -p "$TEMP_DIR"

  if command -v git >/dev/null 2>&1; then
    echo "📥 Cloning skill package from GitHub via git..."
    git clone --depth 1 --quiet "$REPO_URL" "$TEMP_DIR/repo"
    SOURCE_SKILLS_DIR="$TEMP_DIR/repo/skills"
  elif command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    echo "📥 Fetching skill package from GitHub via curl & tar..."
    mkdir -p "$TEMP_DIR/archive"
    curl -fsSL "$ARCHIVE_URL" | tar -xz -C "$TEMP_DIR/archive"
    SOURCE_SKILLS_DIR="$TEMP_DIR/archive/system-design-studio-main/skills"
  elif command -v wget >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    echo "📥 Fetching skill package from GitHub via wget & tar..."
    mkdir -p "$TEMP_DIR/archive"
    wget -qO- "$ARCHIVE_URL" | tar -xz -C "$TEMP_DIR/archive"
    SOURCE_SKILLS_DIR="$TEMP_DIR/archive/system-design-studio-main/skills"
  else
    echo "❌ Error: git, curl, or wget with tar is required to install System Design Studio." >&2
    exit 1
  fi
fi

if [ ! -f "$SOURCE_SKILLS_DIR/$SKILL_NAME/SKILL.md" ]; then
  echo "❌ Error: Skill package could not be verified (SKILL.md missing in source)." >&2
  exit 1
fi

install_to_path() {
  target_parent="$1"
  agent_label="$2"
  
  echo "📦 Installing skills for ${agent_label}..."
  mkdir -p "$target_parent"

  # 1. Primary studio engine skill
  rm -rf "${target_parent}/${SKILL_NAME}"
  cp -R "${SOURCE_SKILLS_DIR}/${SKILL_NAME}" "${target_parent}/${SKILL_NAME}"
  chmod -R u+rwX,go+rX "${target_parent}/${SKILL_NAME}" 2>/dev/null || true
  chmod +x "${target_parent}/${SKILL_NAME}/scripts/"*.sh "${target_parent}/${SKILL_NAME}/scripts/"*.py 2>/dev/null || true

  # 2. Companion in-chat slash command skills (sds-status, sds-teach, etc.)
  local companion_count=0
  for cmd_dir in "${SOURCE_SKILLS_DIR}"/sds-*; do
    if [ -d "$cmd_dir" ]; then
      cmd_name="$(basename "$cmd_dir")"
      rm -rf "${target_parent}/${cmd_name}"
      cp -R "$cmd_dir" "${target_parent}/${cmd_name}"
      chmod -R u+rwX,go+rX "${target_parent}/${cmd_name}" 2>/dev/null || true
      companion_count=$((companion_count + 1))
    fi
  done

  if [ -f "${target_parent}/${SKILL_NAME}/SKILL.md" ]; then
    echo "   ✅ Verified system-design-studio + ${companion_count} in-chat slash commands at ${target_parent}"
  fi
}

echo ""

# 7. Execute Installations
INSTALLED_COUNT=0

# A. Google Antigravity & Agent Open Standards
if [ "$INSTALL_ANTIGRAVITY" = true ]; then
  install_to_path "$HOME_DIR/.gemini/antigravity/skills" "Google Antigravity (~/.gemini/antigravity/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  if [ -d "$HOME_DIR/.gemini/config" ] || [ "$INSTALL_ALL" = true ]; then
    install_to_path "$HOME_DIR/.gemini/config/skills" "Antigravity Global Config (~/.gemini/config/skills)"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi

  install_to_path "$HOME_DIR/.agents/skills" "Agent Skills Open Standard (~/.agents/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
fi

# B. Anthropic Claude Code
if [ "$INSTALL_CLAUDE" = true ]; then
  install_to_path "$HOME_DIR/.claude/skills" "Claude Code (~/.claude/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  # Also install into ~/.claude/commands/ for native Claude Code slash command palette
  mkdir -p "$HOME_DIR/.claude/commands"
  for cmd_dir in "${SOURCE_SKILLS_DIR}"/sds-*; do
    if [ -d "$cmd_dir" ] && [ -f "$cmd_dir/SKILL.md" ]; then
      cmd_name="$(basename "$cmd_dir")"
      cp "$cmd_dir/SKILL.md" "$HOME_DIR/.claude/commands/${cmd_name}.md" 2>/dev/null || true
    fi
  done

  if [ "$PLATFORM" = "linux" ] && [ -d "$XDG_CONFIG/claude" ]; then
    install_to_path "$XDG_CONFIG/claude/skills" "Claude Code XDG (~/.config/claude/skills)"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

# C. Cursor IDE
if [ "$INSTALL_CURSOR" = true ]; then
  install_to_path "$HOME_DIR/.cursor/skills" "Cursor IDE Global (~/.cursor/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  if [ "$PLATFORM" = "macos" ] && [ -d "$HOME_DIR/Library/Application Support/Cursor" ]; then
    install_to_path "$HOME_DIR/Library/Application Support/Cursor/User/skills" "Cursor User Library"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi

  if [ "$PLATFORM" = "linux" ] && [ -d "$XDG_CONFIG/Cursor" ]; then
    install_to_path "$XDG_CONFIG/Cursor/User/skills" "Cursor User XDG"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi

  if [ -n "${APPDATA:-}" ] && [ -d "$APPDATA/Cursor" ]; then
    install_to_path "$APPDATA/Cursor/User/skills" "Cursor Windows AppData"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

# D. OpenAI Codex / CLI Agents
if [ "$INSTALL_CODEX" = true ]; then
  install_to_path "$HOME_DIR/.codex/skills" "OpenAI Codex (~/.codex/skills)"
  INSTALLED_COUNT=$((INSTALLED_COUNT + 1))

  # Also install into ~/.codex/prompts/ for native Codex slash command palette
  mkdir -p "$HOME_DIR/.codex/prompts"
  for cmd_dir in "${SOURCE_SKILLS_DIR}"/sds-*; do
    if [ -d "$cmd_dir" ] && [ -f "$cmd_dir/SKILL.md" ]; then
      cmd_name="$(basename "$cmd_dir")"
      cp "$cmd_dir/SKILL.md" "$HOME_DIR/.codex/prompts/${cmd_name}.md" 2>/dev/null || true
    fi
  done

  if [ "$PLATFORM" = "linux" ] && [ -d "$XDG_CONFIG/codex" ]; then
    install_to_path "$XDG_CONFIG/codex/skills" "OpenAI Codex XDG"
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
  fi
fi

# Also keep an internal copy in ~/.system-design-studio/skills/system-design-studio
install_to_path "$GLOBAL_STUDIO_DIR/skills" "Central Studio Runtime (${GLOBAL_STUDIO_DIR}/skills)"

# Create convenient CLI wrapper at ~/.system-design-studio/bin/sds
cat <<'EOF' > "${GLOBAL_BIN}/sds"
#!/bin/sh
HOME_DIR="${HOME:-$USERPROFILE}"
GLOBAL_DIR="${SDS_GLOBAL_DIR:-$HOME_DIR/.system-design-studio}"
BASE_SCRIPTS="${GLOBAL_DIR}/skills/system-design-studio/scripts"

case "$1" in
  init)
    shift
    exec bash "${BASE_SCRIPTS}/init-learning-instance.sh" "$@"
    ;;
  projects|list)
    shift
    exec python3 "${BASE_SCRIPTS}/manage-projects.py" list "$@"
    ;;
  switch|open)
    shift
    exec python3 "${BASE_SCRIPTS}/manage-projects.py" switch "$@"
    ;;
  notes)
    shift
    exec python3 "${BASE_SCRIPTS}/manage-projects.py" notes "$@"
    ;;
  delete|remove|rm)
    shift
    exec python3 "${BASE_SCRIPTS}/manage-projects.py" delete "$@"
    ;;
  dashboard|tracker|serve)
    shift
    exec python3 "${BASE_SCRIPTS}/serve-dashboard.py" "$@"
    ;;
  rollback|restore|undo)
    shift
    exec python3 "${BASE_SCRIPTS}/git-checkpoint.py" rollback "$@"
    ;;
  checkpoints)
    shift
    exec python3 "${BASE_SCRIPTS}/git-checkpoint.py" list "$@"
    ;;
  curriculum)
    shift
    exec python3 "${BASE_SCRIPTS}/configure-curriculum.py" "$@"
    ;;
  config)
    shift
    exec python3 "${BASE_SCRIPTS}/merge-settings.py" "$@"
    ;;
  status)
    shift
    exec python3 "${BASE_SCRIPTS}/sync-status.py" "$@"
    ;;
  *)
    echo "============================================================================"
    echo "  SYSTEM DESIGN STUDIO CLI (sds)"
    echo "============================================================================"
    echo "Usage: sds <command> [options]"
    echo ""
    echo "Core Commands:"
    echo "  sds init [options]         Initialize or scaffold a project learning instance"
    echo "  sds dashboard [options]    Launch read-only curriculum tracker on localhost"
    echo "  sds list / projects        List registered projects, tracks, and progress"
    echo "  sds switch <id>            Switch active project context"
    echo "  sds notes [id]             List generated study notes for active project"
    echo "  sds delete <id>            Safely delete a project instance"
    echo ""
    echo "State & Safety:"
    echo "  sds rollback [--steps N]   Roll back state to a previous atomic checkpoint"
    echo "  sds checkpoints            List recent state snapshots and Git commits"
    echo "  sds curriculum [options]   Configure, prune, or reorder curriculum tracks"
    echo "  sds config [key] [val]     Inspect or dynamically update settings"
    echo "  sds status                 Display current living cursor and topic metrics"
    echo "============================================================================"
    ;;
esac
EOF
chmod +x "${GLOBAL_BIN}/sds"

echo ""
echo "=========================================================="
echo "🎉 System Design Studio skill installed across ${INSTALLED_COUNT} agent location(s)!"
echo "=========================================================="
echo ""
echo "⚙️  Global Defaults Configured:"
echo "   • Visual Theme:     ${THEME_STYLE}"
echo "   • Output Format:    ${OUTPUT_FORMAT}"
echo "   • Auto-Notes:       ${AUTO_NOTES} (${NOTES_STRUCTURE})"
echo "   • Machine Root:     ${GLOBAL_STUDIO_DIR}"
echo ""
echo "🚀 Next Step — Initialize a Learning Project:"
echo "   Skill installation and learning instance initialization are separated."
echo "   To scaffold your first learning instance, run:"
echo ""
echo "     ${GLOBAL_BIN}/sds init"
echo "   or:"
echo "     bash ${GLOBAL_STUDIO_DIR}/skills/system-design-studio/scripts/init-learning-instance.sh"
echo ""
echo "   (You can also add '${GLOBAL_BIN}' to your PATH for instant 'sds' access)."
echo "=========================================================="
