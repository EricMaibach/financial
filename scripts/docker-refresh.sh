#!/bin/bash
# Docker Refresh Script
# Completely clears Docker state and rebuilds from .env
# Use this whenever you update .env file and need changes to take effect

set -e  # Exit on any error

echo "🧹 Stopping and removing containers..."
docker compose down -v 2>/dev/null || true

echo "🗑️  Removing old images..."
docker compose rm -f 2>/dev/null || true
docker rmi financial-signaltrackers 2>/dev/null || true

echo "💨 Clearing Docker build cache..."
docker builder prune -f

echo "🔧 Rebuilding and starting fresh..."
docker compose up -d --build --force-recreate

echo "⏳ Waiting for container to be healthy..."
sleep 5

echo ""
echo "✅ Done! Container recreated with fresh environment variables."
echo ""
echo "📋 Verify your environment variables:"
docker exec signaltrackers env | grep -E "(ANTHROPIC_API_KEY|OPENAI_API_KEY|MAIL_)" | sort
