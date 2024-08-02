import os
import logging
from datetime import datetime
from flask import Flask, jsonify, Response, stream_with_context
from dotenv import load_dotenv
from queue import Queue, Empty
import threading
from logging.handlers import QueueHandler, QueueListener

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading environment variables from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Additional debug to check if value is set later
def check_listening_port():
    port = os.getenv('LISTENING_PORT')
    host = os.getenv('LISTENING_HOST)
    logger.debug(f"check_listening_port: {port}")
    logger.debug(f"check_listening_host: {host}")    
    return port

from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor

class FlushableStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

class MaxLengthFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', max_length=100):
        super().__init__(fmt, datefmt, style)
        self.max_length = max_length

    def format(self, record):
        original_message = super().format(record)
        if len(original_message) > self.max_length:
            return original_message[:self.max_length] + '...'
        return original_message

def setup_logger(log_directory: str, max_length: int):
    global logger
    # Create a queue to hold log messages
    log_queue = Queue()

    # Setup logger
    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Ensure the log directory exists
    os.makedirs(log_directory, exist_ok=True)

    # Create handlers
    queue_handler = QueueHandler(log_queue)
    file_handler = logging.FileHandler(os.path.join(log_directory, f"{datetime.now().strftime('%Y-%m-%d')}.log"), mode="w")
    console_handler = FlushableStreamHandler()

    # Create formatter and add it to handlers
    formatter = MaxLengthFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', max_length=max_length)
    queue_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(queue_handler)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Create a listener to handle logs from the queue
    listener = QueueListener(log_queue, file_handler, console_handler)
    listener.start()

    logger.propagate = False

    return log_queue

# Usage
log_directory = "log"
max_length = 500
log_queue = setup_logger(log_directory, max_length)

def str_to_bool(s: str) -> bool:
    if s.lower() in ('true', 'yes', '1'):
        return True
    elif s.lower() in ('false', 'no', '0'):
        return False
    else:
        raise ValueError(f"Cannot convert {s} to boolean")

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

    job_application_processor = JobApplicationProcessor()
    job_application_processor.process_jobs(jobs, freelancer_profile)

app = Flask(__name__)

def run_main_thread():
    try:
        main()
    except Exception as e:
        logger.error(f"Exception in main function: {e}")

@app.route('/run', methods=['GET'])
def run_main():
    def log_generator():
        main_thread = threading.Thread(target=run_main_thread)
        main_thread.start()
        
        while main_thread.is_alive():
            try:
                message = log_queue.get(timeout=1)
                yield f'data: {message}\n\n'
            except Empty:
                continue

        # Ensure all remaining messages are processed
        while not log_queue.empty():
            try:
                message = log_queue.get_nowait()
                yield f'data: {message}\n\n'
            except Empty:
                break

    return Response(stream_with_context(log_generator()), content_type='text/event-stream')

if __name__ == '__main__':
    setup_logger("log", 500)
    # Check listening port again before running the app
    listening_port = check_listening_port()
    app.run(host=os.getenv('LISTENING_HOST', '127.0.0.1'), port=int(listening_port or '5000'))
