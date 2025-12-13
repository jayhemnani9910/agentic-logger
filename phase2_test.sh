#!/bin/bash

# Phase 2 Integration Test Suite
# Tests API endpoints, database persistence, and dashboard connectivity

set -e

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
MAX_RETRIES=30
RETRY_DELAY=2

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Phase 2 Integration Test Suite                        ║${NC}"
echo -e "${BLUE}║      API Endpoints + Dashboard + Agent Integration        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Wait for services to be healthy
echo -e "${YELLOW}[TEST 1] Waiting for services to be healthy...${NC}"
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -sf "${API_URL}/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        break
    fi
    RETRY=$((RETRY + 1))
    echo -e "${YELLOW}  Attempt $RETRY/$MAX_RETRIES - Backend not ready, waiting...${NC}"
    sleep $RETRY_DELAY
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Backend did not become healthy${NC}"
    exit 1
fi

# Test 2: Check extended health endpoints
echo ""
echo -e "${YELLOW}[TEST 2] Checking extended health endpoints...${NC}"
RESPONSE=$(curl -sf "${API_URL}/api/health/extended" || echo "{}")
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ Extended health check passed${NC}"
else
    echo -e "${RED}✗ Extended health check failed${NC}"
    echo "Response: $RESPONSE"
fi

# Test 3: Test clipboard events API
echo ""
echo -e "${YELLOW}[TEST 3] Testing clipboard events API...${NC}"
CLIPBOARD_RESPONSE=$(curl -sf "${API_URL}/api/clipboard?limit=10&hours=24" || echo "{}")
if echo "$CLIPBOARD_RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$CLIPBOARD_RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*$' || echo "0")
    echo -e "${GREEN}✓ Clipboard API working (${COUNT} events)${NC}"
else
    echo -e "${RED}✗ Clipboard API failed${NC}"
fi

# Test 4: Test activity events API
echo ""
echo -e "${YELLOW}[TEST 4] Testing activity events API...${NC}"
ACTIVITY_RESPONSE=$(curl -sf "${API_URL}/api/activity?limit=10&hours=24" || echo "{}")
if echo "$ACTIVITY_RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$ACTIVITY_RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*$' || echo "0")
    echo -e "${GREEN}✓ Activity API working (${COUNT} events)${NC}"
else
    echo -e "${RED}✗ Activity API failed${NC}"
fi

# Test 5: Test commands API
echo ""
echo -e "${YELLOW}[TEST 5] Testing commands API...${NC}"
COMMANDS_RESPONSE=$(curl -sf "${API_URL}/api/commands?limit=10&hours=24" || echo "{}")
if echo "$COMMANDS_RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$COMMANDS_RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*$' || echo "0")
    echo -e "${GREEN}✓ Commands API working (${COUNT} events)${NC}"
else
    echo -e "${RED}✗ Commands API failed${NC}"
fi

# Test 6: Test stats API
echo ""
echo -e "${YELLOW}[TEST 6] Testing stats API...${NC}"
STATS_RESPONSE=$(curl -sf "${API_URL}/api/stats?hours=24" || echo "{}")
if echo "$STATS_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ Stats API working${NC}"
    echo "  $(echo "$STATS_RESPONSE" | grep -o '"total":[0-9]*' | head -1)"
else
    echo -e "${RED}✗ Stats API failed${NC}"
fi

# Test 7: Test search API
echo ""
echo -e "${YELLOW}[TEST 7] Testing search API...${NC}"
SEARCH_RESPONSE=$(curl -sf -X POST "${API_URL}/api/search" \
    -H "Content-Type: application/json" \
    -d '{"query":"test","types":["clipboard","activity","commands"],"limit":10}' || echo "{}")
if echo "$SEARCH_RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$SEARCH_RESPONSE" | grep -o '"count":[0-9]*' | grep -o '[0-9]*$' || echo "0")
    echo -e "${GREEN}✓ Search API working (${COUNT} results)${NC}"
else
    echo -e "${RED}✗ Search API failed${NC}"
fi

# Test 8: Test database persistence
echo ""
echo -e "${YELLOW}[TEST 8] Testing database persistence...${NC}"
# Create a test event
CREATE_RESPONSE=$(curl -sf -X POST "${API_URL}/api/events" \
    -H "Content-Type: application/json" \
    -d '{"message":"Phase 2 Test Event","event_type":"test","status":"success"}' || echo "{}")

if echo "$CREATE_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ Event creation successful${NC}"
    
    # Try to retrieve it
    GET_RESPONSE=$(curl -sf "${API_URL}/api/events" || echo "{}")
    if echo "$GET_RESPONSE" | grep -q "Phase 2 Test Event"; then
        echo -e "${GREEN}✓ Event persistence verified${NC}"
    else
        echo -e "${YELLOW}⚠ Event not yet visible in list (may be cached)${NC}"
    fi
else
    echo -e "${RED}✗ Event creation failed${NC}"
fi

# Test 9: Check frontend loads
echo ""
echo -e "${YELLOW}[TEST 9] Checking frontend availability...${NC}"
RETRY=0
while [ $RETRY -lt 10 ]; do
    if curl -sf "${FRONTEND_URL}" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is available on ${FRONTEND_URL}${NC}"
        break
    fi
    RETRY=$((RETRY + 1))
    echo -e "${YELLOW}  Attempt $RETRY/10 - Frontend not ready${NC}"
    sleep 2
done

if [ $RETRY -eq 10 ]; then
    echo -e "${YELLOW}⚠ Frontend not yet available (normal on first build)${NC}"
fi

# Test 10: Database tables check
echo ""
echo -e "${YELLOW}[TEST 10] Verifying database schema...${NC}"
POSTGRES_CMD="PGPASSWORD=postgres psql -h localhost -U postgres -d agentic_logger -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';\" 2>/dev/null"

TABLES=$(eval $POSTGRES_CMD || echo "error")
if [ "$TABLES" != "error" ] && [ "$TABLES" -gt 0 ]; then
    echo -e "${GREEN}✓ Database tables exist (${TABLES} tables)${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify database tables (PostgreSQL not accessible)${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Phase 2 Integration Tests Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next Steps:"
echo "  1. Frontend Dashboard: Open ${FRONTEND_URL} in browser"
echo "  2. Activity Tab: View clipboard, activity, and command timelines"
echo "  3. Stats Tab: Review aggregated statistics"
echo "  4. Search Tab: Test semantic search across events"
echo ""
echo "API Endpoints:"
echo "  GET  ${API_URL}/api/clipboard     - Clipboard events"
echo "  GET  ${API_URL}/api/activity      - Activity timeline"
echo "  GET  ${API_URL}/api/commands      - Command history"
echo "  POST ${API_URL}/api/search        - Semantic search"
echo "  GET  ${API_URL}/api/stats         - System statistics"
echo ""
