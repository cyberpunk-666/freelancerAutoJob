import os
import logging
from datetime import datetime
from flask import Flask, Response, stream_with_context
from dotenv import load_dotenv
from email_sender import EmailSender
from job_application_processor import JobApplicationProcessor
from email_processor import EmailProcessor
from summary_storage import SummaryStorage
from utils import load_template, populate_template, str_to_bool

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading environment variables from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Additional debug to check if value is set later
def check_listening_port():
    port = os.getenv('LISTENING_PORT')
    host = os.getenv('LISTENING_HOST')
    logger.debug(f"check_listening_port: {port}")
    logger.debug(f"check_listening_host: {host}")    
    return port, host

from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor

class MaxLengthFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', max_length=100):
        super().__init__(fmt, datefmt)
        self.max_length = max_length

    def format(self, record):
        original_message = super().format(record)
        if len(original_message) > self.max_length:
            return original_message[:self.max_length] + '...'
        return original_message

def setup_logger(max_length: int):
    global logger

    # Setup logger
    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()

    # Create formatter and add it to handlers
    formatter = MaxLengthFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', max_length=max_length)
    console_handler.setFormatter(formatter)

    # Add handler to the logger
    logger.addHandler(console_handler)

    logger.propagate = False

# Usage
max_length = 500
setup_logger(max_length)


def main():
    # Access the global logger
    global logger

    # Initialize email processor with environment variables
    email_processor = EmailProcessor()
    jobs = email_processor.fetch_jobs()

    logger.info("List of job titles fetched:")
    for job in jobs:
        logger.info(f"- {job['title']}")

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
    try:
        # Initialize the email sender
        email_sender = EmailSender(
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', '25')),
            username=os.getenv('EMAIL_USERNAME'),
            password=os.getenv('EMAIL_PASSWORD')
        )
    
        # Initialize the summary storage
        summary_storage = SummaryStorage()
    
        # Initialize the job application processor
        job_application_processor = JobApplicationProcessor(email_sender, summary_storage)
        job_application_processor.process_jobs(jobs, freelancer_profile)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        

app = Flask(__name__)

@app.route('/run', methods=['GET'])
def run_main():
    try:
        main()
        return Response("Main function executed successfully", content_type='text/plain')
    except Exception as e:
        logger.error(f"Exception in main function: {e}")
        return Response(f"Exception in main function: {e}", content_type='text/plain')

if __name__ == '__main__':
    # Check if we should start as a web service
    is_webservice = str_to_bool(os.getenv('IS_WEBSERVICE', 'false'))

    if is_webservice:
        # Logger setup for web service
        setup_logger(max_length)

        # Check listening port and host again before running the app
        listening_port, listening_host = check_listening_port()

        # In production, this block would be ignored if running with Gunicorn
        # Only for local development
        app.run(host=listening_host or '127.0.0.1', port=int(listening_port or '5000'))
    else:
        # If not a web service, just run main
        main()
