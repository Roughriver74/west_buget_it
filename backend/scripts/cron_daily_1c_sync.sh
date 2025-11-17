#!/bin/bash

# Cron job for daily 1C catalogs synchronization
# Schedule: Daily at 02:00 AM
# Add to crontab: 0 2 * * * /path/to/backend/scripts/cron_daily_1c_sync.sh

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Log file
LOG_FILE="$BACKEND_DIR/logs/1c_catalog_sync.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting 1C catalogs synchronization"
log "=========================================="

# Change to backend directory
cd "$BACKEND_DIR" || {
    log "ERROR: Failed to change to backend directory"
    exit 1
}

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    log "Activating virtual environment..."
    source venv/bin/activate
else
    log "WARNING: Virtual environment not found, using system Python"
fi

# Get all department IDs from database
log "Fetching department IDs..."
DEPARTMENT_IDS=$(docker exec it_budget_db psql -U budget_user -d it_budget_db -t -c "SELECT id FROM departments WHERE is_active = true ORDER BY id;")

if [ -z "$DEPARTMENT_IDS" ]; then
    log "ERROR: No active departments found"
    exit 1
fi

# Sync for each department
TOTAL_DEPTS=0
SUCCESS_DEPTS=0
FAILED_DEPTS=0

while IFS= read -r DEPT_ID; do
    DEPT_ID=$(echo "$DEPT_ID" | xargs)  # Trim whitespace

    if [ -z "$DEPT_ID" ]; then
        continue
    fi

    TOTAL_DEPTS=$((TOTAL_DEPTS + 1))

    log ""
    log "Syncing department ID: $DEPT_ID"
    log "------------------------------------------"

    # Run sync script for this department
    if DEBUG=true python3 scripts/sync_1c_catalogs_auto.py --department-id "$DEPT_ID" --all >> "$LOG_FILE" 2>&1; then
        log "✅ Department $DEPT_ID synced successfully"
        SUCCESS_DEPTS=$((SUCCESS_DEPTS + 1))
    else
        log "❌ Department $DEPT_ID sync failed"
        FAILED_DEPTS=$((FAILED_DEPTS + 1))
    fi

done <<< "$DEPARTMENT_IDS"

# Summary
log ""
log "=========================================="
log "Synchronization Summary:"
log "  Total departments: $TOTAL_DEPTS"
log "  Successful: $SUCCESS_DEPTS"
log "  Failed: $FAILED_DEPTS"
log "=========================================="

if [ "$FAILED_DEPTS" -gt 0 ]; then
    exit 1
else
    exit 0
fi
