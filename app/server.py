import logging
from app.managers.messages_handler import MessageHandler
from app.models.config import setup_logging
from services.task_queue import TaskQueue
from app.services.email_processor import EmailProcessor
import json
import os

# Set up logging
setup_logging()

def run_task_queue_listener():
    logging.info("Initializing task queue listener...")

    # Create a TaskQueue instance
    task_queue = TaskQueue()
    
    # Register callbacks for different task types
    task_queue.register_callback('process_job', MessageHandler.handle_process_job_task)

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
