#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji
SUCCESS="✅"
ERROR="❌"
INFO="ℹ️"
ROCKET="🚀"
WAITING="⏳"

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}   IT Budget Manager - Auto Start Script${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo -e "${WAITING} Waiting for ${service_name} to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo -e "${SUCCESS} ${GREEN}${service_name} is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "\n${ERROR} ${RED}${service_name} failed to start${NC}"
    return 1
}

# Check if Docker is available
if command_exists docker && command_exists docker-compose; then
    echo -e "${INFO} ${BLUE}Docker detected. Using Docker setup...${NC}"
    USE_DOCKER=true
else
    echo -e "${YELLOW}Docker not found. Using manual setup...${NC}"
    USE_DOCKER=false
fi

# ============================================
# DOCKER SETUP
# ============================================
if [ "$USE_DOCKER" = true ]; then
    echo ""
    echo -e "${ROCKET} ${MAGENTA}Starting with Docker...${NC}"
    echo ""

    # Stop existing containers
    echo -e "${INFO} Stopping existing containers..."
    docker-compose down 2>/dev/null

    # Start containers
    echo -e "${INFO} Starting Docker containers..."
    docker-compose up -d

    if [ $? -ne 0 ]; then
        echo -e "${ERROR} ${RED}Failed to start Docker containers${NC}"
        exit 1
    fi

    # Wait for PostgreSQL
    echo ""
    if ! wait_for_service localhost 5432 "PostgreSQL"; then
        echo -e "${ERROR} ${RED}PostgreSQL failed to start. Check logs:${NC}"
        echo "docker-compose logs db"
        exit 1
    fi

    # Wait for Backend
    echo ""
    if ! wait_for_service localhost 8000 "Backend API"; then
        echo -e "${ERROR} ${RED}Backend failed to start. Check logs:${NC}"
        echo "docker-compose logs backend"
        exit 1
    fi

    # Apply migrations
    echo ""
    echo -e "${INFO} ${BLUE}Applying database migrations...${NC}"
    docker-compose exec -T backend alembic upgrade head

    if [ $? -ne 0 ]; then
        echo -e "${ERROR} ${RED}Failed to apply migrations${NC}"
        exit 1
    fi

    # Import data from Excel
    echo ""
    echo -e "${INFO} ${BLUE}Importing data from Excel files...${NC}"
    docker-compose exec -T backend python scripts/import_excel.py

    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Warning: Failed to import Excel data (may be already imported)${NC}"
    fi

    # Wait for Frontend
    echo ""
    if ! wait_for_service localhost 5173 "Frontend"; then
        echo -e "${ERROR} ${RED}Frontend failed to start. Check logs:${NC}"
        echo "docker-compose logs frontend"
        exit 1
    fi

    echo ""
    echo -e "${SUCCESS} ${GREEN}============================================${NC}"
    echo -e "${SUCCESS} ${GREEN}   All services started successfully!${NC}"
    echo -e "${SUCCESS} ${GREEN}============================================${NC}"
    echo ""
    echo -e "${ROCKET} ${CYAN}Your application is ready:${NC}"
    echo ""
    echo -e "  ${BLUE}Frontend:${NC}     http://localhost:5173"
    echo -e "  ${BLUE}Backend API:${NC}  http://localhost:8000"
    echo -e "  ${BLUE}API Docs:${NC}     http://localhost:8000/docs"
    echo ""
    echo -e "${INFO} ${YELLOW}Useful commands:${NC}"
    echo ""
    echo -e "  ${CYAN}View logs:${NC}         docker-compose logs -f [service]"
    echo -e "  ${CYAN}Stop services:${NC}     docker-compose down"
    echo -e "  ${CYAN}Restart service:${NC}   docker-compose restart [service]"
    echo -e "  ${CYAN}Check status:${NC}      docker-compose ps"
    echo ""
    echo -e "${INFO} Press ${YELLOW}Ctrl+C${NC} to view logs (services will continue running)"
    echo ""

    # Open browser
    sleep 3
    if command_exists open; then
        echo -e "${ROCKET} Opening browser..."
        open http://localhost:5173 2>/dev/null
    elif command_exists xdg-open; then
        xdg-open http://localhost:5173 2>/dev/null
    fi

    # Show logs
    docker-compose logs -f

# ============================================
# MANUAL SETUP (WITHOUT DOCKER)
# ============================================
else
    echo ""
    echo -e "${ROCKET} ${MAGENTA}Starting manual setup...${NC}"
    echo ""

    # Check Python
    if ! command_exists python3; then
        echo -e "${ERROR} ${RED}Python 3 is not installed${NC}"
        exit 1
    fi

    # Check Node
    if ! command_exists node; then
        echo -e "${ERROR} ${RED}Node.js is not installed${NC}"
        exit 1
    fi

    # Check PostgreSQL
    echo -e "${INFO} Checking PostgreSQL..."
    if ! command_exists psql; then
        echo -e "${ERROR} ${RED}PostgreSQL is not installed${NC}"
        echo ""
        echo "Please install PostgreSQL 15+ and create database:"
        echo "  CREATE USER budget_user WITH PASSWORD 'budget_pass';"
        echo "  CREATE DATABASE it_budget_db OWNER budget_user;"
        exit 1
    fi

    # Create database if not exists
    echo -e "${INFO} Setting up database..."
    PGPASSWORD=budget_pass psql -U budget_user -d it_budget_db -c "SELECT 1" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Database doesn't exist. Creating...${NC}"
        psql -U postgres -c "CREATE USER budget_user WITH PASSWORD 'budget_pass';" 2>/dev/null
        psql -U postgres -c "CREATE DATABASE it_budget_db OWNER budget_user;" 2>/dev/null
        psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE it_budget_db TO budget_user;" 2>/dev/null
    fi

    # Setup Backend
    echo ""
    echo -e "${INFO} ${BLUE}Setting up Backend...${NC}"
    cd backend

    # Create venv if not exists
    if [ ! -d "venv" ]; then
        echo -e "${INFO} Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate venv
    source venv/bin/activate

    # Install dependencies
    echo -e "${INFO} Installing Python dependencies..."
    pip install -q -r requirements.txt

    # Apply migrations
    echo -e "${INFO} Applying database migrations..."
    alembic upgrade head

    # Import data
    echo -e "${INFO} Importing data from Excel..."
    python scripts/import_excel.py

    # Start backend in background
    echo -e "${INFO} Starting Backend server..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid

    cd ..

    # Wait for backend
    if ! wait_for_service localhost 8000 "Backend API"; then
        echo -e "${ERROR} ${RED}Backend failed to start. Check backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi

    # Setup Frontend
    echo ""
    echo -e "${INFO} ${BLUE}Setting up Frontend...${NC}"
    cd frontend

    # Install dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${INFO} Installing npm dependencies..."
        npm install
    fi

    # Start frontend in background
    echo -e "${INFO} Starting Frontend server..."
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid

    cd ..

    # Wait for frontend
    if ! wait_for_service localhost 5173 "Frontend"; then
        echo -e "${ERROR} ${RED}Frontend failed to start. Check frontend.log${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        exit 1
    fi

    echo ""
    echo -e "${SUCCESS} ${GREEN}============================================${NC}"
    echo -e "${SUCCESS} ${GREEN}   All services started successfully!${NC}"
    echo -e "${SUCCESS} ${GREEN}============================================${NC}"
    echo ""
    echo -e "${ROCKET} ${CYAN}Your application is ready:${NC}"
    echo ""
    echo -e "  ${BLUE}Frontend:${NC}     http://localhost:5173"
    echo -e "  ${BLUE}Backend API:${NC}  http://localhost:8000"
    echo -e "  ${BLUE}API Docs:${NC}     http://localhost:8000/docs"
    echo ""
    echo -e "${INFO} ${YELLOW}Services are running in background${NC}"
    echo ""
    echo -e "  ${CYAN}Backend PID:${NC}  $BACKEND_PID (log: backend.log)"
    echo -e "  ${CYAN}Frontend PID:${NC} $FRONTEND_PID (log: frontend.log)"
    echo ""
    echo -e "${INFO} ${YELLOW}To stop services:${NC}"
    echo -e "  kill $BACKEND_PID $FRONTEND_PID"
    echo -e "  ${CYAN}or run:${NC} ./stop.sh"
    echo ""

    # Open browser
    sleep 3
    if command_exists open; then
        echo -e "${ROCKET} Opening browser..."
        open http://localhost:5173 2>/dev/null
    elif command_exists xdg-open; then
        xdg-open http://localhost:5173 2>/dev/null
    fi

    # Create stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping services..."
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
fi
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
fi
echo "Services stopped"
EOF
    chmod +x stop.sh
fi

echo ""
echo -e "${SUCCESS} ${GREEN}Setup complete! Enjoy using IT Budget Manager! 🎉${NC}"
echo ""
