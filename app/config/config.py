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
        
def setup_logging(max_log_length=1000):
    """Setup logging with a single StreamHandler."""
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

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

    # Add the handler to the root logger
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
    DB_PASSWORD = os.getenv('DB_PASSWORD')
