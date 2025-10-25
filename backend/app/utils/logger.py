"""
Logging configuration for the application
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Define log levels
LOG_LEVEL = logging.INFO


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

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation (10MB max, keep 5 backup files)
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
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
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
        DATE_FORMAT
    )
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)

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
