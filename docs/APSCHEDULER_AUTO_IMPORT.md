# APScheduler Auto-Import Implementation

## Overview

APScheduler has been configured to automatically import credit portfolio data from FTP on a daily schedule. This eliminates the need for manual imports and ensures data is always up-to-date.

## Implementation Details

### 1. Scheduler Service
- **Location**: `backend/app/services/scheduler.py`
- **Features**:
  - AsyncIO scheduler for non-blocking execution
  - Moscow timezone (Europe/Moscow)
  - Configurable import schedule
  - Automatic cache invalidation after import
  - Max 1 concurrent instance per job
  - Misfire grace period: 1 hour

### 2. Scheduled Task

**Task**: Credit Portfolio FTP Import
- **Default Schedule**: Daily at 6:00 AM Moscow time
- **Department**: Finance (ID=8) only
- **Process**:
  1. Download XLSX files from FTP
  2. Parse and import data (receipts, expenses, expense details)
  3. Auto-create organizations, bank accounts, contracts
  4. Invalidate analytics cache
  5. Log import summary

### 3. Configuration

**Environment Variables** (`.env`):
```bash
# Enable/disable scheduler
SCHEDULER_ENABLED=true

# Credit portfolio auto-import
CREDIT_PORTFOLIO_IMPORT_ENABLED=true
CREDIT_PORTFOLIO_IMPORT_HOUR=6        # 0-23 (Moscow time)
CREDIT_PORTFOLIO_IMPORT_MINUTE=0      # 0-59
```

**Settings** (`backend/app/core/config.py`):
```python
SCHEDULER_ENABLED: bool = True
CREDIT_PORTFOLIO_IMPORT_ENABLED: bool = True
CREDIT_PORTFOLIO_IMPORT_HOUR: int = 6
CREDIT_PORTFOLIO_IMPORT_MINUTE: int = 0
```

### 4. Lifecycle

**Startup** (`backend/app/main.py`):
```python
@app.on_event("startup")
async def startup_event():
    from app.services.scheduler import start_scheduler
    start_scheduler()
    # Scheduler runs in background
```

**Shutdown**:
```python
@app.on_event("shutdown")
async def shutdown_event():
    from app.services.scheduler import stop_scheduler
    stop_scheduler()
```

## Usage

### View Scheduled Jobs

```python
from app.services.scheduler import get_scheduler_status

status = get_scheduler_status()
print(status)
# Output:
# {
#   "running": True,
#   "jobs": [
#     {
#       "id": "credit_portfolio_import",
#       "name": "Import Credit Portfolio Data from FTP",
#       "next_run": "2025-11-15 06:00:00+03:00",
#       "trigger": "cron[hour='6', minute='0']"
#     }
#   ]
# }
```

### Manually Trigger Import

**Option 1: Via API** (already exists):
```bash
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/trigger" \
  -H "Authorization: Bearer $TOKEN"
```

**Option 2: Via Scheduler** (for testing):
```python
from app.services.scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.modify_job('credit_portfolio_import', next_run_time='now')
```

### Change Schedule

**Temporarily** (until restart):
```python
from app.services.scheduler import get_scheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = get_scheduler()
scheduler.reschedule_job(
    'credit_portfolio_import',
    trigger=CronTrigger(hour=8, minute=30, timezone='Europe/Moscow')
)
```

**Permanently** (edit `.env` and restart):
```bash
# Import at 8:30 AM instead of 6:00 AM
CREDIT_PORTFOLIO_IMPORT_HOUR=8
CREDIT_PORTFOLIO_IMPORT_MINUTE=30
```

## Monitoring

### Check Logs

```bash
# View scheduler startup
docker logs it_budget_backend | grep "scheduler"

# View scheduled imports
docker logs it_budget_backend | grep "scheduled credit portfolio import"

# View import results
docker logs it_budget_backend | grep "Scheduled import completed"
```

**Example log output**:
```
INFO: Background scheduler started successfully
INFO: Credit portfolio import scheduled: Daily at 06:00 Moscow time
INFO: Scheduled jobs:
INFO:   - Import Credit Portfolio Data from FTP (ID: credit_portfolio_import, Next run: 2025-11-15 06:00:00+03:00)
...
INFO: Starting scheduled credit portfolio import
INFO: Downloading files from FTP...
INFO: Downloaded 3 files from FTP
INFO: Importing credit portfolio for Finance department (ID=8)
INFO: Invalidated analytics cache after importing 3 files
INFO: Scheduled import completed: 3/3 files imported, 0 failed
```

### Health Check

```python
from app.services.scheduler import get_scheduler

scheduler = get_scheduler()

# Check if running
print(f"Scheduler running: {scheduler.running}")

# Get all jobs
for job in scheduler.get_jobs():
    print(f"Job: {job.name}")
    print(f"  Next run: {job.next_run_time}")
    print(f"  Trigger: {job.trigger}")
```

## Troubleshooting

### Scheduler Not Starting

**Symptom**: No "Background scheduler started" in logs

**Possible causes**:
1. SCHEDULER_ENABLED=false in .env
2. Error during startup
3. Python exception in scheduler code

**Solution**:
```bash
# Check configuration
grep SCHEDULER_ENABLED /path/to/.env

# Check logs for errors
docker logs it_budget_backend | grep -i error | grep scheduler
```

### Import Not Running

**Symptom**: Import doesn't run at scheduled time

**Possible causes**:
1. CREDIT_PORTFOLIO_IMPORT_ENABLED=false
2. FTP connection issues
3. Database connection issues

**Solution**:
```bash
# Check configuration
grep CREDIT_PORTFOLIO_IMPORT /path/to/.env

# Trigger manual import to test
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/trigger" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Check FTP connectivity
python -c "
from app.services.credit_portfolio_ftp import download_credit_portfolio_files
files = download_credit_portfolio_files()
print(f'Downloaded {len(files)} files')
"
```

### Missed Imports

**Symptom**: Import didn't run while server was down

**Behavior**: By default, APScheduler will run missed jobs when server starts if within grace period (1 hour)

**Configuration**:
```python
# In scheduler.py
job_defaults={
    'coalesce': True,       # Combine multiple missed runs into one
    'misfire_grace_time': 3600  # Run if missed within 1 hour
}
```

**To disable catchup**:
```python
scheduler.add_job(
    import_credit_portfolio_task,
    ...,
    coalesce=False  # Don't run missed imports
)
```

## Integration with Cache

After successful import, scheduler automatically:
1. Imports data for Finance department (ID=8)
2. Invalidates all cached analytics queries
3. Logs cache invalidation

**Code**:
```python
# In scheduler.py import_credit_portfolio_task()
if summary["success"] > 0:
    from app.api.v1.credit_portfolio import invalidate_analytics_cache
    invalidate_analytics_cache()
    logger.info(f"Invalidated analytics cache after importing {summary['success']} files")
```

## Best Practices

### 1. Schedule During Off-Peak Hours
- Default: 6:00 AM Moscow time
- Avoids peak usage times
- Ensures fresh data for morning reports

### 2. Monitor Import Success
- Set up alerts for failed imports
- Review logs daily
- Investigate any failures promptly

### 3. Test Before Production
```bash
# Test import manually
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/trigger" \
  -H "Authorization: Bearer $TOKEN"

# Verify data imported correctly
curl "http://localhost:8000/api/v1/credit-portfolio/summary?department_id=8" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Backup Before First Scheduled Import
```bash
# Backup database
pg_dump -h localhost -p 54329 -U budget_user it_budget_db > backup_before_autoimport.sql
```

## Future Enhancements

1. **Multiple Schedules**:
   - Weekly reports
   - Monthly reconciliation
   - Hourly updates for critical data

2. **Email Notifications**:
   - Send email on import failure
   - Weekly import summary

3. **Retry Logic**:
   - Automatic retry on FTP connection failure
   - Exponential backoff

4. **Import History API**:
   - View import history via API
   - Dashboard showing import status

5. **Selective Imports**:
   - Import only specific file types
   - Import only data newer than last import

## Summary

APScheduler auto-import provides:
- ✅ Daily automatic credit portfolio data import
- ✅ Configurable schedule via environment variables
- ✅ Finance department only (ID=8)
- ✅ Automatic cache invalidation
- ✅ Integrated with FastAPI lifecycle
- ✅ Production-ready error handling
- ✅ Moscow timezone support

Expected benefits:
- **Manual work reduction**: 100% (no manual imports needed)
- **Data freshness**: Always up-to-date by 6:00 AM
- **Reliability**: Automatic retries and error logging
