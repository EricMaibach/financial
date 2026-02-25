#!/bin/bash
# Engineer Agent — runs every 30 minutes, starts 10 minutes after QA
# Start this from within the financial-engineer directory

echo ""
echo "=== Engineer Agent: waiting 10 minutes before first run ==="
sleep 600

while true; do
  echo ""
  echo "=== Engineer Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-engineer"
  echo "=== Engineer done. Next run in 30 minutes ==="
  sleep 1800
done
