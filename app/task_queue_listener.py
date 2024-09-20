# File: task_queue_listener.py

import os
from dotenv import load_dotenv
from services.task_queue import TaskQueue
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def handle_email_task(task_data):
    logging.info(f"Processing email task: {task_data}")

def run_task_queue_listener():
    # Create a TaskQueue instance
    task_queue = TaskQueue()
    task_queue.register_callback('fetch_email', handle_email_task)

    try:
        # Start processing tasks
        logging.info("Starting task queue processing")
        task_queue.start_processing()

        # Keep the main thread running
        while True:
            pass
    except KeyboardInterrupt:
        logging.info("Stopping task queue processing")
        task_queue.stop_processing()
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        task_queue.stop_processing()

if __name__ == "__main__":
    run_task_queue_listener()
