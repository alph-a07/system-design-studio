#!/usr/bin/env bash
# ==============================================================================
# System Design Studio — Launch Dashboard for Dummy Project
# Launches the interactive curriculum studio & workbench loaded with mock data
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DUMMY_DIR="${SCRIPT_DIR}/dummy-project/.system-design"
DASHBOARD_SCRIPT="${SCRIPT_DIR}/skills/system-design-studio/scripts/serve-dashboard.py"

if [ ! -d "$DUMMY_DIR" ]; then
  echo "❌ Error: Dummy project directory not found at: $DUMMY_DIR" >&2
  exit 1
fi

if [ ! -f "$DASHBOARD_SCRIPT" ]; then
  echo "❌ Error: serve-dashboard.py not found at: $DASHBOARD_SCRIPT" >&2
  exit 1
fi

echo "============================================================================"
echo "  🚀 SYSTEM DESIGN STUDIO — DUMMY PROJECT WORKBENCH"
echo "============================================================================"
echo "📁 Project Directory: ${SCRIPT_DIR}/dummy-project"
echo "🎯 Instance Path:     ${DUMMY_DIR}"
echo "🌐 Launching Dashboard on http://127.0.0.1:8420..."
echo "============================================================================"
echo ""

exec python3 "$DASHBOARD_SCRIPT" --instance-dir "$DUMMY_DIR" "$@"
