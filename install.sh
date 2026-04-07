#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Creating virtual environment..."
python3 -m venv venv --clear

echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Initializing database..."
python3 -c "from db import init_db; init_db()"

echo ""
echo "Setup complete!"

# --- Optional LaunchAgent for auto-start ---
PLIST_LABEL="com.searchy.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
INSTALL_DIR="$(pwd)"

read -p "Would you like Searchy to start automatically on login? [y/N] " AUTO_START

if [[ "$AUTO_START" =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/Library/LaunchAgents"

    cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/venv/bin/python3</string>
        <string>${INSTALL_DIR}/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${INSTALL_DIR}/searchy.log</string>
    <key>StandardErrorPath</key>
    <string>${INSTALL_DIR}/searchy.err.log</string>
</dict>
</plist>
EOF

    launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

    echo "LaunchAgent installed and loaded. Searchy will start on login."
    echo "  Plist: $PLIST_PATH"
    echo "  Logs:  ${INSTALL_DIR}/searchy.log"
    echo ""
    echo "To stop:   launchctl bootout gui/$(id -u) $PLIST_PATH"
    echo "To start:  launchctl bootstrap gui/$(id -u) $PLIST_PATH"
else
    echo "To run Searchy manually:"
    echo "  ./venv/bin/python3 app.py"
fi

echo ""
echo "Then open http://localhost:8080"
