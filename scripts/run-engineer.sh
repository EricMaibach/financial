#!/bin/bash
# Engineer Agent — runs every 1.5 hours, starts 30 minutes after QA
# Start this from within the financial-engineer directory

echo ""
echo "=== Engineer Agent: waiting 30 minutes before first run ==="
sleep 1800

while true; do
  echo ""
  echo "=== Engineer Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-engineer"
  echo "=== Engineer done. Next run in 1.5 hours ==="
  sleep 5400
done
