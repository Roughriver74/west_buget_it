#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}Stopping IT Budget Manager services...${NC}"
echo ""

# Stop Backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
        rm backend.pid
        echo -e "${GREEN}✅ Backend stopped${NC}"
    else
        echo -e "${YELLOW}Backend process not running${NC}"
        rm backend.pid
    fi
else
    echo -e "${YELLOW}No backend PID file found${NC}"
fi

# Stop Frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        rm frontend.pid
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}Frontend process not running${NC}"
        rm frontend.pid
    fi
else
    echo -e "${YELLOW}No frontend PID file found${NC}"
fi

# Kill any remaining processes on ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
