#!/bin/bash
# PM Agent — runs every 2 hours, no initial delay
# Start this from within the financial-pm directory

while true; do
  echo ""
  echo "=== PM Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-pm"
  echo "=== PM done. Next run in 2 hours ==="
  sleep 7200
done
