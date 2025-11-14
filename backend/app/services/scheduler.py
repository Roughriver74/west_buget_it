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
    Scheduled task: Import credit portfolio data from FTP for all departments

    Runs daily at 8:00 AM Moscow time (Europe/Moscow timezone)
    """
    logger.info("Starting scheduled credit portfolio import")

    try:
        from app.services.credit_portfolio_ftp import download_credit_portfolio_files
        from app.services.credit_portfolio_importer import CreditPortfolioImporter

        # Download files from FTP (common for all departments)
        downloaded_files = download_credit_portfolio_files()

        if not downloaded_files:
            logger.warning("No files downloaded from FTP server")
            return

        logger.info(f"Downloaded {len(downloaded_files)} files from FTP")

        # Get database session
        db: Session = SessionLocal()

        try:
            # Get all active departments
            departments = db.query(Department).filter(Department.is_active == True).all()

            if not departments:
                logger.warning("No active departments found")
                return

            # Import for each department
            total_success = 0
            total_failed = 0

            for dept in departments:
                logger.info(f"Importing credit portfolio for department: {dept.name} (id={dept.id})")

                try:
                    # Create importer for this department
                    importer = CreditPortfolioImporter(db, dept.id)

                    # Import files
                    summary = importer.import_files(downloaded_files)

                    total_success += summary["success"]
                    total_failed += summary["failed"]

                    logger.info(
                        f"Department {dept.name}: {summary['success']}/{summary['total']} files imported"
                    )

                except Exception as e:
                    logger.error(f"Error importing for department {dept.name}: {e}")
                    total_failed += len(downloaded_files)

            logger.info(
                f"Scheduled import completed: {total_success} files imported, "
                f"{total_failed} failed across all departments"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in scheduled credit portfolio import: {e}", exc_info=True)


def start_scheduler():
    """
    Start background scheduler with all scheduled tasks

    Tasks:
    - Credit Portfolio Import: Daily at 8:00 AM Moscow time
    """
    scheduler = get_scheduler()

    # Credit Portfolio Import - Daily at 8:00 AM Moscow time
    scheduler.add_job(
        import_credit_portfolio_task,
        CronTrigger(hour=8, minute=0, timezone='Europe/Moscow'),
        id='credit_portfolio_import',
        name='Import Credit Portfolio Data from FTP',
        replace_existing=True,
        max_instances=1  # Prevent concurrent runs
    )

    logger.info("Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id}, Next run: {job.next_run_time})")

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
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "running": True,
        "jobs": jobs
    }
