import logging
from app.models.config import setup_logging
from services.task_queue import TaskQueue
from app.services.email_processor import EmailProcessor


# Set up logging
setup_logging()

# Task queue-related functions
def handle_email_task(task_data):
    logging.info(f"Received email task data: {task_data}")

    try:
        email_processor = EmailProcessor()
        user_id = task_data.get('user_id') 
        logging.info(f"Fetching jobs from email for user_id: {user_id}")
        email_processor.fetch_jobs_from_email(user_id)
        logging.info("Email task completed successfully.")
    except Exception as e:
        logging.error(f"Error in handle_email_task: {str(e)}")

def run_task_queue_listener():
    logging.info("Initializing task queue listener...")

    # Create a TaskQueue instance
    task_queue = TaskQueue()
    task_queue.register_callback('fetch_email_jobs', handle_email_task)

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
