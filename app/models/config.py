from dotenv import load_dotenv
import logging
from app.utils.traceback_formatter import TracebackFormatter

    
class MaxLengthFilter(logging.Filter):
    def __init__(self, max_length):
        super().__init__()
        self.max_length = max_length

    def filter(self, record):
        if len(record.msg) > self.max_length:
            record.msg = record.msg[: self.max_length] + "..."
        return True
import logging

class CustomLogger(logging.Logger):
    def error(self, msg, *args, exc_info=True, **kwargs):
        super().error(msg, *args, exc_info=exc_info, **kwargs)

def setup_logging(max_log_length=1000):
    """Setup logging with a single StreamHandler."""
    # Ensure custom logger class is used
    logging.setLoggerClass(CustomLogger)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Also set the root logger level to DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to prevent duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Setup the logging format
    formatter = TracebackFormatter(
        "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
    )

    # Setup a StreamHandler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    # Add the max length filter to the logger
    max_length_filter = MaxLengthFilter(max_log_length)
    logger.addFilter(max_length_filter)

    return logger

    
import os

# Load environment variables from a .env file
load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
