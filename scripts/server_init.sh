#!/bin/bash
# Server Initialization Script
# This script should be run ONCE after initial server setup
# It creates necessary files and symlinks that are not in git

set -e

SERVER_ROOT="/opt/budget-app"

echo "=========================================="
echo "Server Initialization"
echo "=========================================="

# Check if .env.prod exists
if [ ! -f "$SERVER_ROOT/.env.prod" ]; then
    echo "❌ Error: .env.prod not found!"
    echo "Please create $SERVER_ROOT/.env.prod first"
    exit 1
fi

# Create symlink .env -> .env.prod if doesn't exist
if [ ! -L "$SERVER_ROOT/.env" ]; then
    echo "Creating symlink: .env -> .env.prod"
    cd "$SERVER_ROOT"
    ln -sf .env.prod .env
    echo "✅ Symlink created"
else
    echo "✅ Symlink .env already exists"
fi

# Verify Docker Compose can read variables
echo ""
echo "Verifying environment variables..."
cd "$SERVER_ROOT"
if docker compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    docker compose -f docker-compose.prod.yml config
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Server initialization completed!"
echo "=========================================="
echo ""
echo "Required environment variables in .env.prod:"
echo "  - POSTGRES_DB"
echo "  - POSTGRES_USER"
echo "  - POSTGRES_PASSWORD"
echo "  - CORS_ORIGINS (JSON array format)"
echo "  - SECRET_KEY"
echo ""
echo "You can now deploy with: git push origin main"
