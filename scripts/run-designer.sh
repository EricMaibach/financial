#!/bin/bash
# Designer Agent — runs every 3 hours, starts 2 hours after QA
# Start this from within the financial-designer directory

echo ""
echo "=== Designer Agent: waiting 2 hours before first run ==="
sleep 7200

while true; do
  echo ""
  echo "=== Designer Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-designer"
  echo "=== Designer done. Next run in 3 hours ==="
  sleep 10800
done
