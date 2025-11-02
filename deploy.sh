#!/bin/bash

# ==============================================
# IT Budget Manager - Production Deployment Script
# ==============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_HOST="93.189.228.52"
SERVER_USER="root"
REMOTE_DIR="/root/it_budget"
LOCAL_DIR="$(pwd)"

echo "=========================================="
echo "IT Budget Manager - Deployment"
echo "=========================================="
echo ""

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production not found!${NC}"
    echo "Please create .env.production file with production settings."
    exit 1
fi

# Check if required variables are set
if grep -q "CHANGE_ME" .env.production; then
    echo -e "${YELLOW}Warning: Found CHANGE_ME placeholders in .env.production${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Configuration validated"
echo ""

# Step 1: Create deployment package
echo "📦 Creating deployment package..."
TEMP_DIR=$(mktemp -d)
rsync -av --progress \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude 'backend/venv' \
    --exclude 'backend/logs' \
    --exclude 'frontend/dist' \
    --exclude 'frontend/node_modules' \
    "$LOCAL_DIR/" "$TEMP_DIR/"

# Copy .env.production as .env
cp .env.production "$TEMP_DIR/.env"
echo -e "${GREEN}✓${NC} Deployment package created"
echo ""

# Step 2: Upload to server
echo "⬆️  Uploading to server..."
ssh $SERVER_USER@$SERVER_HOST "mkdir -p $REMOTE_DIR"
rsync -avz --progress \
    --delete \
    "$TEMP_DIR/" \
    "$SERVER_USER@$SERVER_HOST:$REMOTE_DIR/"

echo -e "${GREEN}✓${NC} Files uploaded"
echo ""

# Step 3: Deploy on server
echo "🚀 Deploying on server..."
ssh $SERVER_USER@$SERVER_HOST << 'ENDSSH'
cd /root/it_budget

echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

echo "Building images..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Waiting for services to start..."
sleep 10

echo "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

echo "Checking logs..."
docker-compose -f docker-compose.prod.yml logs --tail=50
ENDSSH

echo ""
echo -e "${GREEN}✓${NC} Deployment completed!"
echo ""
echo "Service URLs:"
echo "  Frontend: https://budget-west.shknv.ru"
echo "  Backend API: http://$SERVER_HOST:8888"
echo ""
echo "To view logs:"
echo "  ssh $SERVER_USER@$SERVER_HOST 'cd $REMOTE_DIR && docker-compose -f docker-compose.prod.yml logs -f'"
echo ""
echo "To restart services:"
echo "  ssh $SERVER_USER@$SERVER_HOST 'cd $REMOTE_DIR && docker-compose -f docker-compose.prod.yml restart'"
echo ""

# Cleanup
rm -rf "$TEMP_DIR"

exit 0
