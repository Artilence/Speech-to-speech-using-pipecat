"""
Logging configuration for voice chat application
"""

import sys
from loguru import logger
from typing import Optional


def setup_logging(level: str = "INFO", format_string: Optional[str] = None):
    """Setup logging configuration"""
    
    # Remove default handler
    logger.remove()
    
    # Custom format if not provided
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add new handler with custom format
    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    return logger


def get_logger(name: str = __name__):
    """Get a logger instance"""
    return logger.bind(name=name)