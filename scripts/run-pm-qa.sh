#!/bin/bash
# PM Q&A Agent — runs every 2 hours, no initial delay
# Start this from within the financial-pm directory

while true; do
  echo ""
  echo "=== PM Q&A Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-pm-qa"
  echo "=== PM Q&A done. Next run in 2 hours ==="
  sleep 7200
done
