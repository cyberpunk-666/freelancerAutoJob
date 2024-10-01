import logging
import os

from app.db.db_utils import get_db
from app.db.postgresdb import PostgresDB
from app.managers.user_preferences_manager import UserPreferencesManager
from app.services.email_processor import EmailProcessor
from app.services.job_application_processor import JobApplicationProcessor
from app.services.task_queue import TaskQueue

# Get the JOB_LINK_PREFIX from environment variables
JOB_LINK_PREFIX = os.getenv('JOB_LINK_PREFIX')

class MessageHandler:
    def __init__(self):
        self.db:PostgresDB = get_db()
        self.logger = logging.getLogger(__name__)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def handle_process_job_task(data):
        logging.info(f"Received job processing task data: {data}")
        try:
            user_id = data.get('user_id')
            task_data = data.get('task_data')
            job_id = task_data.get('job_id')

            job_application_processor = JobApplicationProcessor()
            user_prefrences_manager = UserPreferencesManager()
            user_preferences_answer = user_prefrences_manager.get_preference_value(user_id, 'gemini_api_key')
            gemini_api_key = UserPreferencesManager.get_api_response_value(user_preferences_answer, 'value')
            job_application_processor.gemini_api_key = gemini_api_key
            job_application_processor.process_job(user_id, job_id)
            logging.info(f"Successfully processed job data for user_id: {user_id}")
        except Exception as e:
            logging.error(f"Error in handle_process_job_task: {str(e)}")
