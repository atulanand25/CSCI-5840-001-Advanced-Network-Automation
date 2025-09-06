"""
Shared logging configuration for all SNMP scripts.

This module provides a standardized way to configure logging across the
application. It sets up a logger that writes to both a file and the console,
with configurable log levels and formats.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(log_name, log_file, level=logging.INFO):
    """
    Configures and returns a logger.

    Args:
        log_name (str): The name for the logger.
        log_file (str): The file path to save logs to.
        level (int, optional): The logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: A configured logger instance.
    """
    # Create the logger
    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    # Prevent logs from propagating to the root logger
    logger.propagate = False

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create a rotating file handler
    # Rotates logs when they reach 2MB, keeping 5 backup files.
    file_handler = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger if they aren't already added
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
