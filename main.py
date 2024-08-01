import os
import configparser
import logging
from datetime import datetime
from flask import Flask, jsonify

from email_processor import EmailProcessor
from job_application_processor import JobApplicationProcessor

# Initialize configuration parser
config = configparser.ConfigParser()

def setup_configs():
    global config
    config_path = os.path.join(os.path.dirname(__file__), 'config.cfg')
    config.read(config_path)
    logger.debug(f"Config path: {config_path}")

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
    os.makedirs(log_directory, exist_ok=True)
    log_filename = os.path.join(log_directory, f"{datetime.now().strftime('%Y-%m-%d')}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename, mode="w")
    console_handler = FlushableStreamHandler()

    formatter = MaxLengthFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', max_length=max_length)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return log_filename

def str_to_bool(s: str) -> bool:
    if s.lower() in ('true', 'yes', '1'):
        return True
    elif s.lower() in ('false', 'no', '0'):
        return False
    else:
        raise ValueError(f"Cannot convert {s} to boolean")

def main():
    setup_configs()

    # Initialize email processor with config values
    email_processor = EmailProcessor()
    jobs = email_processor.fetch_jobs()

    logger.info("List of job titles fetched:")
    for job in jobs:
        logger.info(f"- {job['title']}")

    wait_for_key = str_to_bool(config.get("GENERAL", "WAIT_AFTER_FETCHING_JOBS"))
    if wait_for_key:
        input("Press any key to continue...")

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

@app.route('/run', methods=['GET'])
def run_main():
    try:
        main()
        return jsonify({"status": "success", "message": "Main function executed successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    setup_logger("log", 500)
    setup_configs()
    listening_host = config.get("GENERAL", "LISTENING_HOST")
    listening_port = config.get("GENERAL", "LISTENING_PORT")
    app.run(host=listening_host, port=listening_port)
