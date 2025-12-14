#!/bin/bash

# Start backend server only

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Starting backend server on http://localhost:8000"
python main.py

