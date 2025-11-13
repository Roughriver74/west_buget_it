#!/bin/bash
set -e

echo "=========================================="
echo "GitHub Container Registry Setup"
echo "=========================================="
echo ""
echo "This script will help you authenticate the server with GitHub Container Registry"
echo ""

# Check if token is provided
if [ -z "$1" ]; then
    echo "❌ Error: GitHub Personal Access Token required"
    echo ""
    echo "How to create a token:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Give it a name like 'Production Server Access'"
    echo "4. Select scope: read:packages"
    echo "5. Click 'Generate token' and copy it"
    echo ""
    echo "Usage: $0 <github_token>"
    echo "Example: $0 ghp_xxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

GITHUB_TOKEN="$1"
GITHUB_USERNAME="Roughriver74"
SERVER="31.129.107.178"

echo "Step 1: Logging in to GitHub Container Registry on production server..."
ssh root@$SERVER "echo '$GITHUB_TOKEN' | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin"

if [ $? -eq 0 ]; then
    echo "✅ Successfully logged in to GitHub Container Registry"
else
    echo "❌ Failed to login. Please check your token."
    exit 1
fi

echo ""
echo "Step 2: Testing image pull..."
ssh root@$SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml pull backend frontend"

if [ $? -eq 0 ]; then
    echo "✅ Successfully pulled images"
else
    echo "❌ Failed to pull images. Please check package visibility."
    exit 1
fi

echo ""
echo "Step 3: Starting services..."
ssh root@$SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml up -d"

echo ""
echo "Step 4: Waiting for backend to be ready..."
sleep 10

for i in {1..30}; do
    if ssh root@$SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health 2>/dev/null"; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "Step 5: Running migrations..."
ssh root@$SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"

echo ""
echo "Step 6: Checking container status..."
ssh root@$SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml ps"

echo ""
echo "=========================================="
echo "✅ Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Test your application:"
echo "  curl http://31.129.107.178/health"
echo ""
