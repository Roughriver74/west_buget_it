#!/bin/bash
# Quick diagnostic script - run this on the server

echo "========================================="
echo "Quick Diagnostics for 503 Error"
echo "========================================="
echo ""

# Find docker-compose command
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
elif command -v docker &> /dev/null; then
    DC="docker compose"
else
    echo "ERROR: Docker not found"
    exit 1
fi

# Try to find compose file
COMPOSE_FILE=""
for file in docker-compose.prod.yml docker-compose.yml; do
    if [ -f "$file" ]; then
        COMPOSE_FILE="$file"
        break
    fi
done

if [ -z "$COMPOSE_FILE" ]; then
    echo "ERROR: docker-compose file not found"
    exit 1
fi

echo "Using: $COMPOSE_FILE"
echo ""

# 1. Check container status
echo "1. Container Status:"
echo "==================="
$DC -f $COMPOSE_FILE ps
echo ""

# 2. Check if backend is running
echo "2. Backend Container Check:"
echo "==========================="
BACKEND_RUNNING=$(docker ps --filter "name=backend" --filter "status=running" --format "{{.Names}}")
if [ -n "$BACKEND_RUNNING" ]; then
    echo "✅ Backend container is running: $BACKEND_RUNNING"

    # Test backend internally
    echo ""
    echo "Testing backend internally (from inside container)..."
    HEALTH=$(docker exec $BACKEND_RUNNING curl -s http://localhost:8000/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo "✅ Backend /health responds: $HEALTH"
    else
        echo "❌ Backend /health not responding: $HEALTH"
    fi

    # Test OPTIONS request
    echo ""
    echo "Testing OPTIONS request (CORS preflight)..."
    OPTIONS=$(docker exec $BACKEND_RUNNING curl -s -X OPTIONS http://localhost:8000/api/v1/auth/login -H "Origin: https://budget-west.shknv.ru" -H "Access-Control-Request-Method: POST" -v 2>&1)
    echo "$OPTIONS" | grep -E "HTTP|Access-Control"

else
    echo "❌ Backend container is NOT running"
    echo ""
    echo "Checking if container exists but stopped..."
    docker ps -a --filter "name=backend" --format "{{.Names}} - {{.Status}}"
fi
echo ""

# 3. Check backend logs
echo "3. Backend Logs (last 30 lines):"
echo "================================="
$DC -f $COMPOSE_FILE logs --tail=30 backend
echo ""

# 4. Check Traefik connectivity
echo "4. Network Connectivity:"
echo "========================"
if [ -n "$BACKEND_RUNNING" ]; then
    echo "Backend IP:"
    docker inspect $BACKEND_RUNNING --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

    echo ""
    echo "Networks:"
    docker inspect $BACKEND_RUNNING --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}}: {{$value.IPAddress}}{{"\n"}}{{end}}'
fi
echo ""

# 5. Check Traefik labels
echo "5. Traefik Labels:"
echo "=================="
if [ -n "$BACKEND_RUNNING" ]; then
    docker inspect $BACKEND_RUNNING --format='{{range $key, $value := .Config.Labels}}{{if or (contains $key "traefik")}}{{$key}}={{$value}}{{"\n"}}{{end}}{{end}}'
fi
echo ""

# 6. Try external API access
echo "6. External API Test:"
echo "====================="
echo "Testing: https://api.budget-west.shknv.ru/health"
curl -v https://api.budget-west.shknv.ru/health 2>&1 | head -20
echo ""

# 7. Test OPTIONS to external endpoint
echo ""
echo "7. Testing OPTIONS (CORS Preflight) to external API:"
echo "====================================================="
curl -v -X OPTIONS https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Origin: https://budget-west.shknv.ru" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  2>&1 | grep -E "HTTP|Access-Control|503"
echo ""

echo ""
echo "========================================="
echo "Diagnostics Complete"
echo "========================================="
echo ""
echo "Common issues for 503 errors:"
echo "1. Backend container not running → Check logs above"
echo "2. Backend starting up slowly → Wait 1-2 minutes and retry"
echo "3. Database connection failed → Check DB container status"
echo "4. Traefik can't reach backend → Check network configuration"
echo ""
