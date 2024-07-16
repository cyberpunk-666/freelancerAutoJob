import poplib
poplib._MAXLINE = 200480
from email import parser
import re
from urllib.parse import unquote
import html
import configparser
import logging
import requests

class EmailProcessor:
    def __init__(self, config_path='config.cfg'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        self.username = self.config.get('EMAIL', 'USERNAME')
        self.password = self.config.get('EMAIL', 'PASSWORD')
        self.pop3_server = self.config.get('EMAIL', 'POP3_SERVER')
        self.pop3_port = self.config.getint('EMAIL', 'POP3_PORT')
        self.num_messages_to_read = self.config.getint('GENERAL', 'NUM_MESSAGES_TO_READ')
        self.target_sender = self.config.get('GENERAL', 'TARGET_SENDER')
        self.job_link_prefix = self.config.get('GENERAL', 'JOB_LINK_PREFIX')
        self.job_description_classes = self.config.get('HTML_CLASSES', 'JOB_DESCRIPTION_CLASSES').split(',')

    def connect_to_mailbox(self):
        self.mailbox = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
        self.mailbox.user(self.username)
        self.mailbox.pass_(self.password)

    def extract_links_from_body(self, body):
        pattern = r'originalsrc="([^"]+)"'
        links = re.findall(pattern, body)
        decoded_links = [html.unescape(unquote(link)) for link in links]
        return decoded_links

    def extract_job_description(self, soup):
        div_element = soup.find('div', {'data-line-break': 'true'})
        if div_element:
            return div_element.text.strip()
        return None

    def extract_job_title(self, soup):
        title = soup.title
        if title:
            return title.text.strip()
        return None

    def extract_budget(self, soup):
        budget = soup.find(attrs={'data-size': 'mid'})
        if budget:
            return budget.text.strip()
        return None



    def process_message(self, message):
        logging.info("Starting to process message")

        if self.target_sender in message['from']:
            logging.debug(f"Message from target sender: {message['from']}")
            payload = message.get_payload()
            
            if isinstance(payload, list):
                logging.debug("Message payload is a list")
                for part in payload:
                    body = part.get_payload(decode=True).decode('utf-8')
                    logging.debug(f"Decoded message part: {body[:50]}...")  # Log first 50 characters

                    links = self.extract_links_from_body(body)
                    logging.debug(f"Extracted links: {links}")

                    if links:
                        for link in links:
                            logging.debug(f"Processing link: {link}")
                            if link.startswith(self.job_link_prefix):
                                response = requests.get(link)
                                logging.info(f"Requested link: {link}")

                                soup = BeautifulSoup(response.text, 'html.parser')
                                job_description = self.extract_job_description(soup)
                                job_title = self.extract_job_title(soup)
                                job_budget = self.extract_budget(soup)

                                if job_description is not None:
                                    logging.info(f"Job found: {job_title}, Budget: {job_budget}")
                                    return {
                                        'title': job_title,
                                        'description': job_description,
                                        'budget': job_budget,
                                        'link': link
                                    }
        logging.warning("No valid job found in message")
        return None

    def fetch_jobs(self, job_queue):
        logging.info("Fetching jobs from job queue")

        if not job_queue:
            logging.warning("Job queue is empty")
            return []

        jobs = []
        try:
            for job in job_queue:
                logging.debug(f"Fetching job: {job}")
                jobs.append(job)
            logging.info(f"Successfully fetched {len(jobs)} jobs")
        except Exception as e:
            logging.error(f"Error fetching jobs: {e}", exc_info=True)
            return []

        return jobs

