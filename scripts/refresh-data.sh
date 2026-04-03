#!/usr/bin/env bash
# Manually trigger the daily data refresh via the running container's API.
# Usage: bash scripts/refresh-data.sh [host:port]

set -euo pipefail

BASE_URL="${1:-http://192.168.1.48:5000}"

echo "Triggering data refresh on ${BASE_URL}..."
curl -sf -X POST "${BASE_URL}/api/reload-data" | python3 -m json.tool

echo ""
echo "Polling reload status..."
while true; do
    status=$(curl -sf "${BASE_URL}/api/reload-status")
    running=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('running', False))")
    step=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('current_step', 'unknown'))")

    echo "  [$step] running=$running"

    if [ "$running" = "False" ]; then
        echo ""
        echo "Data refresh complete."
        echo "$status" | python3 -m json.tool
        break
    fi

    sleep 10
done
