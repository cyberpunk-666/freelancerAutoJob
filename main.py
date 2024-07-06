from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor

def main():
    # Initialize email processor
    email_processor = EmailProcessor()

    # Fetch jobs from email
    jobs = email_processor.fetch_jobs()

    # Freelancer profile (this should be provided or loaded from a file)
    freelancer_profile = """
    - Experienced Python Developer with over 5 years of experience.
    - Proficient in web scraping, data analysis, and automation.
    - Strong background in web development using frameworks like Django and Flask.
    - Excellent problem-solving skills and ability to work independently.
    """
    
    # Initialize job application processor
    job_application_processor = JobApplicationProcessor()
    
    # Process and apply for jobs
    job_application_processor.process_jobs(jobs, freelancer_profile)

if __name__ == '__main__':
    main()