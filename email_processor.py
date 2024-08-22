
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
from utils import str_to_bool

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        listening_port= os.getenv('LISTENING_PORT')
        logging.debug(f"listening_port 2:{listening_port}")
                
        self.mailbox = None

    # Add other methods here, as needed...
        
    def connect_to_mailbox(self):
        logging.debug("Connecting to mailbox: %s:%d", self.pop3_server, self.pop3_port)
        try:
            self.mailbox = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
            logging.debug(f"username:{self.username}")
            logging.debug(f"password:{self.password}")
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
                                    return {
                                        'title': job_title,
                                        'description': job_description,
                                        'budget': job_budget,
                                        'link': link
                                    }
                            else:
                                logging.debug("Link does not start with job link prefix: %s", link)
                    else:
                        logging.debug("No links found in message body.")
        else:
            logging.debug("Message not from target sender: %s", message['from'])
            
        return None


    def fetch_jobs(self):
        logging.debug("Fetching jobs")
        self.connect_to_mailbox()
        num_messages = len(self.mailbox.list()[1])
        num_messages_to_read = min(self.num_messages_to_read, num_messages)
        jobs = []
        use_cache = str_to_bool(os.getenv('USE_CACHE'))

        processed_email_ids = self.load_processed_emails()

        for i in range(num_messages - num_messages_to_read + 1, num_messages + 1):
            logging.debug("Reading message %d of %d", i, num_messages)
            try:
                retr_result = self.mailbox.retr(i)
                response, lines, octets = retr_result
                msg_content = b'\r\n'.join(lines).decode('utf-8')
                message = parser.Parser().parsestr(msg_content)
                message_id = message['message-id']

                if use_cache and (message_id in processed_email_ids):
                    logging.debug(f"use_cache: {use_cache}")
                    logging.debug("Skipping already processed email: %s", message_id)
                    continue

                job = self.process_message(message)
                if job:
                    jobs.append(job)
                    processed_email_ids.append(message_id)
            except poplib.error_proto as e:
                logging.error(f"Failed to retrieve message {i}: {e}")
                continue

        try:
            self.mailbox.quit()
        except poplib.error_proto as e:
            logging.error(f"Failed to quit mailbox: {e}")

        logging.info("Fetched %d jobs", len(jobs))

        self.save_processed_emails(processed_email_ids)

        return jobs

    def load_processed_emails(self, filename='processed_emails.json'):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                return json.load(file)
        return []
    
    def save_processed_emails(self, email_ids, filename='processed_emails.json'):
        with open(filename, 'w') as file:
            json.dump(email_ids, file)
