#!/bin/bash
# Docker Entrypoint Script
# Runs database migrations before starting the application

set -e

echo "Running database migrations..."
flask db upgrade || {
    echo "Migration failed, but continuing (might be first run)..."
}

echo "Starting application..."
exec gunicorn -w 1 --preload -b 0.0.0.0:5000 --timeout 120 dashboard:app
