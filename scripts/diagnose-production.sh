#!/bin/bash
# Production Diagnostics Script
# Helps diagnose login and connection issues

echo "=================================="
echo "IT Budget Manager - Production Diagnostics"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        exit 1
    fi
    # Use docker compose (v2 syntax)
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

COMPOSE_FILE="${1:-docker-compose.prod.yml}"

echo "Using compose file: $COMPOSE_FILE"
echo ""

# 1. Check container status
echo "1️⃣  Checking container status..."
echo "=================================="
$DOCKER_COMPOSE -f $COMPOSE_FILE ps
echo ""

# 2. Check container health
echo "2️⃣  Checking container health..."
echo "=================================="
BACKEND_HEALTH=$($DOCKER_COMPOSE -f $COMPOSE_FILE ps | grep backend | grep -o "healthy" || echo "unhealthy")
FRONTEND_HEALTH=$($DOCKER_COMPOSE -f $COMPOSE_FILE ps | grep frontend | grep -o "healthy" || echo "unhealthy")
DB_HEALTH=$($DOCKER_COMPOSE -f $COMPOSE_FILE ps | grep db | grep -o "healthy" || echo "unhealthy")

if [ "$BACKEND_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ Backend: healthy${NC}"
else
    echo -e "${RED}❌ Backend: $BACKEND_HEALTH${NC}"
fi

if [ "$FRONTEND_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ Frontend: healthy${NC}"
else
    echo -e "${RED}❌ Frontend: $FRONTEND_HEALTH${NC}"
fi

if [ "$DB_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ Database: healthy${NC}"
else
    echo -e "${RED}❌ Database: $DB_HEALTH${NC}"
fi
echo ""

# 3. Check backend API
echo "3️⃣  Checking backend API..."
echo "=================================="
BACKEND_CONTAINER=$(docker ps --filter "name=backend_prod" --format "{{.Names}}" | head -1)

if [ -n "$BACKEND_CONTAINER" ]; then
    echo "Testing /health endpoint..."
    HEALTH_RESPONSE=$(docker exec $BACKEND_CONTAINER curl -s http://localhost:8000/health 2>/dev/null)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        echo -e "${GREEN}✅ Backend API responding: $HEALTH_RESPONSE${NC}"
    else
        echo -e "${RED}❌ Backend API not responding properly${NC}"
        echo "Response: $HEALTH_RESPONSE"
    fi
else
    echo -e "${RED}❌ Backend container not found${NC}"
fi
echo ""

# 4. Check frontend configuration
echo "4️⃣  Checking frontend configuration..."
echo "=================================="
FRONTEND_CONTAINER=$(docker ps --filter "name=frontend_prod" --format "{{.Names}}" | head -1)

if [ -n "$FRONTEND_CONTAINER" ]; then
    echo "Checking env-config.js..."
    docker exec $FRONTEND_CONTAINER cat /usr/share/nginx/html/env-config.js 2>/dev/null || echo -e "${RED}❌ env-config.js not found${NC}"
else
    echo -e "${RED}❌ Frontend container not found${NC}"
fi
echo ""

# 5. Check CORS configuration
echo "5️⃣  Checking CORS configuration..."
echo "=================================="
if [ -n "$BACKEND_CONTAINER" ]; then
    echo "CORS Origins configured in backend:"
    docker exec $BACKEND_CONTAINER python -c "from app.core.config import settings; print(settings.CORS_ORIGINS)" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not retrieve CORS settings${NC}"
else
    echo -e "${RED}❌ Backend container not running${NC}"
fi
echo ""

# 6. Check environment variables
echo "6️⃣  Checking critical environment variables..."
echo "=================================="
if [ -n "$BACKEND_CONTAINER" ]; then
    echo "Backend environment:"
    docker exec $BACKEND_CONTAINER env | grep -E "^(DB_|SECRET_KEY|CORS_|API_PREFIX|DEBUG)" | while read line; do
        if echo "$line" | grep -q "SECRET_KEY"; then
            echo "SECRET_KEY=<hidden>"
        elif echo "$line" | grep -q "PASSWORD"; then
            echo "${line%%=*}=<hidden>"
        else
            echo "$line"
        fi
    done
fi
echo ""

if [ -n "$FRONTEND_CONTAINER" ]; then
    echo "Frontend environment:"
    docker exec $FRONTEND_CONTAINER env | grep "VITE_" || echo -e "${YELLOW}⚠️  No VITE_ variables found${NC}"
fi
echo ""

# 7. Show recent logs
echo "7️⃣  Recent backend logs (last 20 lines)..."
echo "=================================="
$DOCKER_COMPOSE -f $COMPOSE_FILE logs --tail=20 backend
echo ""

echo "8️⃣  Recent frontend logs (last 10 lines)..."
echo "=================================="
$DOCKER_COMPOSE -f $COMPOSE_FILE logs --tail=10 frontend
echo ""

# 8. Test external API access (if domains are configured)
echo "9️⃣  Testing external API access..."
echo "=================================="
echo "Attempting to reach backend API externally..."

# Try to get backend domain from env or use default
BACKEND_DOMAIN=${BACKEND_DOMAIN:-api.budget-west.shknv.ru}

echo "Testing: https://$BACKEND_DOMAIN/health"
if command -v curl &> /dev/null; then
    EXTERNAL_HEALTH=$(curl -s -w "\nHTTP_CODE:%{http_code}" https://$BACKEND_DOMAIN/health 2>/dev/null)
    HTTP_CODE=$(echo "$EXTERNAL_HEALTH" | grep "HTTP_CODE" | cut -d':' -f2)
    RESPONSE=$(echo "$EXTERNAL_HEALTH" | grep -v "HTTP_CODE")

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ External API accessible (HTTP $HTTP_CODE)${NC}"
        echo "Response: $RESPONSE"
    else
        echo -e "${RED}❌ External API not accessible (HTTP $HTTP_CODE)${NC}"
        echo "Response: $RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠️  curl not available, skipping external test${NC}"
fi
echo ""

# Summary
echo "=================================="
echo "🏁 Diagnostics Complete"
echo "=================================="
echo ""
echo "Quick fixes:"
echo "1. If backend unhealthy: Check logs with 'docker-compose -f $COMPOSE_FILE logs backend'"
echo "2. If CORS error: Verify CORS_ORIGINS includes your frontend domain"
echo "3. If VITE_API_URL wrong: Set environment variable and rebuild frontend"
echo "4. If API unreachable: Check Traefik configuration and DNS"
echo ""
echo "See TROUBLESHOOTING_LOGIN.md for detailed solutions"
