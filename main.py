import logging
import os
from datetime import datetime
from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor

class FlushableStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()
        
class MaxLengthFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', max_length=100):
        super().__init__(fmt, datefmt, style)
        self.max_length = max_length

    def format(self, record):
        original_message = super().format(record)
        if len(original_message) > self.max_length:
            return original_message[:self.max_length] + '...'
        return original_message

def setup_logging(log_directory: str, max_length: int):
    # Create the log directory if it doesn't exist
    os.makedirs(log_directory, exist_ok=True)

    # Create a log file with the current date as the filename
    log_filename = os.path.join(log_directory, f"{datetime.now().strftime('%Y-%m-%d')}.log")

    # Configure the logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create handlers
    file_handler = logging.FileHandler(log_filename, mode="w")
    console_handler = FlushableStreamHandler()

    # Create formatters and add them to the handlers
    formatter = MaxLengthFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', max_length=max_length)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.propagate = False

    return log_filename



def main():
    # Directory for log files
    log_directory = "log"
    max_log_length = 500  # Specify the maximum length for log messages
    log_filename = setup_logging(log_directory, max_log_length)
    
    logger = logging.getLogger(__name__)  # Get a specific logger for this module
    logger.debug(f"Log file created: {log_filename}")

    # Initialize email processor
    email_processor = EmailProcessor()

    # Fetch jobs from email
    jobs = email_processor.fetch_jobs()

    # Display the list of job titles
    logger.info("List of job titles fetched:")
    for job in jobs:
        logger.info(f"- {job['title']}")

    # Pause and wait for a key press
    input("Press any key to continue...")

    # Freelancer profile
    freelancer_profile = ""
    try:
        with open('profile.txt', 'r') as file:
            freelancer_profile = file.read()
        if freelancer_profile == "":
            logger.error("No profile found in profile.txt")
            return
        logger.info("Profile found in profile.txt")
    except FileNotFoundError:
        logger.error("profile.txt not found")
        return

    # Initialize job application processor
    job_application_processor = JobApplicationProcessor()

    # Process and apply for jobs
    job_application_processor.process_jobs(jobs, freelancer_profile)

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()