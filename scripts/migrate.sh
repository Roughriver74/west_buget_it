#!/bin/bash

# ============================================
# IT Budget Manager - Database Migration Script
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                            ║${NC}"
echo -e "${CYAN}║       Database Migration Utility           ║${NC}"
echo -e "${CYAN}║                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo -e "${YELLOW}   Run ./run.sh first to set up the environment${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Display current migration status
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Current Migration Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

unset DEBUG
CURRENT=$(alembic current 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Current revision:${NC}"
    echo "$CURRENT"
else
    echo -e "${RED}❌ Failed to check current revision${NC}"
    echo "$CURRENT"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Available Migrations${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

HEADS=$(alembic heads 2>&1)
echo -e "${CYAN}Latest revision:${NC}"
echo "$HEADS"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Migration History${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

HISTORY=$(alembic history --verbose 2>&1 | head -20)
echo "$HISTORY"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Applying Migrations${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Apply migrations
echo -e "${YELLOW}🔄 Upgrading database to latest version...${NC}"
unset DEBUG
UPGRADE_OUTPUT=$(alembic upgrade head 2>&1)
UPGRADE_STATUS=$?

if [ $UPGRADE_STATUS -eq 0 ]; then
    if echo "$UPGRADE_OUTPUT" | grep -q "Running upgrade"; then
        echo -e "${GREEN}✅ Migrations applied successfully!${NC}"
        echo ""
        echo "$UPGRADE_OUTPUT" | grep "Running upgrade"
    else
        echo -e "${GREEN}✅ Database already up to date!${NC}"
    fi
else
    echo -e "${RED}❌ Migration failed!${NC}"
    echo ""
    echo "$UPGRADE_OUTPUT"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Final Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

unset DEBUG
FINAL=$(alembic current 2>&1)
echo -e "${GREEN}✅ Current revision:${NC}"
echo "$FINAL"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Migration completed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd ..
