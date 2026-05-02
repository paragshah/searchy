#!/bin/bash
set -e

cd "$(dirname "$0")"

PORT=8080

# Kill any existing instance
PID=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$PID" ]; then
    echo "Stopping existing process (PID $PID) on port $PORT..."
    kill "$PID" 2>/dev/null
    sleep 1
fi

echo "Starting Searchy on http://127.0.0.1:$PORT"
exec ./start.sh
