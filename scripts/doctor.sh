#!/bin/bash
# Doctor script - verify deployment readiness

set -e

echo "🔍 Running deployment health checks..."
echo ""

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# 1. Check required environment variables
echo "📋 Checking environment variables..."
echo ""

# Backend env
BACKEND_ENV="$PROJECT_ROOT/apps/backend/.env"
if [ ! -f "$BACKEND_ENV" ]; then
    echo -e "${YELLOW}⚠️  Backend .env not found at $BACKEND_ENV${NC}"
    echo "   Create it from .env.example"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓${NC} Backend .env exists"
    
    # Check required vars
    REQUIRED_VARS=("DATABASE_URL" "OPENAI_API_KEY" "SESSION_SECRET" "FRONTEND_ORIGIN")
    for var in "${REQUIRED_VARS[@]}"; do
        if ! grep -q "^${var}=" "$BACKEND_ENV" || grep -q "^${var}=$" "$BACKEND_ENV"; then
            echo -e "${RED}✗${NC} Missing or empty: $var"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${GREEN}✓${NC} $var is set"
        fi
    done
fi

# Frontend env
FRONTEND_ENV="$PROJECT_ROOT/apps/frontend/.env.local"
if [ ! -f "$FRONTEND_ENV" ]; then
    echo -e "${YELLOW}⚠️  Frontend .env.local not found at $FRONTEND_ENV${NC}"
    echo "   Optional for local dev (Next.js rewrite handles /api)"
else
    echo -e "${GREEN}✓${NC} Frontend .env.local exists"
fi

echo ""

# 2. Check frontend build
echo "📦 Checking frontend build..."
if [ ! -d "$PROJECT_ROOT/apps/frontend/.next" ]; then
    echo -e "${YELLOW}⚠️  Frontend build not found${NC}"
    echo "   Run: cd apps/frontend && npm run build"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓${NC} Frontend build exists"
fi
echo ""

# 3. Check backend dependencies
echo "🐍 Checking backend dependencies..."
if [ ! -d "$PROJECT_ROOT/apps/backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Backend virtual environment not found${NC}"
    echo "   Run: cd apps/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓${NC} Backend virtual environment exists"
fi
echo ""

# 4. Check PM2 ecosystem file
echo "⚙️  Checking PM2 configuration..."
if [ ! -f "$PROJECT_ROOT/pm2.ecosystem.config.js" ]; then
    echo -e "${RED}✗${NC} pm2.ecosystem.config.js not found"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓${NC} PM2 ecosystem file exists"
fi
echo ""

# 5. Health check (if backend is running)
echo "🏥 Checking backend health..."
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

if command -v curl &> /dev/null; then
    if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend health check passed"
        
        # Check components
        if curl -s -f "$BACKEND_URL/health/components" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Backend components health check passed"
        else
            echo -e "${YELLOW}⚠️  Backend components health check failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Backend not responding at $BACKEND_URL${NC}"
        echo "   Start backend: cd apps/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    fi
else
    echo -e "${YELLOW}⚠️  curl not found, skipping health check${NC}"
fi
echo ""

# Summary
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS issue(s)${NC}"
    echo ""
    echo "Fix the issues above before deploying."
    exit 1
fi





