import logging
import logging.handlers
import queue
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed  # Make sure to import concurrent.futures
from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor
from email_sender import EmailSender
from summary_storage import SummaryStorage
import os

def setup_logging():
    """Setup logging with QueueHandler for thread-safe logging."""
    log_queue = Queue()

    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Setup the logging format
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

    # Setup a StreamHandler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create a QueueHandler and attach it to the root logger
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    # Create a QueueListener to listen for log records in the main thread
    queue_listener = logging.handlers.QueueListener(log_queue, console_handler)
    queue_listener.start()

    return queue_listener

def main():
    # Setup logging and start QueueListener
    queue_listener = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the email processing application.")

    # Initialize the necessary components
    try:
        logger.info("Initializing the email sender.")
        email_sender = EmailSender(
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', '25')),
            username=os.getenv('EMAIL_USERNAME'),
            password=os.getenv('EMAIL_PASSWORD')
        )
        logger.info("Email sender initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize EmailSender: {e}")
        return

    try:
        logger.info("Initializing the summary storage.")
        summary_storage = SummaryStorage()
        logger.info("Summary storage initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize SummaryStorage: {e}")
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
        job_application_processor = JobApplicationProcessor(email_sender, summary_storage)
        logger.info("Job application processor initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize JobApplicationProcessor: {e}")
        return

    logger.info("Starting to fetch and process jobs from emails.")
    
    # Fetch and process jobs in parallel, one email at a time
    try:
        for jobs, message_id in email_processor.fetch_jobs():
            logger.info(f"Processing jobs for email: {message_id}")
            job_application_processor.process_jobs_from_email(jobs, message_id, email_processor)
            logger.info(f"Finished processing jobs for email: {message_id}")
    except Exception as e:
        logger.error(f"An error occurred during email fetching and processing: {e}")
        return

    logger.info("Finished processing all emails.")

    # Stop the QueueListener to clean up
    queue_listener.stop()

if __name__ == '__main__':
    main()
