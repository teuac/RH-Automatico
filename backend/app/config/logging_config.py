import os
import logging
from logging.handlers import RotatingFileHandler

# Define logs directory relative to project root
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Common Formatter
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_logger(name: str, filename: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger is already initialized
    if not logger.handlers:
        # File Handler with rotation (10MB max size, keeping 5 backups)
        file_path = os.path.join(LOGS_DIR, filename)
        file_handler = RotatingFileHandler(file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Stream Handler (console output)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Initialize system loggers
system_logger = setup_logger("system", "system.log")
app_logger = setup_logger("application", "app.log")
audit_logger = setup_logger("audit", "audit.log")
error_logger = setup_logger("error", "error.log", level=logging.ERROR)
