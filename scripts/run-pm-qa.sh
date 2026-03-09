#!/bin/bash
# PM Q&A Agent — runs every 15 minutes, no initial delay
# Start this from within the financial-pm directory

while true; do
  echo ""
  echo "=== PM Q&A Agent: $(date) ==="

  PENDING=$(gh api graphql \
    -f query='{ repository(owner: "EricMaibach", name: "fianancial-council") { discussions(first: 30, categoryId: "DIC_kwDORXrB_s4C3MjM", states: [OPEN]) { nodes { comments(first: 30) { nodes { body author { login } } } } } } }' \
    2>/dev/null | jq '[
      .data.repository.discussions.nodes[] |
      select(
        (.comments.nodes | length == 0) or
        (.comments.nodes | last | .body | startswith("PM:") | not)
      )
    ] | length')

  if [ "${PENDING:-0}" -eq 0 ]; then
    echo "=== No pending PM questions. Skipping Claude. Next run in 15 minutes ==="
  else
    echo "=== Found ${PENDING} discussion(s) needing a response. Invoking Claude... ==="
    claude --dangerously-skip-permissions -p "/work-pm-qa"
    echo "=== PM Q&A done. Next run in 15 minutes ==="
  fi

  sleep 900
done
