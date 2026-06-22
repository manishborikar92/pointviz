import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import LOGGER_NAME, LOG_SUBDIR, LOG_FILENAME, LOG_MAX_BYTES, LOG_BACKUP_COUNT

logger = logging.getLogger(LOGGER_NAME)

def setup_logging(level=logging.INFO):
    """Set up loggers for console output and a rotating log file in user home directory."""
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. File Handler
    try:
        log_dir = Path.home() / LOG_SUBDIR
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / LOG_FILENAME
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging initialized. Log file located at: {log_file}")
    except Exception as e:
        # Fallback if home directory log path is not writeable
        logger.warning(f"Could not initialize file logging: {e}. Console logging only.")
        
    return logger
