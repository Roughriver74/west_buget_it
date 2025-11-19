"""
Logging configuration for the application
"""
import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Define log levels - environment-based configuration
# Development: INFO, Production: WARNING, Debug: DEBUG
_LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
_LOG_LEVEL_ENV = os.getenv('LOG_LEVEL', 'WARNING').upper()
LOG_LEVEL = _LOG_LEVEL_MAP.get(_LOG_LEVEL_ENV, logging.WARNING)

# Check if running in production (Docker container)
IS_PRODUCTION = os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true' or os.path.exists('/app')


def setup_logger(name: str = "app", level: int = LOG_LEVEL) -> logging.Logger:
    """
    Setup and configure logger

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler - always enabled
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handlers - only in development (not in Docker)
    if not IS_PRODUCTION:
        try:
            # Create logs directory if it doesn't exist
            LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
            LOGS_DIR.mkdir(exist_ok=True)

            # File handler with rotation (5MB max, keep 3 backup files)
            log_file = LOGS_DIR / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB (reduced from 10MB)
                backupCount=3,  # Reduced from 5
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # Error file handler - only errors and critical
            error_log_file = LOGS_DIR / f"{name}_errors.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB (reduced from 10MB)
                backupCount=3,  # Reduced from 5
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
                DATE_FORMAT
            )
            error_handler.setFormatter(error_formatter)
            logger.addHandler(error_handler)
        except Exception as e:
            # If file logging fails, just use console
            logger.warning(f"Could not setup file logging: {e}")

    return logger


# Create default logger
logger = setup_logger("app")


def log_request(method: str, path: str, user: str = "anonymous"):
    """Log HTTP request"""
    logger.info(f"Request: {method} {path} - User: {user}")


def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)


def log_warning(message: str, context: str = ""):
    """Log warning with context"""
    logger.warning(f"{context}: {message}")


def log_info(message: str, context: str = ""):
    """Log info message with context"""
    logger.info(f"{context}: {message}")


def log_debug(message: str, context: str = ""):
    """Log debug message with context"""
    logger.debug(f"{context}: {message}")
