#!/bin/sh
set -e

echo "======================================"
echo "IT Budget Manager - Frontend Starting"
echo "======================================"

# Default values if not provided
VITE_API_URL=${VITE_API_URL:-"http://localhost:8888"}

echo "Configuring frontend with:"
echo "  VITE_API_URL: $VITE_API_URL"

# Replace placeholders in env-config.js (run as root)
sed -i "s|__VITE_API_URL__|${VITE_API_URL}|g" /usr/share/nginx/html/env-config.js

echo "✅ Configuration completed!"
echo ""
echo "======================================"
echo "Starting Nginx web server"
echo "======================================"

# Switch to nginx user and start nginx
exec su-exec nginx nginx -g 'daemon off;'
