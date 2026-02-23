#!/bin/bash
# Designer Agent — runs every 1.5 hours, starts 1 hour after QA
# Start this from within the financial-designer directory

echo ""
echo "=== Designer Agent: waiting 1 hour before first run ==="
sleep 3600

while true; do
  echo ""
  echo "=== Designer Agent: $(date) ==="
  claude --dangerously-skip-permissions -p "/work-designer"
  echo "=== Designer done. Next run in 1.5 hours ==="
  sleep 5400
done
