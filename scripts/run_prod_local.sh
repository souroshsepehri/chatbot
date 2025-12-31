#!/bin/bash
# Bash script to run production mode locally
# This mimics exactly what runs on the server

set -e  # Exit on error

# Make script executable
chmod +x "$0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo -e "${GREEN}🚀 Starting Production Mode (Local)${NC}"
echo ""

# Parse arguments
SKIP_BUILD=false
SKIP_MIGRATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-migrate)
            SKIP_MIGRATE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 1. Load environment variables from .env.production files
echo -e "${CYAN}📋 Loading production environment variables...${NC}"

BACKEND_ENV_PATH="$PROJECT_ROOT/apps/backend/.env.production"
FRONTEND_ENV_PATH="$PROJECT_ROOT/apps/frontend/.env.production.local"

# Check if production env files exist, if not, use .env files
if [ ! -f "$BACKEND_ENV_PATH" ]; then
    BACKEND_ENV_PATH="$PROJECT_ROOT/apps/backend/.env"
    echo -e "${YELLOW}⚠️  .env.production not found, using .env${NC}"
fi

if [ ! -f "$FRONTEND_ENV_PATH" ]; then
    FRONTEND_ENV_PATH="$PROJECT_ROOT/apps/frontend/.env.local"
    echo -e "${YELLOW}⚠️  .env.production.local not found, using .env.local${NC}"
fi

# Load backend env
if [ -f "$BACKEND_ENV_PATH" ]; then
    set -a
    source "$BACKEND_ENV_PATH"
    set +a
    echo -e "${GREEN}✅ Backend env loaded from: $BACKEND_ENV_PATH${NC}"
else
    echo -e "${RED}❌ Backend .env file not found at: $BACKEND_ENV_PATH${NC}"
    exit 1
fi

# Load frontend env
if [ -f "$FRONTEND_ENV_PATH" ]; then
    set -a
    source "$FRONTEND_ENV_PATH"
    set +a
    echo -e "${GREEN}✅ Frontend env loaded from: $FRONTEND_ENV_PATH${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend .env file not found, using defaults${NC}"
fi

echo ""

# 2. Database Migration
if [ "$SKIP_MIGRATE" = false ]; then
    echo -e "${CYAN}🗄️  Running database migrations...${NC}"
    cd "$PROJECT_ROOT/apps/backend"
    
    # Check if venv exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        PYTHON_CMD="venv/bin/python"
    else
        PYTHON_CMD="python3"
        echo -e "${YELLOW}⚠️  Virtual environment not found, using system Python${NC}"
    fi
    
    $PYTHON_CMD -m alembic upgrade head
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Migration failed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Migrations completed${NC}"
    echo ""
else
    echo -e "${YELLOW}⏭️  Skipping migrations (--skip-migrate)${NC}"
    echo ""
fi

# 3. Build Frontend
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${CYAN}🏗️  Building frontend...${NC}"
    cd "$PROJECT_ROOT/apps/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Build
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Frontend build failed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Frontend built successfully${NC}"
    echo ""
else
    echo -e "${YELLOW}⏭️  Skipping frontend build (--skip-build)${NC}"
    echo ""
fi

# 4. Start with PM2
echo -e "${CYAN}🚀 Starting services with PM2...${NC}"
cd "$PROJECT_ROOT"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}❌ PM2 is not installed. Install it with: npm install -g pm2${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Stop existing processes
echo -e "${YELLOW}🛑 Stopping existing PM2 processes...${NC}"
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

# Start with PM2
pm2 start pm2.ecosystem.config.js

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start PM2 services!${NC}"
    exit 1
fi

# Show status
echo ""
echo -e "${CYAN}📊 PM2 Status:${NC}"
pm2 status

echo ""
echo -e "${GREEN}✅ Production mode started successfully!${NC}"
echo ""
echo -e "${CYAN}📍 Services:${NC}"
echo -e "   ${NC}Backend:  http://localhost:8000"
echo -e "   ${NC}Frontend: http://localhost:3000"
echo ""
echo -e "${CYAN}📝 Useful commands:${NC}"
echo -e "   ${NC}pm2 logs              - View all logs"
echo -e "   ${NC}pm2 logs chatbot-backend   - View backend logs"
echo -e "   ${NC}pm2 logs chatbot-frontend  - View frontend logs"
echo -e "   ${NC}pm2 stop all          - Stop all services"
echo -e "   ${NC}pm2 restart all       - Restart all services"
echo ""

