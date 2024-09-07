import poplib
poplib._MAXLINE = 8192
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
import threading
import time
from email.utils import parsedate_to_datetime
import ssl
from urllib.parse import urlparse, urlunparse
from app.utils.api_response import APIResponse
import logging
from app.models.processed_email_manager import ProcessedEmailManager
from app.db.utils import get_db
from app.models.job_manager import JobManager

class EmailProcessor:
    def __init__(self, processed_emails):
        self.logger = logging.getLogger(__name__)
        self.processed_emails = processed_emails        
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
        self.mailbox = None

    def connect_to_mailbox(self):
        self.logger.debug("Connecting to mailbox: %s:%d", self.pop3_server, self.pop3_port)
        try:
            self.mailbox = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
            self.mailbox.user(self.username)
            self.mailbox.pass_(self.password)
            self.logger.info("Successfully connected to mailbox")
        except poplib.error_proto as e:
            self.logger.error("Failed to connect to mailbox: %s", e)
            raise

    def extract_links_from_body(self, body):
        self.logger.debug("Extracting links from email body")
        pattern = r' href="([^"]+)"'
        links = re.findall(pattern, body)
        decoded_links = [html.unescape(unquote(link)) for link in links]
        return decoded_links

    def extract_job_description(self, soup):
        self.logger.debug("Extracting job description from HTML")
        div_element = soup.find('div', {'data-line-break': 'true'})
        if div_element:
            return div_element.text.strip()
        return None

    def extract_job_title(self, soup):
        self.logger.debug("Extracting job title from HTML")
        title = soup.title
        if title:
            return title.text.strip()
        return None

    def extract_budget(self, soup):
        self.logger.debug("Extracting budget from HTML")
        budget = soup.find('h2', {'data-size-desktop': 'xlarge'})
        if budget:
            return budget.text.strip()
        return None


    def process_message(self, message, user_id):
        self.logger.debug("Processing message from: %s", message['from'])
        seen_jobs = set()  # A set to track seen job links
        jobs = []  # Initialize an empty list to store jobs

        job_manager = JobManager(get_db(), user_id)  # Initialize JobManager with user_id

        if self.target_sender in message['from']:
            payload = message.get_payload()
            if isinstance(payload, list):
                for part in payload:
                    body = part.get_payload(decode=True).decode('utf-8')
                    self.logger.debug("Extracted message body: %s", body)
                    links = self.extract_links_from_body(body)
                    if links:
                        for link in links:
                            # Parse the link and remove query parameters
                            parsed_url = urlparse(link)
                            link_without_query = urlunparse(parsed_url._replace(query=""))

                            if link_without_query.startswith(self.job_link_prefix):
                                if link_without_query not in seen_jobs:
                                    self.logger.info("Found job link: %s", link_without_query)
                                    response = requests.get(link)
                                    self.logger.debug("Fetched response from job link: %s", response.text[:100])
                                    soup = BeautifulSoup(response.text, 'html.parser')

                                    job_description = self.extract_job_description(soup)
                                    job_title = self.extract_job_title(soup)
                                    job_budget = self.extract_budget(soup)

                                    if job_description is not None and job_title is not None:
                                        self.logger.info("Job found: %s", job_title)

                                        # Check if the job already exists
                                        if not job_manager.job_exists(job_title):
                                            # Extract the email date
                                            email_date = parsedate_to_datetime(message['Date'])

                                            # Create a new job entry in job_details
                                            job_id = job_manager.create_job(
                                                job_title=job_title,
                                                job_description=job_description,
                                                budget=job_budget,
                                                status="open",
                                                email_date=email_date
                                            )

                                            # Yield the newly added job
                                            yield {
                                                'job_id': job_id,
                                                'title': job_title,
                                                'description': job_description,
                                                'budget': job_budget,
                                                'link': link_without_query,
                                                'email_date': email_date
                                            }

                                else:
                                    self.logger.debug("Link has already been processed: %s", link_without_query)
                            else:
                                self.logger.debug("Link does not start with job link prefix: %s", link_without_query)

                            # Add the link to seen jobs
                            seen_jobs.add(link_without_query)
                    else:
                        self.logger.debug("No links found in message body.")
            else:
                self.logger.debug("Message not from target sender: %s", message['from'])


    def fetch_email(self, index, user_id, max_retries=3):
        self.logger.debug("Fetching email %d", index)
        retries = 0

        while retries < max_retries:
            try:
                retr_result = self.mailbox.retr(index)
                response, lines, octets = retr_result
                msg_content = b'\r\n'.join(lines).decode('utf-8')
                message = parser.Parser().parsestr(msg_content)
                message_id = message['message-id']

                # Check if the email has already been processed
                pem = ProcessedEmailManager(get_db(), user_id)
                if pem.is_email_processed(message_id, user_id):
                    self.logger.debug(f"Skipping already processed email: {message_id}")
                    return None, None

                jobs = []  # Initialize an empty list to store jobs
                # Process the message and yield jobs
                for job in self.process_message(message, user_id):
                    self.logger.info(f"New job added: {job['title']} with ID {job['job_id']}")
                    jobs.append(job)

                # If jobs were found, mark the email as processed and return the jobs
                if jobs:
                    self.mark_email_as_processed(message_id, user_id)
                    return jobs, message_id
                else:
                    self.logger.debug(f"No jobs found in email {index}. Moving to the next email.")
                    return None, None

            except ssl.SSLError as e:
                retries += 1
                self.logger.error(f"SSL error occurred while fetching email {index}: {e}")
                if retries < max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    self.logger.info(f"Retrying to fetch email {index} in {wait_time} seconds ({retries}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Failed to fetch email {index} after {max_retries} attempts due to SSL error.")
                    return None, None

            except Exception as e:
                self.logger.error(f"An unexpected error occurred while fetching email {index}: {e}")
                return None, None

        self.logger.error(f"Failed to fetch email {index} after {max_retries} attempts.")
        return None, None



    def fetch_and_process_email(self, index, user_id, job_application_processor):
        self.logger.debug(f"Fetching and processing email {index}")
        result = self.fetch_email(index, user_id)
        if result:
            jobs, message_id = result
            self.process_email_jobs(jobs, message_id, job_application_processor, user_id)
        else:
            self.logger.warning(f"Skipping email {index} due to errors or no jobs found.")

    def process_email_jobs(self, jobs, message_id, job_application_processor, user_id):
        for job in jobs:
            try:
                job_application_processor.process_job(job)
            except Exception as e:
                self.logger.error(f"Failed to process job: {job['title']} from email {message_id}: {e}")
        pem = ProcessedEmailManager(get_db(), user_id)
        pem.mark_email_as_processed(message_id, user_id)
    
    def fetch_jobs_from_email(self, user_id) -> APIResponse:
        jobs_list = []
        try:
            self.connect_to_mailbox()
            num_messages = len(self.mailbox.list()[1])  # Fetch the number of messages
            self.logger.info(f"Number of messages in the mailbox: {num_messages}")

            # Iterate through the most recent emails, starting from the last one
            for i in range(max(1, num_messages - self.num_messages_to_read + 1), num_messages + 1):
                self.logger.info(f"Fetching email {i} out of {num_messages}")
                try:
                    jobs, message_id = self.fetch_email(i, user_id)
                    if jobs:
                        jobs_list.extend(jobs)
                except Exception as e:
                    self.logger.error(f"Error processing email {i}: {e}")
                    return APIResponse(
                        status="failure",
                        message=f"Error fetching email {i}: {str(e)}",
                        data={"job_list": jobs_list}
                    )

            # Return a successful APIResponse with the collected jobs
            return APIResponse(
                status="success",
                message="Jobs fetched successfully",
                data={"job_list": jobs_list}
            )

        except Exception as e:
            self.logger.error(f"Failed to fetch jobs from email: {e}")
            return APIResponse(
                status="failure",
                message="Failed to fetch jobs from email",
                data={"job_list": jobs_list}
            )

        finally:
            if self.mailbox:
                try:
                    self.mailbox.quit()
                    self.logger.info("Disconnected from mailbox")
                except Exception as e:
                    self.logger.error(f"Error while disconnecting from mailbox: {e}")
