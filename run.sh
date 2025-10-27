#!/bin/bash

# ============================================
# IT Budget Manager - Unified Start Script
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Clear screen and show header
clear
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                            ║${NC}"
echo -e "${CYAN}║       IT Budget Manager v0.1.0             ║${NC}"
echo -e "${CYAN}║          Unified Start Script              ║${NC}"
echo -e "${CYAN}║                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_port() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for ${service} (port ${port})...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            echo -e "${GREEN}✅ ${service} is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e "\n${RED}❌ ${service} failed to start${NC}"
    return 1
}

# ============================================
# STEP 1: Start PostgreSQL
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: PostgreSQL Database${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if PostgreSQL container exists
if docker ps -a | grep -q it_budget_db; then
    if docker ps | grep -q it_budget_db; then
        echo -e "${GREEN}✅ PostgreSQL already running${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL container exists but stopped. Starting...${NC}"
        docker start it_budget_db
        sleep 3
    fi
else
    echo -e "${BLUE}🚀 Starting PostgreSQL container...${NC}"
    docker run -d \
      --name it_budget_db \
      -e POSTGRES_USER=budget_user \
      -e POSTGRES_PASSWORD=budget_pass \
      -e POSTGRES_DB=it_budget_db \
      -p 54329:54329 \
      -v it_budget_postgres_data:/var/lib/postgresql/data \
      postgres:15-alpine >/dev/null 2>&1
fi

# Wait for PostgreSQL
if ! wait_for_port 54329 "PostgreSQL"; then
    echo -e "${RED}❌ Failed to start PostgreSQL${NC}"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL: postgresql://budget_user:***@localhost:54329/it_budget_db${NC}"
echo ""

# ============================================
# STEP 2: Backend Setup
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Backend API (FastAPI)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd backend

# Check if backend is already running
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
    echo -e "${YELLOW}   Stopping existing backend...${NC}"
    if [ -f ../backend.pid ]; then
        kill $(cat ../backend.pid) 2>/dev/null
        rm ../backend.pid
    fi
    sleep 2
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
# Always check for new dependencies
echo -e "${BLUE}📦 Installing/updating dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Always apply migrations to ensure database is up to date
echo -e "${BLUE}🔄 Applying database migrations...${NC}"
unset DEBUG
if alembic upgrade head 2>&1 | grep -E "(Running upgrade|Target database is not up to date)"; then
    echo -e "${GREEN}✅ Migrations applied successfully${NC}"
else
    echo -e "${GREEN}✅ Database is up to date${NC}"
fi

# Check if data is imported
DATA_COUNT=$(docker exec it_budget_db psql -U budget_user -d it_budget_db -t -c "SELECT COUNT(*) FROM budget_categories;" 2>/dev/null | tr -d ' ')
if [ "$DATA_COUNT" -gt 0 ] 2>/dev/null; then
    echo -e "${GREEN}✅ Data already imported (${DATA_COUNT} categories)${NC}"
else
    echo -e "${BLUE}📊 Importing data from Excel...${NC}"
    unset DEBUG
    python scripts/import_excel.py 2>&1 | grep -E "(completed|Imported|Added)" | tail -3
    echo -e "${GREEN}✅ Data imported${NC}"
fi

# Create admin user if not exists
echo -e "${BLUE}👤 Checking admin user...${NC}"
unset DEBUG
ADMIN_CHECK=$(python create_admin.py 2>&1 | grep -E "(already exists|created successfully)")
if echo "$ADMIN_CHECK" | grep -q "already exists"; then
    echo -e "${GREEN}✅ Admin user already exists${NC}"
elif echo "$ADMIN_CHECK" | grep -q "created successfully"; then
    echo -e "${GREEN}✅ Admin user created (username: admin, password: admin)${NC}"
fi

# Start backend
echo -e "${BLUE}🚀 Starting Backend API server...${NC}"
unset DEBUG
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

cd ..

# Wait for backend
if ! wait_for_port 8000 "Backend API"; then
    echo -e "${RED}❌ Failed to start Backend${NC}"
    echo -e "${YELLOW}Check logs: tail -f backend.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}✅ API Docs: http://localhost:8000/docs${NC}"
echo ""

# ============================================
# STEP 3: Frontend Setup
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Frontend (React + Vite)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd frontend

# Check if frontend is already running
if check_port 5173; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 5173${NC}"
    echo -e "${YELLOW}   Stopping existing frontend...${NC}"
    if [ -f ../frontend.pid ]; then
        kill $(cat ../frontend.pid) 2>/dev/null
        rm ../frontend.pid
    fi
    sleep 2
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Installing npm dependencies...${NC}"
    npm install > /dev/null 2>&1
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Start frontend
echo -e "${BLUE}🚀 Starting Frontend dev server...${NC}"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

cd ..

# Wait for frontend
if ! wait_for_port 5173 "Frontend"; then
    echo -e "${RED}❌ Failed to start Frontend${NC}"
    echo -e "${YELLOW}Check logs: tail -f frontend.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend: http://localhost:5173${NC}"
echo ""

# ============================================
# SUCCESS!
# ============================================
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ IT Budget Manager Started Successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}🌐 Application URLs:${NC}"
echo ""
echo -e "  ${MAGENTA}Frontend:${NC}     http://localhost:5173"
echo -e "  ${MAGENTA}Backend API:${NC}  http://localhost:8000"
echo -e "  ${MAGENTA}API Docs:${NC}     http://localhost:8000/docs"
echo -e "  ${MAGENTA}ReDoc:${NC}        http://localhost:8000/redoc"
echo ""
echo -e "${CYAN}📊 Database:${NC}"
echo ""
echo -e "  ${MAGENTA}Connection:${NC}   postgresql://budget_user:budget_pass@localhost:54329/it_budget_db"
echo -e "  ${MAGENTA}CLI Access:${NC}   docker exec -it it_budget_db psql -U budget_user -d it_budget_db"
echo ""
echo -e "${CYAN}🔧 Management:${NC}"
echo ""
echo -e "  ${YELLOW}View logs:${NC}"
echo -e "    Backend:   tail -f backend.log"
echo -e "    Frontend:  tail -f frontend.log"
echo ""
echo -e "  ${YELLOW}Stop services:${NC}"
echo -e "    ./stop.sh"
echo ""
echo -e "  ${YELLOW}PIDs:${NC}"
echo -e "    Backend:   $(cat backend.pid 2>/dev/null || echo 'N/A')"
echo -e "    Frontend:  $(cat frontend.pid 2>/dev/null || echo 'N/A')"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}🎉 Ready to use! Open http://localhost:5173 in your browser${NC}"
echo ""

# Try to open browser
sleep 2
if command -v open >/dev/null 2>&1; then
    echo -e "${BLUE}🌐 Opening browser...${NC}"
    open http://localhost:5173 2>/dev/null &
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5173 2>/dev/null &
fi

echo -e "${YELLOW}Press Ctrl+C to stop following logs (services will continue running)${NC}"
echo ""

# Follow logs
trap 'echo -e "\n${YELLOW}Logs stopped. Services are still running. Use ./stop.sh to stop them.${NC}"; exit 0' INT

tail -f backend.log frontend.log 2>/dev/null
