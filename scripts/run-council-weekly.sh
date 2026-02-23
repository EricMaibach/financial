#!/bin/bash
# Council Weekly — CEO then PM, runs every Monday via cron
# Order is critical: CEO must complete before PM runs.
# Cron: 0 10 * * 1 /path/to/scripts/run-council-weekly.sh
# Logs to: ~/.claude/projects/financial/logs/council-weekly.log

LOG_DIR="$HOME/.claude/projects/financial/logs"
LOG_FILE="$LOG_DIR/council-weekly.log"
REPO_DIR="$HOME/Documents/repos/financialproject/financial-pm"

mkdir -p "$LOG_DIR"

echo "" >> "$LOG_FILE"
echo "=== Council Weekly: $(date) ===" >> "$LOG_FILE"

cd "$REPO_DIR" || {
  echo "ERROR: Could not cd to $REPO_DIR" >> "$LOG_FILE"
  exit 1
}

echo "--- CEO running ---" >> "$LOG_FILE"
claude --dangerously-skip-permissions -p "/work-ceo" >> "$LOG_FILE" 2>&1
echo "--- CEO done: $(date) ---" >> "$LOG_FILE"

echo "--- PM Council running ---" >> "$LOG_FILE"
claude --dangerously-skip-permissions -p "/work-pm-council" >> "$LOG_FILE" 2>&1
echo "--- PM Council done: $(date) ---" >> "$LOG_FILE"

echo "=== Council Weekly complete: $(date) ===" >> "$LOG_FILE"
