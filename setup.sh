#!/usr/bin/env bash
set -euo pipefail

# ☤ xrpl-hermes — one-command setup
# Usage: bash setup.sh

echo "☤ xrpl-hermes setup"
echo "━━━━━━━━━━━━━━━━━━"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Install Python 3.10+ first."
    exit 1
fi
echo "✓ python3 $(python3 --version | cut -d' ' -f2)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created (.venv)"
else
    echo "✓ Virtual environment exists (.venv)"
fi

# Activate and install
source .venv/bin/activate
pip install --quiet --upgrade pip setuptools
pip install --quiet -r requirements.txt
echo "✓ Dependencies installed"

# Make scripts executable
chmod +x scripts/xrpl_tools.py 2>/dev/null || true

# Verify
echo ""
echo "━━━ Verification ━━━"
python3 -c "import xrpl; print('✓ xrpl-py', xrpl.__version__)"
python3 -c "import httpx; print('✓ httpx', httpx.__version__)"

echo ""
echo "☤ Setup complete. Activate with: source .venv/bin/activate"
