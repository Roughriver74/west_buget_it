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


async def create_monthly_employee_kpis_task():
    """
    Scheduled task: Auto-create EmployeeKPI records for all active employees

    Runs on the 1st day of each month at 00:01 AM Moscow time
    Creates EmployeeKPI records with DRAFT status for the current month
    Copies goals from previous month or creates default goals
    """
    logger.info("Starting automatic EmployeeKPI creation for current month")

    try:
        from datetime import datetime
        from app.services.employee_kpi_auto_creator import EmployeeKPIAutoCreator

        # Get current year and month
        now = datetime.now()
        year = now.year
        month = now.month

        logger.info(f"Creating EmployeeKPI records for {year}-{month:02d}")

        # Get database session
        db: Session = SessionLocal()

        try:
            # Create KPIs for all departments
            creator = EmployeeKPIAutoCreator(db)
            result = creator.create_monthly_kpis(year=year, month=month)

            logger.info(
                f"EmployeeKPI auto-creation completed: "
                f"{result['created']} created, {result['skipped']} skipped, {result['errors']} errors "
                f"(total {result['total_employees']} employees)"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in scheduled EmployeeKPI auto-creation: {e}", exc_info=True)


async def check_expired_modules_task():
    """
    Scheduled task: Check and deactivate expired organization modules

    Runs daily at configurable time (default: 1:00 AM Moscow time)
    - Finds all OrganizationModule records where expires_at < now() and is_active = True
    - Sets is_active = False for expired modules
    - Creates MODULE_EXPIRED events for auditing
    - Logs expired modules for admin notification
    """
    logger.info("Starting expired modules check")

    try:
        from datetime import datetime
        from app.db.models import OrganizationModule, Organization, Module, ModuleEventTypeEnum
        from app.services.module_service import ModuleService

        db: Session = SessionLocal()

        try:
            # Find expired modules that are still active
            expired_modules = db.query(OrganizationModule).join(
                Organization, OrganizationModule.organization_id == Organization.id
            ).join(
                Module, OrganizationModule.module_id == Module.id
            ).filter(
                OrganizationModule.is_active == True,
                OrganizationModule.expires_at.isnot(None),
                OrganizationModule.expires_at < datetime.utcnow()
            ).all()

            if not expired_modules:
                logger.info("No expired modules found")
                return

            logger.info(f"Found {len(expired_modules)} expired module(s)")

            module_service = ModuleService(db)
            deactivated_count = 0

            for org_module in expired_modules:
                try:
                    # Get related data
                    organization = db.query(Organization).get(org_module.organization_id)
                    module = db.query(Module).get(org_module.module_id)

                    if not organization or not module:
                        logger.warning(
                            f"Skipping OrganizationModule {org_module.id}: "
                            f"Organization or Module not found"
                        )
                        continue

                    logger.info(
                        f"Deactivating expired module: "
                        f"Organization={organization.short_name}, "
                        f"Module={module.code}, "
                        f"Expired at={org_module.expires_at}"
                    )

                    # Deactivate module
                    org_module.is_active = False
                    org_module.updated_at = datetime.utcnow()

                    # Emit MODULE_EXPIRED event
                    module_service.emit_event(
                        organization_id=org_module.organization_id,
                        module_id=org_module.module_id,
                        event_type=ModuleEventTypeEnum.MODULE_EXPIRED,
                        metadata={
                            "expired_at": org_module.expires_at.isoformat(),
                            "organization_name": organization.short_name,
                            "module_code": module.code,
                            "module_name": module.name,
                            "auto_deactivated": True
                        }
                    )

                    deactivated_count += 1

                except Exception as e:
                    logger.error(
                        f"Error deactivating OrganizationModule {org_module.id}: {e}",
                        exc_info=True
                    )

            # Commit all changes
            db.commit()

            logger.info(
                f"Expired modules check completed: "
                f"{deactivated_count}/{len(expired_modules)} modules deactivated"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in scheduled expired modules check: {e}", exc_info=True)


def start_scheduler():
    """
    Start background scheduler with all scheduled tasks

    Tasks:
    - Credit Portfolio Import: Configurable schedule (default: Daily at 6:00 AM Moscow time)
    - Employee KPI Auto-Creation: Monthly on 1st day at 00:01 AM Moscow time
    - Expired Modules Check: Daily at configurable time (default: Daily at 1:00 AM Moscow time)

    Configuration via environment variables:
    - SCHEDULER_ENABLED: Enable/disable scheduler (default: true)
    - CREDIT_PORTFOLIO_IMPORT_ENABLED: Enable credit portfolio auto-import (default: true)
    - CREDIT_PORTFOLIO_IMPORT_HOUR: Hour for import (0-23, default: 6)
    - CREDIT_PORTFOLIO_IMPORT_MINUTE: Minute for import (0-59, default: 0)
    - EMPLOYEE_KPI_AUTO_CREATE_ENABLED: Enable auto-creation of EmployeeKPI (default: true)
    - MODULE_EXPIRY_CHECK_ENABLED: Enable module expiry check (default: true)
    - MODULE_EXPIRY_CHECK_HOUR: Hour for module expiry check (0-23, default: 1)
    - MODULE_EXPIRY_CHECK_MINUTE: Minute for module expiry check (0-59, default: 0)
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

    # Employee KPI Auto-Creation - Monthly on 1st day at 00:01 AM
    kpi_auto_create_enabled = getattr(settings, 'EMPLOYEE_KPI_AUTO_CREATE_ENABLED', True)
    if kpi_auto_create_enabled:
        scheduler.add_job(
            create_monthly_employee_kpis_task,
            CronTrigger(day=1, hour=0, minute=1, timezone='Europe/Moscow'),
            id='employee_kpi_auto_create',
            name='Auto-create Monthly EmployeeKPI Records',
            replace_existing=True,
            max_instances=1  # Prevent concurrent runs
        )

        logger.info("EmployeeKPI auto-creation scheduled: Monthly on 1st day at 00:01 AM Moscow time")
    else:
        logger.info("EmployeeKPI auto-creation is disabled via EMPLOYEE_KPI_AUTO_CREATE_ENABLED setting")

    # Expired Modules Check - Daily at configurable time
    module_expiry_check_enabled = getattr(settings, 'MODULE_EXPIRY_CHECK_ENABLED', True)
    if module_expiry_check_enabled:
        expiry_check_hour = getattr(settings, 'MODULE_EXPIRY_CHECK_HOUR', 1)
        expiry_check_minute = getattr(settings, 'MODULE_EXPIRY_CHECK_MINUTE', 0)

        scheduler.add_job(
            check_expired_modules_task,
            CronTrigger(hour=expiry_check_hour, minute=expiry_check_minute, timezone='Europe/Moscow'),
            id='module_expiry_check',
            name='Check and Deactivate Expired Organization Modules',
            replace_existing=True,
            max_instances=1  # Prevent concurrent runs
        )

        logger.info(f"Module expiry check scheduled: Daily at {expiry_check_hour:02d}:{expiry_check_minute:02d} Moscow time")
    else:
        logger.info("Module expiry check is disabled via MODULE_EXPIRY_CHECK_ENABLED setting")

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
