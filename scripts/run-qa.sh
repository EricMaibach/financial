#!/bin/bash
# QA Agent — runs every 3 hours
# Start this from within the financial-qa directory

while true; do
  echo ""
  echo "=== QA Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-qa"
  echo "=== QA done. Next run in 3 hours ==="
  sleep 10800
done
