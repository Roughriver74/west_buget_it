#!/bin/sh
set -e

echo "======================================"
echo "IT Budget Manager - Frontend Starting"
echo "======================================"

# Default values if not provided
VITE_API_URL=${VITE_API_URL:-"http://localhost:8888"}

echo "Configuring frontend with:"
echo "  VITE_API_URL: $VITE_API_URL"

# Create or update env-config.js (run as root before switching user)
cat > /usr/share/nginx/html/env-config.js << EOF
// Runtime configuration - injected at container startup
// Generated at: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
window.ENV_CONFIG = {
  VITE_API_URL: '${VITE_API_URL}'
};
EOF

echo "✅ Configuration completed!"
echo "Generated env-config.js with VITE_API_URL: ${VITE_API_URL}"

# Ensure correct permissions
chown nginx:nginx /usr/share/nginx/html/env-config.js

# Show generated config for debugging
echo ""
echo "Generated config contents:"
cat /usr/share/nginx/html/env-config.js
echo ""

echo ""
echo "======================================"
echo "Starting Nginx web server"
echo "======================================"

# Switch to nginx user and start nginx
exec su-exec nginx nginx -g 'daemon off;'
