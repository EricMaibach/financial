#!/bin/bash
# Designer Agent — runs every 30 minutes, starts 20 minutes after QA
# Start this from within the financial-designer directory

echo ""
echo "=== Designer Agent: waiting 20 minutes before first run ==="
sleep 1200

while true; do
  echo ""
  echo "=== Designer Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-designer"
  echo "=== Designer done. Next run in 30 minutes ==="
  sleep 1800
done
