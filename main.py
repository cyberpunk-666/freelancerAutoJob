from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor
import logging
import os
import json
from datetime import datetime

def main():
    
    # Directory for log files
    log_directory = "log"
    os.makedirs(log_directory, exist_ok=True)  # Create the directory if it doesn't exist
    
    # Create a log file with the current date as the filename
    log_filename = os.path.join(log_directory, f"{datetime.now().strftime('%Y-%m-%d')}.log")
    
    # Configure the logger
    logging.basicConfig(
        level=logging.DEBUG,  # Minimum log level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
        datefmt='%Y-%m-%d %H:%M:%S',  # Date format
        handlers=[
            logging.FileHandler(log_filename),  # Log file
            logging.StreamHandler()  # Console output
        ]
    )

    # Filename for saving jobs
    jobs_filename = 'jobs.json'

    # Check if jobs file exists
    if os.path.exists(jobs_filename):
        with open(jobs_filename, 'r') as file:
            jobs = json.load(file)
        logging.info(f"Loaded jobs from {jobs_filename}")
    else:
        # Initialize email processor
        email_processor = EmailProcessor()

        # Fetch jobs from email
        jobs = email_processor.fetch_jobs()

        # Save jobs to a file for debugging purposes
        with open(jobs_filename, 'w') as file:
            json.dump(jobs, file)
        logging.info(f"Saved jobs to {jobs_filename}")

    # Freelancer profile
    freelancer_profile = ""
    try:
        with open('profile.txt', 'r') as file:
            freelancer_profile = file.read()
        if freelancer_profile == "":
            logging.error("No profile found in profile.txt")
            return
        else:
            logging.info("Profile found in profile.txt")
    except FileNotFoundError:
        logging.error("profile.txt not found")
        return

    # Initialize job application processor
    job_application_processor = JobApplicationProcessor()
    
    # Process and apply for jobs
    job_application_processor.process_jobs(jobs, freelancer_profile)

if __name__ == '__main__':
    main()