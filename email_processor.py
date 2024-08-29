import poplib
import logging
from email import parser
import re
from urllib.parse import unquote
import html
from bs4 import BeautifulSoup
import requests
import os
import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from utils import str_to_bool
import threading
import time
from email.utils import parsedate_to_datetime

class EmailProcessor:
    def __init__(self):
        self.username = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.pop3_server = os.getenv('POP3_SERVER')
        self.pop3_port = int(os.getenv('POP3_PORT'))
        self.num_messages_to_read = int(os.getenv('NUM_MESSAGES_TO_READ'))
        self.target_sender = os.getenv('TARGET_SENDER')
        self.job_link_prefix = os.getenv('JOB_LINK_PREFIX')
        self.job_description_classes = os.getenv('JOB_DESCRIPTION_CLASSES').split(',')
        self.min_hourly_rate = float(os.getenv('MIN_HOURLY_RATE'))
        self.lock = threading.Lock()
        self.processed_emails = self.load_processed_emails()
        self.mailbox = None

    def connect_to_mailbox(self):
        logging.debug("Connecting to mailbox: %s:%d", self.pop3_server, self.pop3_port)
        try:
            self.mailbox = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
            self.mailbox.user(self.username)
            self.mailbox.pass_(self.password)
            logging.info("Successfully connected to mailbox")
        except poplib.error_proto as e:
            logging.error("Failed to connect to mailbox: %s", e)
            raise

    def extract_links_from_body(self, body):
        logging.debug("Extracting links from email body")
        pattern = r' href="([^"]+)"'
        links = re.findall(pattern, body)
        decoded_links = [html.unescape(unquote(link)) for link in links]
        return decoded_links

    def extract_job_description(self, soup):
        logging.debug("Extracting job description from HTML")
        div_element = soup.find('div', {'data-line-break': 'true'})
        if div_element:
            return div_element.text.strip()
        return None

    def extract_job_title(self, soup):
        logging.debug("Extracting job title from HTML")
        title = soup.title
        if title:
            return title.text.strip()
        return None

    def extract_budget(self, soup):
        logging.debug("Extracting budget from HTML")
        budget = soup.find('h2', {'data-size-desktop': 'xlarge'})
        if budget:
            return budget.text.strip()
        return None

    def process_message(self, message):
        logging.debug("Processing message from: %s", message['from'])
        if self.target_sender in message['from']:
            payload = message.get_payload()
            if isinstance(payload, list):
                for part in payload:
                    body = part.get_payload(decode=True).decode('utf-8')
                    logging.debug("Extracted message body: %s", body)
                    links = self.extract_links_from_body(body)
                    if links:
                        for link in links:
                            if link.startswith(self.job_link_prefix):
                                logging.info("Found job link: %s", link)
                                response = requests.get(link)
                                logging.debug("Fetched response from job link: %s", response.text[:100])
                                soup = BeautifulSoup(response.text, 'html.parser')
                                job_description = self.extract_job_description(soup)
                                job_title = self.extract_job_title(soup)
                                job_budget = self.extract_budget(soup)
                                if job_description is not None:
                                    logging.info("Job found: %s", job_title)

                                    # Extract the email date
                                    email_date = parsedate_to_datetime(message['Date'])

                                    return {
                                        'title': job_title,
                                        'description': job_description,
                                        'budget': job_budget,
                                        'link': link,
                                        'email_date': email_date
                                    }
                            else:
                                logging.debug("Link does not start with job link prefix: %s", link)
                    else:
                        logging.debug("No links found in message body.")
        else:
            logging.debug("Message not from target sender: %s", message['from'])
            
        return None


    def fetch_email(self, index, max_retries=3):
        logging.debug("Fetching email %d", index)
        retries = 0
        while retries < max_retries:
            try:
                retr_result = self.mailbox.retr(index)
                response, lines, octets = retr_result
                msg_content = b'\r\n'.join(lines).decode('utf-8')
                message = parser.Parser().parsestr(msg_content)
                message_id = message['message-id']

                if message_id in self.processed_emails:
                    logging.debug("Skipping already processed email: %s", message_id)
                    return None

                job = self.process_message(message)
                if job:
                    self.processed_emails.append(message_id)  # Track processed email ID
                    return job, message_id
                else:
                    logging.debug("No job found in email %d. Moving to the next email.", index)
                    return None  # No retry needed, just move to the next email

            except poplib.error_proto as e:
                logging.error(f"Failed to retrieve message {index}: {e}")
                retries += 1
                wait_time = 2 ** retries  # Exponential backoff
                logging.warning(f"Retrying to fetch email {index} in {wait_time} seconds (Attempt {retries}/{max_retries}).")
                time.sleep(wait_time)
            except Exception as e:
                logging.error(f"An unexpected error occurred while fetching email {index}: {e}")
                break  # Exit loop on unexpected errors

        logging.error(f"Exceeded maximum retries for email {index}.")
        return None
    

    def fetch_jobs(self):
        logging.debug("Fetching jobs")
        self.connect_to_mailbox()
        num_messages = len(self.mailbox.list()[1])
        num_messages_to_read = min(self.num_messages_to_read, num_messages)
        jobs = []

        for i in range(num_messages - num_messages_to_read + 1, num_messages + 1):
            result = self.fetch_email(i)
            if result:
                job, message_id = result
                jobs.append(job)
                yield jobs, message_id  # Yield jobs and the corresponding message ID

        try:
            self.mailbox.quit()
        except poplib.error_proto as e:
            logging.error(f"Failed to quit mailbox: {e}")

        logging.info("Finished fetching jobs")

    def load_processed_emails(self, filename='processed_emails.json'):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                return json.load(file)
        return []
    
    def save_processed_emails(self, email_ids, filename='processed_emails.json'):
        with open(filename, 'w') as file:
            json.dump(email_ids, file)

    def mark_email_as_processed(self, message_id):
        self.save_processed_emails(self.processed_emails)
        logging.info(f"Marked email as processed: {message_id}")
