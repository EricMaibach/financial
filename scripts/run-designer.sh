#!/bin/bash
# Designer Agent — runs every 10 minutes, starts 20 minutes after QA
# Start this from within the financial-designer directory

# Pre-flight check: returns 0 if Claude should run, 1 if there's nothing to do.
designer_has_work() {
  local labels=("needs-design-review" "needs-design-spec")
  for label in "${labels[@]}"; do
    local count
    count=$(gh issue list --label "$label" --state open --json number 2>/dev/null | jq 'length')
    if [ "$count" -gt 0 ]; then
      echo "=== Queue hit: $count issue(s) labeled '$label' ==="
      return 0
    fi
  done

  echo "=== Skipping: no items in any Designer queue ==="
  return 1
}

echo ""
echo "=== Designer Agent: waiting 20 minutes before first run ==="
sleep 1200

while true; do
  echo ""
  echo "=== Designer Agent: $(date) ==="

  if designer_has_work; then
    claude --dangerously-skip-permissions -p "/work-designer"
    echo "=== Designer done. Next run in 10 minutes ==="
  fi

  sleep 600
done
