#!/bin/bash
# Engineer Agent — runs every 3 hours, starts 1 hour after QA
# Start this from within the financial-engineer directory

echo ""
echo "=== Engineer Agent: waiting 1 hour before first run ==="
sleep 3600

while true; do
  echo ""
  echo "=== Engineer Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-engineer"
  echo "=== Engineer done. Next run in 3 hours ==="
  sleep 10800
done
