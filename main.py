from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor
import logging

def main():
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize email processor
    email_processor = EmailProcessor()

    # Fetch jobs from email
    jobs = email_processor.fetch_jobs()

    # Freelancer profile
    # Open the file in read mode
    freelancer_profile = ""
    with open('profile.txt', 'r') as file:
    # Read the contents of the file into a string variable
        freelancer_profile = file.read()
    if freelancer_profile == "":
        print("no profile found in profile.txt")
    # Initialize job application processor
    job_application_processor = JobApplicationProcessor()
    
    # Process and apply for jobs
    job_application_processor.process_jobs(jobs, freelancer_profile)

if __name__ == '__main__':
    main()