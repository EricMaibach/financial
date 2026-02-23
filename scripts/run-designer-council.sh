#!/bin/bash
# Designer Council Agent — runs daily via cron, 1 hour after Researcher
# Cron: 0 9 * * * /path/to/scripts/run-designer-council.sh
# Logs to: ~/.claude/projects/financial/logs/designer-council.log

LOG_DIR="$HOME/.claude/projects/financial/logs"
LOG_FILE="$LOG_DIR/designer-council.log"
REPO_DIR="$HOME/Documents/repos/financialproject/financial-pm"

mkdir -p "$LOG_DIR"

echo "" >> "$LOG_FILE"
echo "=== Designer Council: $(date) ===" >> "$LOG_FILE"

cd "$REPO_DIR" || {
  echo "ERROR: Could not cd to $REPO_DIR" >> "$LOG_FILE"
  exit 1
}

claude --dangerously-skip-permissions -p "/work-designer-council" >> "$LOG_FILE" 2>&1

echo "=== Designer Council done: $(date) ===" >> "$LOG_FILE"
