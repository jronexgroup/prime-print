#!/bin/bash
echo "=========================================="
echo "  Runova Print Agent Setup"
echo "=========================================="
echo

cd "$(dirname "$0")"

echo "[1/3] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Python3 not found. Install Python 3.10+"
    exit 1
fi

echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q

echo "[3/3] Starting agent..."
echo
echo "=========================================="
echo "  Enter your server URL (default: http://localhost:8000)"
echo "=========================================="
read -p "Server URL: " SERVER
if [ -z "$SERVER" ]; then
    SERVER="http://localhost:8000"
fi

python3 runova_agent.py --server "$SERVER"
