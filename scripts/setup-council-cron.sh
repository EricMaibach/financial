#!/bin/bash
# One-time setup: installs council workflow cron jobs.
# Safe to re-run — checks for existing entries before adding.
# Run from any directory: bash scripts/setup-council-cron.sh

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RESEARCHER_SCRIPT="$SCRIPTS_DIR/run-researcher-council.sh"
DESIGNER_SCRIPT="$SCRIPTS_DIR/run-designer-council.sh"
WEEKLY_SCRIPT="$SCRIPTS_DIR/run-council-weekly.sh"

# Verify scripts exist
for script in "$RESEARCHER_SCRIPT" "$DESIGNER_SCRIPT" "$WEEKLY_SCRIPT"; do
  if [ ! -f "$script" ]; then
    echo "ERROR: Script not found: $script"
    exit 1
  fi
done

# Cron entries
RESEARCHER_CRON="0 8 * * * $RESEARCHER_SCRIPT"
DESIGNER_CRON="0 9 * * * $DESIGNER_SCRIPT"
WEEKLY_CRON="0 10 * * 1 $WEEKLY_SCRIPT"

# Add each entry only if not already present
CURRENT_CRONTAB=$(crontab -l 2>/dev/null || true)
NEW_CRONTAB="$CURRENT_CRONTAB"

add_if_missing() {
  local entry="$1"
  local script_path="$2"
  if echo "$CURRENT_CRONTAB" | grep -qF "$script_path"; then
    echo "Already installed: $script_path"
  else
    NEW_CRONTAB="${NEW_CRONTAB}"$'\n'"${entry}"
    echo "Adding: $entry"
  fi
}

add_if_missing "$RESEARCHER_CRON"  "$RESEARCHER_SCRIPT"
add_if_missing "$DESIGNER_CRON"    "$DESIGNER_SCRIPT"
add_if_missing "$WEEKLY_CRON"      "$WEEKLY_SCRIPT"

echo "$NEW_CRONTAB" | crontab -

echo ""
echo "Done. Current crontab:"
crontab -l
