#!/usr/bin/env python3
"""
Cron script for automated FTP import of expenses
Runs every 2 hours to synchronize expenses from FTP server
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.services.ftp_import_service import import_from_ftp


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


async def run_import():
    """Run FTP import"""
    log("=" * 60)
    log("Starting automated FTP import")
    log("=" * 60)

    # Get FTP credentials from environment variables
    ftp_host = os.getenv("FTP_HOST", "floppisw.beget.tech")
    ftp_user = os.getenv("FTP_USER", "floppisw_zrds")
    ftp_pass = os.getenv("FTP_PASS", "4yZUaloOBmU!")
    remote_path = os.getenv("FTP_REMOTE_PATH", "/Zayavki na raszkhod(spisok) XLSX.xlsx")

    log(f"FTP Server: {ftp_host}")
    log(f"FTP User: {ftp_user}")
    log(f"Remote file: {remote_path}")

    db = SessionLocal()

    try:
        # Run import with skip_duplicates=True (don't update existing)
        result = await import_from_ftp(
            db=db,
            host=ftp_host,
            username=ftp_user,
            password=ftp_pass,
            remote_path=remote_path,
            delete_from_year=None,  # Don't delete old data
            delete_from_month=None,
            skip_duplicates=True,  # Skip duplicates
            default_department_id=None
        )

        log("")
        log("Import completed successfully!")
        log(f"  Total in file: {result['total_in_file']}")
        log(f"  Created: {result['created']}")
        log(f"  Updated: {result['updated']}")
        log(f"  Skipped: {result['skipped']}")
        log(f"  Deleted: {result['deleted']}")
        log("=" * 60)

        return True

    except Exception as e:
        log(f"❌ Import failed: {e}")
        import traceback
        log(traceback.format_exc())
        log("=" * 60)
        return False
    finally:
        db.close()


def main():
    """Main entry point"""
    success = asyncio.run(run_import())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
