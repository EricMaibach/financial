#!/bin/bash
# QA Agent — runs every 30 minutes
# Start this from within the financial-qa directory

while true; do
  echo ""
  echo "=== QA Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-qa"
  echo "=== QA done. Next run in 30 minutes ==="
  sleep 1800
done
