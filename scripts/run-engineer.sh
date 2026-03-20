#!/bin/bash
# Engineer Agent — runs every 5 minutes, starts 5 minutes after launch
# Start this from within the financial-engineer directory

# Pre-flight check: returns 0 if Claude should run, 1 if there's nothing to do.
engineer_has_work() {
  # Condition 1: open PRs — Engineer stops immediately if any exist
  local open_prs
  open_prs=$(gh pr list --state open --json number 2>/dev/null | jq 'length')
  if [ "$open_prs" -gt 0 ]; then
    echo "=== Skipping: $open_prs open PR(s) exist — waiting for human merge ==="
    return 1
  fi

  # Condition 2: at least one item in any engineer queue
  local labels=("needs-design-changes" "needs-fixes" "ready-for-pr" "ready-for-implementation")
  for label in "${labels[@]}"; do
    local count
    count=$(gh issue list --label "$label" --state open --json number 2>/dev/null | jq 'length')
    if [ "$count" -gt 0 ]; then
      echo "=== Queue hit: $count issue(s) labeled '$label' ==="
      return 0
    fi
  done

  echo "=== Skipping: no items in any engineer queue ==="
  return 1
}

echo ""
echo "=== Engineer Agent: waiting 5 minutes before first run ==="
sleep 300

while true; do
  echo ""
  echo "=== Engineer Agent: $(date) ==="

  if engineer_has_work; then
    claude --dangerously-skip-permissions -p "/work-engineer"
    echo "=== Engineer done. Next run in 5 minutes ==="
  fi

  sleep 300
done
