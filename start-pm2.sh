#!/bin/bash
# Bash script to start PM2 services
# Run from project root directory

echo "🚀 Starting Chatbot Services with PM2..."

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed. Install it with: npm install -g pm2"
    exit 1
fi

# Check if frontend is built
if [ ! -d "apps/frontend/.next" ]; then
    echo "⚠️  Frontend build not found. Building frontend..."
    cd apps/frontend
    npm run build
    if [ $? -ne 0 ]; then
        echo "❌ Frontend build failed!"
        exit 1
    fi
    cd ../..
    echo "✅ Frontend built successfully!"
fi

# Check if backend venv exists
if [ ! -d "apps/backend/venv" ]; then
    echo "⚠️  Backend virtual environment not found. Creating..."
    cd apps/backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ../..
    echo "✅ Backend virtual environment created!"
fi

# Create logs directory
mkdir -p logs

# Stop existing processes
echo "🛑 Stopping existing PM2 processes..."
pm2 stop all 2>/dev/null
pm2 delete all 2>/dev/null

# Start with PM2
echo "▶️  Starting services with PM2..."
pm2 start pm2.ecosystem.config.js

# Show status
echo ""
echo "📊 PM2 Status:"
pm2 status

echo ""
echo "✅ Services started! Use 'pm2 logs' to view logs"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:3000"



