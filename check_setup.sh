#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "IT Budget Manager - Setup Checker"
echo "======================================"
echo ""

# Check if Docker is installed
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
fi

# Check if Docker Compose is installed
echo -n "Checking Docker Compose... "
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
fi

# Check if Python is installed
echo -n "Checking Python 3.11+... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    echo -e "${GREEN}✓ Installed (v${PYTHON_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (optional for non-Docker setup)${NC}"
fi

# Check if Node.js is installed
echo -n "Checking Node.js 18+... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Installed (${NODE_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (optional for non-Docker setup)${NC}"
fi

# Check if PostgreSQL is installed
echo -n "Checking PostgreSQL... "
if command -v psql &> /dev/null; then
    POSTGRES_VERSION=$(psql --version | cut -d ' ' -f 3)
    echo -e "${GREEN}✓ Installed (v${POSTGRES_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (optional for non-Docker setup)${NC}"
fi

echo ""
echo "======================================"
echo "Project Files Check"
echo "======================================"

# Check if essential files exist
FILES=(
    "docker-compose.yml"
    "backend/requirements.txt"
    "backend/app/main.py"
    "backend/alembic.ini"
    "frontend/package.json"
    "frontend/src/main.tsx"
    ".gitignore"
    "README.md"
)

for FILE in "${FILES[@]}"; do
    echo -n "Checking ${FILE}... "
    if [ -f "$FILE" ]; then
        echo -e "${GREEN}✓ Exists${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
    fi
done

echo ""
echo "======================================"
echo "Excel Data Files Check"
echo "======================================"

# Check if Excel files exist
EXCEL_FILES=(
    "IT_Budget_Analysis_Full.xlsx"
    "заявки на расходы по дням.xlsx"
)

for FILE in "${EXCEL_FILES[@]}"; do
    echo -n "Checking ${FILE}... "
    if [ -f "$FILE" ]; then
        echo -e "${GREEN}✓ Exists${NC}"
    else
        echo -e "${YELLOW}⚠ Not found${NC}"
    fi
done

echo ""
echo "======================================"
echo "Configuration Files Check"
echo "======================================"

# Check .env files
echo -n "Checking backend/.env... "
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}⚠ Not found (will use .env.example)${NC}"
fi

echo -n "Checking frontend/.env... "
if [ -f "frontend/.env" ]; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}⚠ Not found (will use .env.example)${NC}"
fi

echo ""
echo "======================================"
echo "Recommendations"
echo "======================================"

if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ You can use Docker setup!${NC}"
    echo ""
    echo "Quick start with Docker:"
    echo "  1. docker-compose up -d"
    echo "  2. docker-compose exec backend alembic upgrade head"
    echo "  3. docker-compose exec backend python scripts/import_excel.py"
    echo "  4. Open http://localhost:5173"
else
    echo -e "${YELLOW}⚠ Docker not fully available${NC}"
    echo ""
    echo "You'll need to install dependencies manually:"
    echo "  Backend: cd backend && pip install -r requirements.txt"
    echo "  Frontend: cd frontend && npm install"
fi

echo ""
echo "For detailed instructions, see:"
echo "  - QUICKSTART.md for quick setup"
echo "  - SETUP.md for detailed setup"
echo "  - README.md for overview"
echo ""
