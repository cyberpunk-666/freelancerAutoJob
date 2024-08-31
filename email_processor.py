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
import ssl
from urllib.parse import urlparse, urlunparse

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
        jobs = []  # Initialize an empty list to store jobs
        seen_jobs = set()  # A set to track seen job links

        if self.target_sender in message['from']:
            payload = message.get_payload()
            if isinstance(payload, list):
                for part in payload:
                    body = part.get_payload(decode=True).decode('utf-8')
                    logging.debug("Extracted message body: %s", body)
                    links = self.extract_links_from_body(body)
                    if links:
                        for link in links:
                            # Parse the link and remove query parameters
                            parsed_url = urlparse(link)
                            link_without_query = urlunparse(parsed_url._replace(query=""))

                            if link_without_query.startswith(self.job_link_prefix):
                                if link_without_query not in seen_jobs:
                                    logging.info("Found job link: %s", link_without_query)
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

                                        # Append the job to the list
                                        jobs.append({
                                            'title': job_title,
                                            'description': job_description,
                                            'budget': job_budget,
                                            'link': link_without_query,  # Store the link without query parameters
                                            'email_date': email_date
                                        })
                                else:
                                    logging.debug("Link has already been processed: %s", link_without_query)
                            else:
                                logging.debug("Link does not start with job link prefix: %s", link_without_query)

                            # Add the link to seen jobs
                            seen_jobs.add(link_without_query)
                    else:
                        logging.debug("No links found in message body.")
            else:
                logging.debug("Message not from target sender: %s", message['from'])

        return jobs  # Return the list of jobs


    def fetch_email(self, index, max_retries=6):
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

                jobs = self.process_message(message)  # Now returns a list of jobs
                if jobs:
                    self.processed_emails.append(message_id)  # Track processed email ID
                    return jobs, message_id  # Return list of jobs and the message ID
                else:
                    logging.debug("No jobs found in email %d. Moving to the next email.", index)
                    return None  # No retry needed, just move to the next email

            except ssl.SSLError as e:
                retries += 1
                logging.error(f"SSL error occurred while fetching email {index}: {e}")
                if retries < max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    logging.info(f"Retrying to fetch email {index} in {wait_time} seconds ({retries}/{max_retries})...")
                    time.sleep(wait_time)
                    continue  # Retry fetching the email
                else:
                    logging.error(f"Failed to fetch email {index} after {max_retries} attempts due to SSL error.")
                    return None

            except Exception as e:
                logging.error(f"An unexpected error occurred while fetching email {index}: {e}")
                return None

        logging.error(f"Failed to fetch email {index} after {max_retries} attempts.")
        return None


    def fetch_and_process_email(self, index, job_application_processor):
        logging.debug(f"Fetching and processing email {index}")
        result = self.fetch_email(index)
        if result:
            jobs, message_id = result
            self.process_email_jobs(jobs, message_id, job_application_processor)
        else:
            logging.warning(f"Skipping email {index} due to errors or no jobs found.")

    def process_email_jobs(self, jobs, message_id, job_application_processor):
        for job in jobs:
            try:
                job_application_processor.process_job(job)
            except Exception as e:
                logging.error(f"Failed to process job: {job['title']} from email {message_id}: {e}")
        self.mark_email_as_processed(message_id)

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
