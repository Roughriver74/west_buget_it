#!/usr/bin/env python
"""
Standalone scheduler process for background tasks

This script runs as a separate process to avoid conflicts with uvicorn workers.
It starts the APScheduler and keeps it running until interrupted.
"""
import asyncio
import signal
import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from app.utils.logger import logger, log_info, log_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    log_info("Received shutdown signal, stopping scheduler...", "Scheduler")
    stop_scheduler()
    sys.exit(0)

async def main():
    """Main function to run scheduler"""
    log_info("Starting standalone scheduler process", "Scheduler")

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start scheduler
        start_scheduler()

        # Get status
        status = get_scheduler_status()
        log_info(
            f"Scheduler started successfully: "
            f"Running={status['running']}, Jobs={len(status['jobs'])}",
            "Scheduler"
        )

        # Keep process alive
        log_info("Scheduler is running. Press Ctrl+C to stop.", "Scheduler")

        while True:
            await asyncio.sleep(60)  # Check every minute

            # Verify scheduler is still running
            status = get_scheduler_status()
            if not status['running']:
                log_error("Scheduler stopped unexpectedly!", "Scheduler")
                sys.exit(1)

    except KeyboardInterrupt:
        log_info("Keyboard interrupt received", "Scheduler")
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
        sys.exit(1)
    finally:
        stop_scheduler()
        log_info("Scheduler stopped", "Scheduler")

if __name__ == "__main__":
    asyncio.run(main())
