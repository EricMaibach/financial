#!/bin/bash
# Full Council Run — all agents in order, loops every 2 days.
# Run manually from a terminal: bash scripts/run-council.sh
# Keep this terminal session alive; Ctrl+C to stop.
#
# Order (critical):
#   1. Researcher
#   2. Designer Council
#   3. Engineer Council
#   4. CEO
#   5. PM Council
#
# Logs to: ~/.claude/projects/financial/logs/council-full.log

LOG_DIR="$HOME/.claude/projects/financial/logs"
LOG_FILE="$LOG_DIR/council-full.log"
REPO_DIR="$HOME/Documents/repos/financialproject/financial-pm"
SLEEP_SECONDS=$((2 * 24 * 60 * 60))  # 2 days

mkdir -p "$LOG_DIR"

run_agent() {
  local name="$1"
  local command="$2"
  echo ""
  echo "--- $name starting: $(date) ---"
  echo "" >> "$LOG_FILE"
  echo "--- $name starting: $(date) ---" >> "$LOG_FILE"
  claude --dangerously-skip-permissions -p "$command" 2>&1 | tee -a "$LOG_FILE"
  echo "--- $name done: $(date) ---"
  echo "--- $name done: $(date) ---" >> "$LOG_FILE"
}

cd "$REPO_DIR" || {
  echo "ERROR: Could not cd to $REPO_DIR"
  exit 1
}

echo "Council loop started. Running every 2 days. Ctrl+C to stop."
echo "Logs: $LOG_FILE"

while true; do
  echo ""
  echo "=================================================="
  echo "=== Full Council Run: $(date) ==="
  echo "=================================================="
  echo "" >> "$LOG_FILE"
  echo "=================================================" >> "$LOG_FILE"
  echo "=== Full Council Run: $(date) ===" >> "$LOG_FILE"
  echo "=================================================" >> "$LOG_FILE"

  run_agent "Researcher"       "/work-researcher"
  run_agent "Designer Council" "/work-designer-council"
  run_agent "Engineer Council" "/work-engineer-council"
  run_agent "CEO"              "/work-ceo"
  run_agent "PM Council"       "/work-pm-council"

  echo ""
  echo "=== Full Council Run complete: $(date) ==="
  echo "=== Sleeping 2 days. Next run: $(date -d "+2 days") ==="
  echo "=== Full Council Run complete: $(date) ===" >> "$LOG_FILE"
  echo "=== Next run: $(date -d "+2 days") ===" >> "$LOG_FILE"

  sleep "$SLEEP_SECONDS"
done
