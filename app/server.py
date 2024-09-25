import logging
from app.models.config import setup_logging
from services.task_queue import TaskQueue
from app.services.email_processor import EmailProcessor
import json
import os

# Set up logging
setup_logging()

# Get the JOB_LINK_PREFIX from environment variables
JOB_LINK_PREFIX = os.getenv('JOB_LINK_PREFIX')

# Task queue-related functions
def handle_email_fetching_task(data):
    logging.info(f"Received email fetching task data: {data}")
    try:
        email_processor = EmailProcessor()
        user_id = data.get('user_id')
        task_data = data.get('task_data')
        num_messages_to_read = task_data.get('num_messages_to_read', 10)
        task_queue = TaskQueue()
        
        emails_response = email_processor.fetch_emails(num_messages_to_read)
        if emails_response.status == "success":
            emails = emails_response.data["emails"]
            for email in emails:
                if email['from'].startswith(JOB_LINK_PREFIX):
                    # Add a task for processing this specific email
                    task_queue.add_task('process_single_email', {
                        "user_id": user_id,
                        "email_content": email_processor.serialize_email(email)
                    })
            logging.info(f"Email fetching task completed successfully for user_id: {user_id}")
        else:
            logging.error(f"Error fetching emails for user_id {user_id}: {emails_response.message}")
    except Exception as e:
        logging.error(f"Error in handle_email_fetching_task: {str(e)}")

def handle_single_email_processing(data):
    logging.info(f"Received single email processing task data: {data}")
    try:
        email_processor = EmailProcessor()
        user_id = data.get('user_id')
        email_content = data.get('email_content')
        task_queue = TaskQueue()
        
        email = email_processor.deserialize_email(email_content)
        links_response = email_processor.extract_job_links([email])
        if links_response.status == "success":
            job_links = links_response.data["job_links"]
            for link in job_links:
                # Send individual messages for each job link
                task_queue.add_task('scrape_job_details', {
                    "user_id": user_id,
                    "job_link": link
                })
            logging.info(f"Job link extraction completed successfully for user_id: {user_id}")
        else:
            logging.error(f"Error extracting job links for user_id {user_id}: {links_response.message}")
    except Exception as e:
        logging.error(f"Error in handle_single_email_processing: {str(e)}")

def handle_job_detail_scraping_task(data):
    logging.info(f"Received job detail scraping task data: {data}")
    try:
        email_processor = EmailProcessor()
        user_id = data.get('user_id')
        job_link = data.get('job_link')
        
        details_response = email_processor.scrape_job_details(job_link)
        if details_response.status == "success":
            job_detail = details_response.data["job_detail"]
            email_processor.store_job_in_database(user_id, job_detail)
            logging.info(f"Successfully scraped and stored job details for link: {job_link}")
        else:
            logging.error(f"Failed to scrape job details for link {job_link}: {details_response.message}")
    except Exception as e:
        logging.error(f"Error in handle_job_detail_scraping_task: {str(e)}")

def run_task_queue_listener():
    logging.info("Initializing task queue listener...")

    # Create a TaskQueue instance
    task_queue = TaskQueue()
    
    # Register callbacks for different task types
    task_queue.register_callback('fetch_email', handle_email_fetching_task)
    task_queue.register_callback('process_single_email', handle_single_email_processing)
    task_queue.register_callback('scrape_job_details', handle_job_detail_scraping_task)

    try:
        logging.info("Starting task queue processing.")
        task_queue.start_processing()

        # Keep the main thread running using eventlet sleep
        while True:
            pass              
    except KeyboardInterrupt:
        logging.info("Task queue processing interrupted by KeyboardInterrupt.")
        task_queue.stop_processing()
    except Exception as e:
        logging.error(f"An error occurred in task queue listener: {str(e)}")
        task_queue.stop_processing()

# Main function to run task queue listener
if __name__ == '__main__':
    logging.info("Starting application...")

    try:
        logging.info("Starting task queue listener.")
        run_task_queue_listener()
    except Exception as e:
        logging.error(f"Error in main loop: {str(e)}")
