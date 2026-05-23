#!/bin/bash
# jazz-voicing-engine quickstart — arrange Autumn Leaves
set -e
echo "🎹 Jazz Voicing Engine — Quick Start"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pip install -e . --quiet 2>/dev/null || true

export PYTHONPATH="$SCRIPT_DIR"
python3 examples/jazz_arrangement.py
echo "✅ jazz-voicing-engine works!"
