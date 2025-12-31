#!/bin/bash

# Setup script for Domain-Restricted Chatbot Platform

set -e

echo "🚀 Setting up Domain-Restricted Chatbot Platform..."

# Backend setup
echo "📦 Setting up backend..."
cd apps/backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
alembic upgrade head

echo "✅ Backend setup complete!"

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "Building frontend..."
npm run build

echo "✅ Frontend setup complete!"

cd ../..

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create an admin user: cd apps/backend && python create_admin.py"
echo "2. Set up environment variables (see .env.example files)"
echo "3. Start with PM2: pm2 start pm2.ecosystem.config.js"
echo ""
echo "Or run in development mode:"
echo "  Backend: cd apps/backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd apps/frontend && npm run dev"

