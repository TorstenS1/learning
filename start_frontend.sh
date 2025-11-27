#!/bin/bash

# ALIS Frontend Startup Script

echo "======================================"
echo "🎨 Starting ALIS Frontend"
echo "======================================"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed."
    echo ""
fi

# Start Vite dev server
echo "🚀 Starting Vite dev server..."
echo "======================================"
npm run dev
