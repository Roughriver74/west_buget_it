"""
Background scheduler for automated tasks
Uses APScheduler for periodic task execution
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Department
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def import_credit_portfolio_task():
    """
    Scheduled task: Import credit portfolio data from FTP

    Credit portfolio is ONLY tied to Finance department (ID=8)
    Runs daily at configurable time (default: 6:00 AM Moscow time)
    """
    logger.info("Starting scheduled credit portfolio import")

    # Finance department ID (credit portfolio is exclusive to Finance)
    FINANCE_DEPARTMENT_ID = 8

    try:
        from app.services.credit_portfolio_ftp import download_credit_portfolio_files
        from app.services.credit_portfolio_importer import CreditPortfolioImporter

        # Download files from FTP
        logger.info("Downloading files from FTP...")
        downloaded_files = download_credit_portfolio_files()

        if not downloaded_files:
            logger.warning("No files downloaded from FTP server")
            return

        logger.info(f"Downloaded {len(downloaded_files)} files from FTP")

        # Get database session
        db: Session = SessionLocal()

        try:
            # Import for Finance department only
            logger.info(f"Importing credit portfolio for Finance department (ID={FINANCE_DEPARTMENT_ID})")

            importer = CreditPortfolioImporter(db, FINANCE_DEPARTMENT_ID)
            summary = importer.import_files(downloaded_files)

            # Invalidate analytics cache after successful import
            if summary["success"] > 0:
                try:
                    from app.api.v1.credit_portfolio import invalidate_analytics_cache
                    invalidate_analytics_cache()
                    logger.info(f"Invalidated analytics cache after importing {summary['success']} files")
                except Exception as cache_err:
                    logger.warning(f"Failed to invalidate cache: {cache_err}")

            logger.info(
                f"Scheduled import completed: {summary['success']}/{summary['total']} files imported, "
                f"{summary['failed']} failed"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in scheduled credit portfolio import: {e}", exc_info=True)


def start_scheduler():
    """
    Start background scheduler with all scheduled tasks

    Tasks:
    - Credit Portfolio Import: Configurable schedule (default: Daily at 6:00 AM Moscow time)

    Configuration via environment variables:
    - SCHEDULER_ENABLED: Enable/disable scheduler (default: true)
    - CREDIT_PORTFOLIO_IMPORT_ENABLED: Enable credit portfolio auto-import (default: true)
    - CREDIT_PORTFOLIO_IMPORT_HOUR: Hour for import (0-23, default: 6)
    - CREDIT_PORTFOLIO_IMPORT_MINUTE: Minute for import (0-59, default: 0)
    """
    # Check if scheduler is enabled
    scheduler_enabled = getattr(settings, 'SCHEDULER_ENABLED', True)
    if not scheduler_enabled:
        logger.info("Background scheduler is disabled via SCHEDULER_ENABLED setting")
        return

    scheduler = get_scheduler()

    # Credit Portfolio Import - Configurable schedule
    import_enabled = getattr(settings, 'CREDIT_PORTFOLIO_IMPORT_ENABLED', True)
    if import_enabled:
        import_hour = getattr(settings, 'CREDIT_PORTFOLIO_IMPORT_HOUR', 6)
        import_minute = getattr(settings, 'CREDIT_PORTFOLIO_IMPORT_MINUTE', 0)

        scheduler.add_job(
            import_credit_portfolio_task,
            CronTrigger(hour=import_hour, minute=import_minute, timezone='Europe/Moscow'),
            id='credit_portfolio_import',
            name='Import Credit Portfolio Data from FTP',
            replace_existing=True,
            max_instances=1  # Prevent concurrent runs
        )

        logger.info(f"Credit portfolio import scheduled: Daily at {import_hour:02d}:{import_minute:02d} Moscow time")
    else:
        logger.info("Credit portfolio auto-import is disabled via CREDIT_PORTFOLIO_IMPORT_ENABLED setting")

    logger.info("Scheduled jobs:")
    for job in scheduler.get_jobs():
        try:
            next_run = job.next_run_time if hasattr(job, 'next_run_time') else 'N/A'
        except:
            next_run = 'N/A'
        logger.info(f"  - {job.name} (ID: {job.id}, Next run: {next_run})")

    # Start scheduler
    scheduler.start()
    logger.info("Background scheduler started successfully")


def stop_scheduler():
    """Stop background scheduler"""
    scheduler = get_scheduler()
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


def get_scheduler_status():
    """
    Get scheduler status and job information

    Returns:
        dict: Scheduler status and jobs
    """
    scheduler = get_scheduler()

    if not scheduler or not scheduler.running:
        return {
            "running": False,
            "jobs": []
        }

    jobs = []
    for job in scheduler.get_jobs():
        try:
            next_run_time = job.next_run_time if hasattr(job, 'next_run_time') else None
        except:
            next_run_time = None

        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(next_run_time) if next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "running": True,
        "jobs": jobs
    }
