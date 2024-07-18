import logging
import os
import json
from datetime import datetime
from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor

def setup_logging(log_directory: str):
    # Create the log directory if it doesn't exist
    os.makedirs(log_directory, exist_ok=True)

    # Create a log file with the current date as the filename
    log_filename = os.path.join(log_directory, f"{datetime.now().strftime('%Y-%m-%d')}.log")

    # Configure the logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create handlers
    file_handler = logging.FileHandler(log_filename)
    console_handler = logging.StreamHandler()

    # Create formatters and add them to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return log_filename

def main():
    # Directory for log files
    log_directory = "log"
    log_filename = setup_logging(log_directory)
    
    logger = logging.getLogger(__name__)  # Get a specific logger for this module
    logger.debug(f"Log file created: {log_filename}")

    # Filename for saving jobs
    jobs_filename = 'jobs.json'

    # Check if jobs file exists
    if os.path.exists(jobs_filename):
        with open(jobs_filename, 'r') as file:
            jobs = json.load(file)
        logger.info(f"Loaded jobs from {jobs_filename}")
    else:
        # Initialize email processor
        email_processor = EmailProcessor()

        # Fetch jobs from email
        jobs = email_processor.fetch_jobs()

        # Save jobs to a file for debugging purposes
        with open(jobs_filename, 'w') as file:
            json.dump(jobs, file)
        logger.info(f"Saved jobs to {jobs_filename}")

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