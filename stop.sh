#!/bin/bash

PORT=8080

if ! lsof -ti:$PORT &>/dev/null; then
    echo "Searchy is not running on port $PORT."
    exit 0
fi

echo "Stopping Searchy on port $PORT..."
kill $(lsof -ti:$PORT) 2>/dev/null || true
sleep 1

# Force-kill anything still hanging on
if lsof -ti:$PORT &>/dev/null; then
    kill -9 $(lsof -ti:$PORT) 2>/dev/null || true
    sleep 1
fi

if lsof -ti:$PORT &>/dev/null; then
    echo "Failed to stop Searchy."
    exit 1
fi

echo "Searchy stopped."
