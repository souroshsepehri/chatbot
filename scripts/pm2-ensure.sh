#!/bin/bash
# PM2 Ensure Script - Idempotent script to ensure both backend and frontend are running
# Usage: bash scripts/pm2-ensure.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Checking PM2 processes..."

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}❌ PM2 is not installed. Please install it first:${NC}"
    echo "   npm install -g pm2"
    exit 1
fi

# Get list of running PM2 processes
PM2_LIST=$(pm2 jlist 2>/dev/null || echo "[]")

# Check if chatbot-backend exists
BACKEND_EXISTS=$(echo "$PM2_LIST" | grep -o '"name":"chatbot-backend"' || echo "")

# Check if chatbot-frontend exists
FRONTEND_EXISTS=$(echo "$PM2_LIST" | grep -o '"name":"chatbot-frontend"' || echo "")

# Determine action
if [ -z "$BACKEND_EXISTS" ] || [ -z "$FRONTEND_EXISTS" ]; then
    echo -e "${YELLOW}⚠️  Missing processes detected. Starting PM2 ecosystem...${NC}"
    pm2 start pm2.ecosystem.config.js
else
    echo -e "${GREEN}✓ Both processes found. Reloading with updated environment...${NC}"
    pm2 reload pm2.ecosystem.config.js --update-env
fi

# Always save PM2 configuration
echo "💾 Saving PM2 configuration..."
pm2 save

# Show status
echo ""
echo -e "${GREEN}📊 PM2 Status:${NC}"
pm2 status

echo ""
echo -e "${GREEN}✅ PM2 ensure complete!${NC}"
echo ""
echo "To verify services are running:"
echo "  curl 127.0.0.1:8000/health"
echo "  curl 127.0.0.1:3000"

