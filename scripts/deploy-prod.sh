#!/bin/bash
set -e

# ============================================
# IT Budget Manager - Production Deployment
# ============================================

SERVER="root@93.189.228.52"
REMOTE_DIR="/root/budget-app"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "======================================"
echo "IT Budget Manager - Deployment Script"
echo "======================================"
echo ""
echo "Server: $SERVER"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we can connect to the server
echo "Checking connection to server..."
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to server $SERVER"
    echo "Please check your SSH connection and try again"
    exit 1
fi
print_success "Connected to server"
echo ""

# Backup current configuration on server
echo "Creating backup of current configuration..."
ssh "$SERVER" "cd $REMOTE_DIR && \
    mkdir -p backups && \
    tar -czf backups/backup-\$(date +%Y%m%d-%H%M%S).tar.gz \
        docker-compose.prod.yml .env 2>/dev/null || true"
print_success "Backup created"
echo ""

# Upload updated files
echo "Uploading updated configuration files..."
scp "$LOCAL_DIR/docker-compose.prod.yml" "$SERVER:$REMOTE_DIR/" && print_success "docker-compose.prod.yml uploaded"
scp "$LOCAL_DIR/.env.prod.example" "$SERVER:$REMOTE_DIR/" && print_success ".env.prod.example uploaded"
echo ""

# Update .env file on server if it exists
echo "Updating CORS configuration in .env..."
ssh "$SERVER" "cd $REMOTE_DIR && \
    if [ -f .env ]; then \
        # Backup current .env
        cp .env .env.backup.\$(date +%Y%m%d-%H%M%S); \
        # Update CORS_ORIGINS if it exists, or add it
        if grep -q '^CORS_ORIGINS=' .env; then \
            sed -i \"s|^CORS_ORIGINS=.*|CORS_ORIGINS='[\\\"https://budget-acme.shknv.ru\\\",\\\"https://api.budget-acme.shknv.ru\\\"]'|\" .env; \
        else \
            echo \"CORS_ORIGINS='[\\\"https://budget-acme.shknv.ru\\\",\\\"https://api.budget-acme.shknv.ru\\\"]'\" >> .env; \
        fi; \
    else \
        echo '.env file not found - please create it from .env.prod.example'; \
        exit 1; \
    fi"
print_success "CORS configuration updated in .env"
echo ""

# Restart services
echo "Restarting Docker services..."
echo "This may take a few minutes..."
echo ""

ssh "$SERVER" "cd $REMOTE_DIR && \
    docker-compose -f docker-compose.prod.yml down && \
    docker-compose -f docker-compose.prod.yml up -d --build"

if [ $? -eq 0 ]; then
    print_success "Docker services restarted successfully"
else
    print_error "Failed to restart Docker services"
    exit 1
fi
echo ""

# Wait for services to start
echo "Waiting for services to start (40 seconds)..."
sleep 40
echo ""

# Check service status
echo "Checking service status..."
ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f docker-compose.prod.yml ps"
echo ""

# Check backend health
echo "Checking backend health endpoint..."
if ssh "$SERVER" "docker exec it_budget_backend_prod curl -f http://localhost:8000/health" > /dev/null 2>&1; then
    print_success "Backend is healthy"
else
    print_warning "Backend health check failed - service may still be starting"
fi
echo ""

# Show backend logs (last 20 lines)
echo "Recent backend logs:"
ssh "$SERVER" "docker logs --tail 20 it_budget_backend_prod"
echo ""

echo "======================================"
print_success "Deployment completed!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Test login at: https://budget-acme.shknv.ru"
echo "2. Check API at: https://api.budget-acme.shknv.ru/health"
echo "3. View full logs: ssh $SERVER 'docker logs -f it_budget_backend_prod'"
echo ""
echo "If issues persist, check logs on server:"
echo "  ssh $SERVER"
echo "  cd $REMOTE_DIR"
echo "  docker-compose -f docker-compose.prod.yml logs backend"
echo ""
