import logging
import logging.handlers
from queue import Queue
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)  # Make sure to import concurrent.futures
from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor
from email_sender import EmailSender
from job_details import JobDetails
from postgres_db import PostgresDB
from dotenv import load_dotenv
import os

class MaxLengthFilter(logging.Filter):
    def __init__(self, max_length):
        super().__init__()
        self.max_length = max_length

    def filter(self, record):
        if len(record.msg) > self.max_length:
            record.msg = record.msg[:self.max_length] + '...'
        return True


def init_database():
    """Initialize the database connection and create necessary tables."""
    # Load environment variables from .env file
    load_dotenv()
    logging.info("Environment variables loaded from .env file.")

    # Retrieve database configuration from environment variables
    db_config = {
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    logging.debug(f"Database configuration: {db_config}")

    # Initialize the PostgresDB instance
    try:
        db = PostgresDB(**db_config)
        logging.info("Database connection established successfully.")
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        raise

    # Initialize the JobDetails instance
    try:
        job_details = JobDetails(db)
        logging.info("JobDetails instance created successfully.")
    except Exception as e:
        logging.error(f"Failed to create JobDetails instance: {e}")
        raise

    # Create the job_details table
    try:
        job_details.create_table()
        logging.info("job_details table ensured to exist.")
    except Exception as e:
        logging.error(f"Failed to create job_details table: {e}")
        raise

    return job_details

def setup_logging(max_log_length=1000):
    """Setup logging with a single StreamHandler."""
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to prevent duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Setup the logging format
    formatter = logging.Formatter(
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




def main():   
    # Setup logging with a maximum length for each log entry
    logger = setup_logging(max_log_length=500)  
    
    logger.info("Starting application.")
    
    # Initialize the database and JobDetails
    job_details = init_database()    
    logging.info("Database initialized successfully.")
            
    # Initialize the necessary components
    try:
        logger.info("Initializing the email sender.")
        email_sender = EmailSender(
            smtp_server=os.getenv("SMTP_SERVER"),
            smtp_port=int(os.getenv("SMTP_PORT", "25")),
            username=os.getenv("EMAIL_USERNAME"),
            password=os.getenv("EMAIL_PASSWORD"),
        )
        logger.info("Email sender initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize EmailSender: {e}")
        return

    try:
        logger.info("Initializing the email processor.")
        email_processor = EmailProcessor()
        logger.info("Email processor initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize EmailProcessor: {e}")
        return

    try:
        logger.info("Initializing the job application processor.")
        job_application_processor = JobApplicationProcessor(
            email_sender, job_details
        )
        logger.info("Job application processor initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize JobApplicationProcessor: {e}")
        return

    logger.info("Starting to fetch and process jobs from emails.")

    try:
        for jobs, message_id in email_processor.fetch_jobs():
            logger.info(f"Processing jobs for email: {message_id}")
            job_application_processor.process_jobs_from_email(
                jobs, message_id, email_processor
            )
            logger.info(f"Finished processing jobs for email: {message_id}")
    except Exception as e:
        logger.error(f"An error occurred during email fetching and processing: {e}")
        return

    logger.info("Finished processing all emails.")



if __name__ == "__main__":
    main()
