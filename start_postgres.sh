#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   Starting PostgreSQL in Docker${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Stop existing PostgreSQL container if running
echo -e "${YELLOW}Stopping existing PostgreSQL container...${NC}"
docker stop it_budget_db 2>/dev/null
docker rm it_budget_db 2>/dev/null

# Start PostgreSQL
echo -e "${BLUE}Starting PostgreSQL container...${NC}"
docker run -d \
  --name it_budget_db \
  -e POSTGRES_USER=budget_user \
  -e POSTGRES_PASSWORD=budget_pass \
  -e POSTGRES_DB=it_budget_db \
  -p 5432:5432 \
  -v it_budget_postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start PostgreSQL${NC}"
    exit 1
fi

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if docker exec it_budget_db pg_isready -U budget_user -d it_budget_db &>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Test connection
echo ""
echo -e "${BLUE}Testing database connection...${NC}"
docker exec it_budget_db psql -U budget_user -d it_budget_db -c "SELECT version();" | head -3

# Show connection info
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   PostgreSQL is running!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Connection details:${NC}"
echo -e "  Host:     localhost"
echo -e "  Port:     5432"
echo -e "  Database: it_budget_db"
echo -e "  User:     budget_user"
echo -e "  Password: budget_pass"
echo ""
echo -e "${BLUE}Connection string:${NC}"
echo -e "  postgresql://budget_user:budget_pass@localhost:5432/it_budget_db"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  ${YELLOW}Connect to DB:${NC}    docker exec -it it_budget_db psql -U budget_user -d it_budget_db"
echo -e "  ${YELLOW}View logs:${NC}        docker logs it_budget_db"
echo -e "  ${YELLOW}Stop DB:${NC}          docker stop it_budget_db"
echo -e "  ${YELLOW}Start DB:${NC}         docker start it_budget_db"
echo -e "  ${YELLOW}Remove DB:${NC}        docker rm -f it_budget_db"
echo ""
