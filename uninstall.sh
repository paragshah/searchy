#!/bin/bash
set -e

cd "$(dirname "$0")"
INSTALL_DIR="$(pwd)"

PLIST_LABEL="com.searchy.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
DB_FILE="searchy.db"
BACKUP_DIR="searchy-db-backup"

echo "=== Searchy Uninstaller ==="
echo ""

# --- Stop the LaunchAgent ---
if [ -f "$PLIST_PATH" ]; then
    echo "Stopping and removing LaunchAgent..."
    launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    echo "  LaunchAgent removed."
else
    echo "No LaunchAgent found at $PLIST_PATH, skipping."
fi

# --- Kill any running Searchy process ---
echo "Stopping any running Searchy processes..."
PIDS=$(pgrep -f "python3.*app\.py" 2>/dev/null | grep -v "^$$\$" || true)
if [ -n "$PIDS" ]; then
    # Only kill processes whose working directory or command line references this install
    for PID in $PIDS; do
        CMD=$(ps -p "$PID" -o args= 2>/dev/null || true)
        if echo "$CMD" | grep -q "$INSTALL_DIR"; then
            kill "$PID" 2>/dev/null || true
            echo "  Stopped process $PID."
        fi
    done
else
    echo "  No running Searchy processes found."
fi

# --- Back up and remove the database ---
if [ -f "$DB_FILE" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    DEST="${BACKUP_DIR}/${DB_FILE}.${TIMESTAMP}"
    mkdir -p "$BACKUP_DIR"
    cp "$DB_FILE" "$DEST"
    echo "Database backed up to: $DEST"
    rm -f "$DB_FILE"
    echo "Database deleted."
else
    echo "No database file found, skipping backup."
fi

# --- Remove virtual environment ---
if [ -d "venv" ]; then
    echo "Removing virtual environment..."
    rm -rf venv
    echo "  Virtual environment removed."
fi

# --- Remove generated caches and logs ---
rm -rf __pycache__
rm -f searchy.log searchy.err.log

echo ""
echo "Uninstall complete. Source files have been left in place."
echo "Database backup location: ${INSTALL_DIR}/${BACKUP_DIR}/"
