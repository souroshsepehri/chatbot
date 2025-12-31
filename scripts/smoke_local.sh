#!/bin/bash
# Smoke test script - basic health and functionality checks
# Usage: ./scripts/smoke_local.sh [BASE_URL]
# Default BASE_URL: http://localhost:8000

set -e

# Default base URL
BASE_URL="${1:-http://localhost:8000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

echo "🔥 Running smoke tests against ${BASE_URL}"
echo ""

# Test 1: Health check
printf "Testing /health endpoint... "
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/health" 2>/dev/null || printf "\n000")
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)

if [ "$HEALTH_CODE" = "200" ]; then
    # Check if response contains "status" field
    if echo "$HEALTH_BODY" | grep -q '"status"'; then
        printf "${GREEN}✓ PASSED${NC}\n"
    else
        printf "${RED}✗ FAILED${NC} - Response doesn't contain status field\n"
        FAILED=1
    fi
else
    printf "${RED}✗ FAILED${NC} - HTTP ${HEALTH_CODE}\n"
    FAILED=1
fi

# Test 2: Chat refusal check
printf "Testing /chat refusal (empty KB/website)... "
CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"message":"test question"}' \
    "${BASE_URL}/chat" 2>/dev/null || printf "\n000")
CHAT_BODY=$(echo "$CHAT_RESPONSE" | head -n -1)
CHAT_CODE=$(echo "$CHAT_RESPONSE" | tail -n 1)

if [ "$CHAT_CODE" = "200" ]; then
    # Check if refused is true (using portable grep pattern)
    if echo "$CHAT_BODY" | grep -qE '"refused"[[:space:]]*:[[:space:]]*true'; then
        printf "${GREEN}✓ PASSED${NC}\n"
    else
        printf "${RED}✗ FAILED${NC} - Expected refused=true but got:\n"
        echo "$CHAT_BODY" | head -n 5
        FAILED=1
    fi
else
    printf "${RED}✗ FAILED${NC} - HTTP ${CHAT_CODE}\n"
    if [ -n "$CHAT_BODY" ]; then
        echo "Response: $CHAT_BODY"
    fi
    FAILED=1
fi

# Summary
echo ""
if [ $FAILED -eq 0 ]; then
    printf "${GREEN}✓ All smoke tests passed!${NC}\n"
    exit 0
else
    printf "${RED}✗ Some smoke tests failed!${NC}\n"
    exit 1
fi

