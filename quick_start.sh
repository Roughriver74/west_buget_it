#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   IT Budget Manager - Quick Start${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Start PostgreSQL
echo -e "${BLUE}Step 1: Starting PostgreSQL...${NC}"
./start_postgres.sh | grep -E "(Starting|ready|Connection)"

# Setup Backend
echo ""
echo -e "${BLUE}Step 2: Setting up Backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "  ✅ Dependencies installed"

# Apply migrations
alembic upgrade head 2>&1 | grep -E "(upgrade|Initial)"
echo "  ✅ Migrations applied"

# Import data
python scripts/import_excel.py 2>&1 | grep -E "(completed|Imported|Added)" | tail -5
echo "  ✅ Data imported"

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
sleep 3
echo "  ✅ Backend started (PID: $BACKEND_PID)"

cd ..

# Test API
echo ""
echo -e "${BLUE}Step 3: Testing API...${NC}"
sleep 2
HEALTH=$(curl -s http://localhost:8000/health)
if [ "$HEALTH" == '{"status":"healthy"}' ]; then
    echo "  ✅ Backend API is healthy"
else
    echo "  ❌ Backend API is not responding"
    exit 1
fi

# Count data
echo ""
echo -e "${BLUE}Step 4: Checking database...${NC}"
CATEGORIES=$(docker exec it_budget_db psql -U budget_user -d it_budget_db -t -c "SELECT COUNT(*) FROM budget_categories;")
ORGANIZATIONS=$(docker exec it_budget_db psql -U budget_user -d it_budget_db -t -c "SELECT COUNT(*) FROM organizations;")
echo "  ✅ Categories: $CATEGORIES"
echo "  ✅ Organizations: $ORGANIZATIONS"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   🎉 IT Budget Manager is running!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Access the application:${NC}"
echo ""
echo -e "  🌐 API:           http://localhost:8000"
echo -e "  📖 API Docs:      http://localhost:8000/docs"
echo -e "  📘 ReDoc:         http://localhost:8000/redoc"
echo ""
echo -e "${BLUE}Database connection:${NC}"
echo -e "  postgresql://budget_user:budget_pass@localhost:5432/it_budget_db"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo ""
echo -e "  ${BLUE}View API logs:${NC}     tail -f backend.log"
echo -e "  ${BLUE}Stop backend:${NC}      kill \$(cat backend.pid)"
echo -e "  ${BLUE}Stop PostgreSQL:${NC}   docker stop it_budget_db"
echo -e "  ${BLUE}Database CLI:${NC}      docker exec it_budget_db psql -U budget_user -d it_budget_db"
echo ""
echo -e "${BLUE}Test endpoints:${NC}"
echo ""
echo -e "  curl http://localhost:8000/health"
echo -e "  curl http://localhost:8000/api/v1/categories"
echo -e "  curl http://localhost:8000/api/v1/analytics/dashboard?year=2025"
echo ""
echo -e "${GREEN}Frontend setup:${NC}"
echo -e "  cd frontend"
echo -e "  npm install"
echo -e "  npm run dev"
echo ""
