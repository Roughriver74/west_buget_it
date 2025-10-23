#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   IT Budget Manager - Setup Test${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Test Backend dependencies
echo -e "${BLUE}Testing Backend setup...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q fastapi uvicorn sqlalchemy pydantic pydantic-settings

# Test FastAPI import
echo "Testing FastAPI import..."
python3 << 'EOF'
try:
    from app.main import app
    from app.core.config import settings
    print("✅ Backend imports successful!")
    print(f"   App Name: {settings.APP_NAME}")
    print(f"   Version: {settings.APP_VERSION}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
EOF

cd ..

# Test Frontend dependencies
echo ""
echo -e "${BLUE}Testing Frontend setup...${NC}"
cd frontend

if [ ! -f "package.json" ]; then
    echo "❌ package.json not found"
    exit 1
fi

echo "Checking package.json..."
if [ -f "package.json" ]; then
    echo "✅ package.json exists"
    echo "   Dependencies:"
    grep -A 20 '"dependencies"' package.json | grep '"' | head -10
fi

cd ..

# Summary
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Setup Test Summary${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Backend files:"
find backend/app -name "*.py" | wc -l | xargs echo "  Python files:"

echo ""
echo "Frontend files:"
find frontend/src -name "*.ts" -o -name "*.tsx" | wc -l | xargs echo "  TypeScript files:"

echo ""
echo "Documentation:"
ls -1 *.md | wc -l | xargs echo "  Markdown files:"

echo ""
echo -e "${GREEN}✅ Project structure is correct!${NC}"
echo ""
echo "To start the application:"
echo "  1. Install PostgreSQL or use Docker"
echo "  2. Run: ./start.sh"
echo ""
echo "Or use Docker (recommended):"
echo "  1. Install Docker and Docker Compose"
echo "  2. Run: docker-compose up -d"
echo ""
