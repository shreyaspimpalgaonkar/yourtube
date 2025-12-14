#!/bin/bash

# Start frontend server only

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🚀 Starting frontend server on http://localhost:3000"
npm run dev

