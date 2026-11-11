#!/bin/bash
set -e

cd "$(dirname "$0")"

PORT=8080
LOG_DIR="logs"

mkdir -p "$LOG_DIR"

# Under launchd (non-interactive), send all script and app output to the log files
if [ ! -t 1 ]; then
    exec >> "$LOG_DIR/searchy.log" 2>> "$LOG_DIR/searchy.err.log"
fi

# Kill any existing instances on the port (lsof may return multiple PIDs)
if lsof -ti:$PORT &>/dev/null; then
    echo "Stopping existing process(es) on port $PORT..."
    kill $(lsof -ti:$PORT) 2>/dev/null || true
    sleep 1
    # Force-kill anything still hanging on
    kill -9 $(lsof -ti:$PORT) 2>/dev/null || true
    sleep 1
fi

# Recreate venv if missing
if [ ! -f venv/bin/python3 ]; then
    python3 -m venv venv --clear
    venv/bin/pip install -r requirements.txt
fi

echo "Starting Searchy on http://127.0.0.1:$PORT"

# If running interactively (terminal), launch in background so the shell is not blocked
if [ -t 1 ]; then
    nohup venv/bin/python3 app.py >> "$LOG_DIR/searchy.log" 2>&1 &
    echo "Running in background (PID $!). Logs: $LOG_DIR/searchy.log"
else
    exec venv/bin/python3 app.py
fi
