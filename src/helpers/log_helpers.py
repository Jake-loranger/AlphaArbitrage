import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# Constants for logging
LOG_FOLDER = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

def get_logger(name: str, log_level: Optional[int] = None, print_to_console: bool = False) -> logging.Logger:
    """
    Get a logger instance with both file and console handlers.
    
    Args:
        name: The name of the logger (usually __name__)
        log_level: Optional log level override (defaults to INFO)
        print_to_console: Whether to print logs to console (defaults to True)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_FOLDER, exist_ok=True)
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Set log level
    if log_level is None:
        log_level = logging.INFO
    logger.setLevel(log_level)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    
    # Create and configure file handler
    log_file = os.path.join(LOG_FOLDER, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Add file handler to logger
    logger.addHandler(file_handler)
    
    # Add console handler only if print_to_console is True
    if print_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

def set_log_level(level: int):
    """
    Set the log level for all loggers.
    
    Args:
        level: The logging level to set (e.g., logging.DEBUG, logging.INFO)
    """
    logging.getLogger().setLevel(level)
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(level)

def log_data(message: str, level: int = logging.INFO, print_to_console: bool = False) -> None:
    """
    Log a message with the specified level.
    
    Args:
        message: The message to log
        level: The logging level (defaults to INFO)
        print_to_console: Whether to print logs to console (defaults to True)
    """
    logger = get_logger(__name__, print_to_console=print_to_console)
    logger.log(level, message)

# Example usage:
if __name__ == "__main__":
    # Get a logger for this module
    logger = get_logger(__name__)
    
    # Log messages at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Set all loggers to DEBUG level
    set_log_level(logging.DEBUG) 