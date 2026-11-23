#!/bin/sh
# System Design Studio — Learning Instance Initializer (v3.2)
# Scaffolds an isolated learning instance in default (~/.system-design-studio/projects/<name>)
# or custom workspace locations, with curated curriculum tracks, project-scoped notes,
# and automatic registration in the central multi-project registry.
#
# POSIX sh compliant for macOS, Linux, BSD, and Windows (Git Bash/WSL).
set -e
(set -o pipefail) 2>/dev/null && set -o pipefail || true

HOME_DIR="${HOME:-}"
if [ -z "$HOME_DIR" ] && [ -n "${USERPROFILE:-}" ]; then
  HOME_DIR="$USERPROFILE"
fi
GLOBAL_STUDIO_DIR="${SDS_GLOBAL_DIR:-$HOME_DIR/.system-design-studio}"
GLOBAL_CONFIG="${GLOBAL_STUDIO_DIR}/config.json"

SCRIPT_PATH="${0:-}"
SCRIPT_DIR=""
if [ -n "$SCRIPT_PATH" ] && [ -f "$SCRIPT_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" 2>/dev/null && pwd || echo "")"
fi
RESOURCES_DIR="${SCRIPT_DIR}/../resources"

echo "=========================================================="
echo "  System Design Studio — Learning Instance Initializer   "
echo "=========================================================="

# Default fallbacks
PROJECT_NAME="System Design Study"
PROJECT_ID="system-design-study"
TARGET_DIR=""
NOTES_DIR=""
NOTES_STRUCTURE="per-topic"
CHOSEN_TRACK="full-mastery"
BYO_FILE=""
THEME_STYLE="slate-clean"
OUTPUT_FORMAT="html"
AUTO_NOTES="true"
INTERACTIVE=true

# Read defaults from global config if available
if [ -f "$GLOBAL_CONFIG" ] && command -v python3 >/dev/null 2>&1; then
  THEME_STYLE="$(python3 -c "import json; print(json.load(open('$GLOBAL_CONFIG')).get('artifactStyle', 'slate-clean'))" 2>/dev/null || echo "slate-clean")"
  OUTPUT_FORMAT="$(python3 -c "import json; print(json.load(open('$GLOBAL_CONFIG')).get('outputType', 'html'))" 2>/dev/null || echo "html")"
  NOTES_STRUCTURE="$(python3 -c "import json; print(json.load(open('$GLOBAL_CONFIG')).get('notesStructure', 'per-topic'))" 2>/dev/null || echo "per-topic")"
  AUTO_NOTES="$(python3 -c "import json; print(str(json.load(open('$GLOBAL_CONFIG')).get('autoGenerateNotes', True)).lower())" 2>/dev/null || echo "true")"
fi

# Parse CLI flags
while [ $# -gt 0 ]; do
  case "$1" in
    --name=*)
      PROJECT_NAME="${1#*=}"
      ;;
    --name)
      shift; PROJECT_NAME="$1"
      ;;
    --id=*)
      PROJECT_ID="${1#*=}"
      EXPLICIT_ID=true
      ;;
    --id)
      shift; PROJECT_ID="$1"
      EXPLICIT_ID=true
      ;;
    --path=*)
      TARGET_DIR="${1#*=}"
      ;;
    --path)
      shift; TARGET_DIR="$1"
      ;;
    --track=*)
      CHOSEN_TRACK="${1#*=}"
      ;;
    --track)
      shift; CHOSEN_TRACK="$1"
      ;;
    --byo=*)
      BYO_FILE="${1#*=}"
      ;;
    --byo)
      shift; BYO_FILE="$1"
      ;;
    --notes-dir=*)
      NOTES_DIR="${1#*=}"
      ;;
    --notes-dir)
      shift; NOTES_DIR="$1"
      ;;
    --notes-structure=*)
      NOTES_STRUCTURE="${1#*=}"
      ;;
    --notes-structure)
      shift; NOTES_STRUCTURE="$1"
      ;;
    --theme=*)
      THEME_STYLE="${1#*=}"
      ;;
    --theme)
      shift; THEME_STYLE="$1"
      ;;
    --output=*)
      OUTPUT_FORMAT="${1#*=}"
      ;;
    --output)
      shift; OUTPUT_FORMAT="$1"
      ;;
    --notes=*)
      AUTO_NOTES="${1#*=}"
      ;;
    --notes)
      shift; AUTO_NOTES="$1"
      ;;
    --defaults|--non-interactive|-y)
      INTERACTIVE=false
      ;;
    --help|-h)
      echo "Usage: init-learning-instance.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --name <str>             Project display name"
      echo "  --id <str>               Project unique identifier (slug)"
      echo "  --path <dir>             Target directory (default: ~/.system-design-studio/projects/<name>)"
      echo "  --track <track>          Curated track (full-mastery, interview-sprint, distributed-systems, staff-architect, mobile-offline)"
      echo "  --byo <file.md>          Bring-Your-Own markdown curriculum file"
      echo "  --notes-dir <dir>        Custom notes directory"
      echo "  --notes-structure <str>  per-topic (default) | per-cluster | per-tier | single-file"
      echo "  --theme <id>             slate-clean, editorial-paper, midnight-neon, nordic-frost, warm-amber"
      echo "  --output <type>          html (default) | markdown"
      echo "  --notes <bool>           true | false (auto-generate discussion notes)"
      echo "  --defaults, -y           Non-interactive, use defaults"
      exit 0
      ;;
    *)
      # Treat bare argument as project name
      if [ -z "$TARGET_DIR" ] && [ -n "$1" ]; then
        PROJECT_NAME="$1"
      fi
      ;;
  esac
  shift
done

# Validate visual preferences to prevent invalid settings
case "$THEME_STYLE" in
  slate-clean|editorial-paper|midnight-neon|nordic-frost|warm-amber)
    ;;
  *)
    echo "⚠️  Warning: Unknown theme '$THEME_STYLE'. Falling back to 'slate-clean'."
    THEME_STYLE="slate-clean"
    ;;
esac

case "$OUTPUT_FORMAT" in
  html|markdown)
    ;;
  md)
    OUTPUT_FORMAT="markdown"
    ;;
  *)
    echo "⚠️  Warning: Unknown output format '$OUTPUT_FORMAT'. Falling back to 'html'."
    OUTPUT_FORMAT="html"
    ;;
esac

case "$AUTO_NOTES" in
  true|false)
    ;;
  1|yes|y)
    AUTO_NOTES="true"
    ;;
  0|no|n)
    AUTO_NOTES="false"
    ;;
  *)
    AUTO_NOTES="true"
    ;;
esac

case "$NOTES_STRUCTURE" in
  per-topic|per-cluster|per-tier|single-file)
    ;;
  *)
    NOTES_STRUCTURE="per-topic"
    ;;
esac

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

# Clean up project ID if not explicitly passed
if [ "${EXPLICIT_ID:-false}" != true ]; then
  PROJECT_ID="$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')"
fi
[ -z "$PROJECT_ID" ] && PROJECT_ID="system-design-study"

# Interactive Wizard
if [ "$INTERACTIVE" = true ]; then
  echo ""
  echo "👉 Step 1: Project Identity"
  printf "   Project Name [%s]: " "$PROJECT_NAME"
  read_input input_name
  if [ -n "$input_name" ]; then
    PROJECT_NAME="$input_name"
    PROJECT_ID="$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')"
  fi

  echo ""
  echo "👉 Step 2: Project Workspace Location"
  DEFAULT_PROJ_LOC="${GLOBAL_STUDIO_DIR}/projects/${PROJECT_ID}"
  echo "   [1] Current Directory ($(pwd)) [Recommended]"
  echo "   [2] Default Studio Directory (${DEFAULT_PROJ_LOC})"
  echo "   [3] Custom Path"
  printf "   Select location [1]: "
  read_input input_loc
  case "$input_loc" in
    2)
      TARGET_DIR="$DEFAULT_PROJ_LOC"
      ;;
    3)
      printf "   Enter custom directory path: "
      read_input custom_dir
      TARGET_DIR="$custom_dir"
      ;;
    *)
      TARGET_DIR="$(pwd)"
      ;;
  esac

  echo ""
  echo "👉 Step 3: Project Notes Location"
  echo "   [1] Default Project Notes (<project>/notes) [Recommended]"
  echo "   [2] Custom Directory (e.g. Obsidian Vault, external folder)"
  printf "   Select notes location [1]: "
  read_input input_notes_loc
  case "$input_notes_loc" in
    2)
      printf "   Enter custom notes path: "
      read_input custom_notes
      NOTES_DIR="$custom_notes"
      ;;
    *)
      NOTES_DIR="" # Will resolve to <project>/notes
      ;;
  esac

  echo ""
  echo "👉 Step 4: Notes Structuring Strategy"
  echo "   [1] Per-Topic Files (notes/<tier>/<cluster>/<topic>.md) [Default]"
  echo "   [2] Per-Cluster Files (notes/<tier>/<cluster>.md)"
  echo "   [3] Per-Tier Files (notes/tier-<N>.md)"
  echo "   [4] Single Master File (notes/SYSTEM-DESIGN-NOTES.md)"
  printf "   Select structuring mode [1]: "
  read_input input_struct
  case "$input_struct" in
    2) NOTES_STRUCTURE="per-cluster" ;;
    3) NOTES_STRUCTURE="per-tier" ;;
    4) NOTES_STRUCTURE="single-file" ;;
    *) NOTES_STRUCTURE="per-topic" ;;
  esac

  echo ""
  echo "👉 Step 5: Curriculum Track Selection"
  echo "   [1] Full 50-Cluster Systems Mastery (Comprehensive 50 clusters, 354 topics) [Default]"
  echo "   [2] Short-Term Interview Sprint (15 High-Yield clusters, 114 topics)"
  echo "   [3] Distributed Systems & Storage Deep-Dive (23 clusters, 171 topics)"
  echo "   [4] Staff+ / Principal Architecture & System Defense (25 clusters, 184 topics)"
  echo "   [5] Mobile & Offline-First Systems (16 clusters, 113 topics)"
  echo "   [6] Bring Your Own Syllabus (BYO Markdown File)"
  printf "   Select curriculum track [1]: "
  read_input input_track
  case "$input_track" in
    2) CHOSEN_TRACK="interview-sprint" ;;
    3) CHOSEN_TRACK="distributed-systems" ;;
    4) CHOSEN_TRACK="staff-architect" ;;
    5) CHOSEN_TRACK="mobile-offline" ;;
    6)
      printf "   Enter path to your markdown syllabus file: "
      read_input input_byo
      BYO_FILE="$input_byo"
      ;;
    *) CHOSEN_TRACK="full-mastery" ;;
  esac
fi

# Fallback default path if empty
if [ -z "$TARGET_DIR" ]; then
  if [ "$(pwd)" = "$HOME_DIR" ]; then
    TARGET_DIR="${GLOBAL_STUDIO_DIR}/projects/${PROJECT_ID}"
  else
    TARGET_DIR="$(pwd)"
  fi
fi

# Resolve notes directory
if [ -z "$NOTES_DIR" ]; then
  RESOLVED_NOTES_DIR="${TARGET_DIR}/notes"
else
  RESOLVED_NOTES_DIR="$NOTES_DIR"
fi

INSTANCE_DIR="${TARGET_DIR}/.system-design"
LESSONS_DIR="${INSTANCE_DIR}/lessons"

echo ""
echo "🚀 Initializing project at ${TARGET_DIR}..."
mkdir -p "${LESSONS_DIR}"
mkdir -p "${RESOLVED_NOTES_DIR}"

# 1. Generate or Import Curriculum & Manifest
if [ -n "$BYO_FILE" ] && [ -f "$BYO_FILE" ]; then
  echo "📥 Importing custom syllabus from ${BYO_FILE}..."
  python3 "${SCRIPT_DIR}/import-curriculum.py" \
    --input "$BYO_FILE" \
    --instance-dir "$INSTANCE_DIR" \
    --title "$PROJECT_NAME" \
    --auto-fix
elif [ -f "${SCRIPT_DIR}/configure-curriculum.py" ]; then
  echo "🎯 Configuring track '${CHOSEN_TRACK}'..."
  python3 "${SCRIPT_DIR}/configure-curriculum.py" \
    --track "$CHOSEN_TRACK" \
    --output-dir "$INSTANCE_DIR" \
    --title "$PROJECT_NAME"
else
  # Fallback copy
  cp "${RESOURCES_DIR}/CURRICULUM-template.md" "${INSTANCE_DIR}/CURRICULUM.md"
  cp "${RESOURCES_DIR}/manifest-template.json" "${INSTANCE_DIR}/manifest.json"
fi

# 2. CURSOR.md
if [ -f "${RESOURCES_DIR}/CURSOR-template.md" ]; then
  cp "${RESOURCES_DIR}/CURSOR-template.md" "${INSTANCE_DIR}/CURSOR.md"
fi

# 3. settings.json
cat <<EOF > "${INSTANCE_DIR}/settings.json"
{
  "\$schemaVersion": "3.2",
  "projectId": "${PROJECT_ID}",
  "projectName": "${PROJECT_NAME}",
  "track": "${CHOSEN_TRACK}",
  "artifactStyle": "${THEME_STYLE}",
  "outputType": "${OUTPUT_FORMAT}",
  "autoGenerateNotes": ${AUTO_NOTES},
  "notesStructure": "${NOTES_STRUCTURE}",
  "paths": {
    "instanceDir": ".system-design",
    "cursorDir": ".system-design",
    "lessonsDir": ".system-design/lessons",
    "notesDir": "${RESOLVED_NOTES_DIR}"
  },
  "deliveryMode": "strictly-artifact-first",
  "inlineDiscussions": true
}
EOF

# Merge with settings template if present to guarantee style lists
if [ -f "${RESOURCES_DIR}/settings-template.json" ] && [ -f "${SCRIPT_DIR}/merge-settings.py" ]; then
  python3 "${SCRIPT_DIR}/merge-settings.py" \
    --current "${INSTANCE_DIR}/settings.json" \
    --template "${RESOURCES_DIR}/settings-template.json" \
    --output "${INSTANCE_DIR}/settings.json"
fi

# 4. DECISIONS.md
if [ ! -f "${INSTANCE_DIR}/DECISIONS.md" ]; then
  cat <<EOF > "${INSTANCE_DIR}/DECISIONS.md"
# Architecture Decision Records (ADRs)

*No decisions accepted yet. Decisions will be recorded as architectural trade-offs are evaluated and defended in workshops.*
EOF
fi

# 5. Register in Central Multi-Project Registry
if [ -f "${SCRIPT_DIR}/manage-projects.py" ]; then
  python3 "${SCRIPT_DIR}/manage-projects.py" register \
    --id "$PROJECT_ID" \
    --name "$PROJECT_NAME" \
    --path "$TARGET_DIR" \
    --track "$CHOSEN_TRACK" \
    --notes-dir "$RESOLVED_NOTES_DIR" \
    --notes-structure "$NOTES_STRUCTURE" \
    --set-active
fi

# 6. Record Initial Git Checkpoint if inside Git repository
if [ -f "${SCRIPT_DIR}/git-checkpoint.py" ]; then
  python3 "${SCRIPT_DIR}/git-checkpoint.py" commit \
    --instance-dir "${INSTANCE_DIR}" \
    --type curriculum \
    --subject "initialize learning project '${PROJECT_NAME}' (track: ${CHOSEN_TRACK})" >/dev/null 2>&1 || true
fi

echo ""
echo "============================================================================"
echo "  🎉 Project Initialized Successfully!"
echo "============================================================================"
echo "  • Project Name:     ${PROJECT_NAME} (${PROJECT_ID})"
echo "  • Workspace Path:   ${TARGET_DIR}"
echo "  • Curriculum Track: ${CHOSEN_TRACK}"
echo "  • Study Notes:      ${RESOLVED_NOTES_DIR} (${NOTES_STRUCTURE})"
echo "  • Output Mode:      ${OUTPUT_FORMAT} (Theme: ${THEME_STYLE})"
echo "----------------------------------------------------------------------------"
echo "  🚀 Interactive Workbench:"
echo "     sds dashboard    ➔ Launch read-only progress tracker (http://localhost:8420)"
echo ""
echo "  💬 Pure In-Chat Workflow:"
echo "     /sds-status      ➔ Check current living cursor & focus topic"
echo "     /sds-teach       ➔ Deliver the active topic lesson & simulator"
echo "     (Reply in chat)  ➔ Defend physical invariants directly in chat"
echo "     /sds-complete    ➔ Seal verified mastery into Git with auto-notes"
echo "============================================================================"
