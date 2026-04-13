#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -f venv/bin/python3 ]; then
    python3 -m venv venv --clear
    venv/bin/pip install -r requirements.txt
fi

exec venv/bin/python3 app.py
