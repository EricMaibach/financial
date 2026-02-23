#!/bin/bash
# Researcher Council Agent — runs daily via cron
# Cron: 0 8 * * * /path/to/scripts/run-researcher-council.sh
# Logs to: ~/.claude/projects/financial/logs/researcher-council.log

LOG_DIR="$HOME/.claude/projects/financial/logs"
LOG_FILE="$LOG_DIR/researcher-council.log"
REPO_DIR="$HOME/Documents/repos/financialproject/financial-pm"

mkdir -p "$LOG_DIR"

echo "" >> "$LOG_FILE"
echo "=== Researcher Council: $(date) ===" >> "$LOG_FILE"

cd "$REPO_DIR" || {
  echo "ERROR: Could not cd to $REPO_DIR" >> "$LOG_FILE"
  exit 1
}

claude --dangerously-skip-permissions -p "/work-researcher" >> "$LOG_FILE" 2>&1

echo "=== Researcher Council done: $(date) ===" >> "$LOG_FILE"
