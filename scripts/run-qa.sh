#!/bin/bash
# QA Agent — runs every 10 minutes
# Start this from within the financial-qa directory

# Pre-flight check: returns 0 if Claude should run, 1 if there's nothing to do.
qa_has_work() {
  local labels=("needs-qa-testing" "needs-test-plan" "bug")
  for label in "${labels[@]}"; do
    local count
    count=$(gh issue list --label "$label" --state open --json number 2>/dev/null | jq 'length')
    if [ "$count" -gt 0 ]; then
      echo "=== Queue hit: $count issue(s) labeled '$label' ==="
      return 0
    fi
  done

  echo "=== Skipping: no items in any QA queue ==="
  return 1
}

while true; do
  echo ""
  echo "=== QA Agent: $(date) ==="

  if qa_has_work; then
    claude --dangerously-skip-permissions -p "/work-qa"
    echo "=== QA done. Next run in 10 minutes ==="
  fi

  sleep 600
done
