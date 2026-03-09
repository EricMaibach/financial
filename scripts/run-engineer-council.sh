#!/bin/bash
# Engineer Council Agent — runs daily via cron
# Cron: 30 10 * * * /path/to/scripts/run-engineer-council.sh
# Logs to: ~/.claude/projects/financial/logs/engineer-council.log

LOG_DIR="$HOME/.claude/projects/financial/logs"
LOG_FILE="$LOG_DIR/engineer-council.log"
REPO_DIR="$HOME/Documents/repos/financialproject/financial-pm"

mkdir -p "$LOG_DIR"

echo "" >> "$LOG_FILE"
echo "=== Engineer Council: $(date) ===" >> "$LOG_FILE"

cd "$REPO_DIR" || {
  echo "ERROR: Could not cd to $REPO_DIR" >> "$LOG_FILE"
  exit 1
}

# Phase guard — council pauses during BUILDING
ROADMAP="$REPO_DIR/docs/PRODUCT_ROADMAP.md"
PHASE_STATE=$(grep "^\*\*State:\*\*" "$ROADMAP" | awk '{print $2}')
if [ "$PHASE_STATE" = "BUILDING" ]; then
  echo "Phase is BUILDING — council paused. Exiting." >> "$LOG_FILE"
  exit 0
fi

claude --dangerously-skip-permissions -p "/work-engineer-council" >> "$LOG_FILE" 2>&1

echo "=== Engineer Council done: $(date) ===" >> "$LOG_FILE"
