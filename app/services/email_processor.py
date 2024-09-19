import poplib

from app.services.job_application_processor import JobApplicationProcessor
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
from app.models.api_response import APIResponse
import logging
from app.managers.processed_email_manager import ProcessedEmailManager
from app.db.db_utils import get_db
from app.managers.job_manager import JobManager
import ssl
import time
import imaplib
import smtplib

class APIResponse:
    def __init__(self, status: str, message: str, data: dict = None):
        self.status = status
        self.message = message
        self.data = data or {}


class EmailProcessor:
    def __init__(self):
        self.logger = logging.getLogger()
        db = get_db()
        self.job_manager = JobManager(db)

        # Email configuration
        self.email_address = os.environ.get('EMAIL_USERNAME')
        self.email_password = os.environ.get('EMAIL_PASSWORD')
        self.pop3_server = os.environ.get('POP3_SERVER')
        self.pop3_port = int(os.environ.get('POP3_PORT'))
        self.connection_type = os.environ.get('CONNECTION_TYPE').lower()
        # Job fetching and processing configuration
        self.num_messages_to_read = int(os.environ.get('NUM_MESSAGES_TO_READ', 10))
        self.target_sender = os.environ.get('TARGET_SENDER')
        self.job_link_prefix = os.environ.get('JOB_LINK_PREFIX')

        # Instantiate the mailbox object
        self.mailbox = None



    def is_connected(self):
        if isinstance(self.mailbox, imaplib.IMAP4):
            try:
                status = self.mailbox.noop()[0]
                return status == 'OK'
            except:
                return False
        elif isinstance(self.mailbox, poplib.POP3):
            try:
                status = self.mailbox.noop()
                return True
            except:
                return False
        elif isinstance(self.mailbox, smtplib.SMTP):
            try:
                status = self.mailbox.noop()[0]
                return status == 250
            except:
                return False
        else:
            return False

    def establish_mailbox_connection(self):
        # Check if already connected
        if self.is_connected():
            print(f"Already connected to {self.connection_type} server")
            return

        # If not connected, establish a new connection
        try:
            if self.connection_type == 'imap':
                self.mailbox = imaplib.IMAP4_SSL(self.pop3_server, self.pop3_port)
                self.mailbox.login(self.email_address, self.email_password)
            elif self.connection_type == 'pop3':
                self.mailbox = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
                self.mailbox.user(self.email_address)
                self.mailbox.pass_(self.email_password)
            elif self.connection_type == 'smtp':
                self.mailbox = smtplib.SMTP(self.pop3_server, self.pop3_port)
                self.mailbox.starttls()
                self.mailbox.login(self.email_address, self.email_password)
            else:
                raise ValueError("Unsupported connection type")

            if self.is_connected():
                print(f"Successfully connected to {self.connection_type} server")
            else:
                print(f"Failed to connect to {self.connection_type} server")
                self.mailbox = None
        except Exception as e:
            print(f"Error connecting to {self.connection_type} server: {str(e)}")
            self.mailbox = None
            
    def extract_links_from_body(self, body: str) -> APIResponse:
        self.logger.debug("Extracting links from email body")
        try:
            pattern = r' href="([^"]+)"'
            links = re.findall(pattern, body)
            decoded_links = [html.unescape(unquote(link)) for link in links]
            return APIResponse(status="success", message="Links extracted successfully", data={"links": decoded_links})
        except Exception as e:
            self.logger.error(f"Error extracting links from email body: {e}")
            return APIResponse(status="failure", message="Error extracting links from email body")

    def extract_job_description(self, soup: BeautifulSoup) -> APIResponse:
        self.logger.debug("Extracting job description from HTML")
        div_element = soup.find('div', {'data-line-break': 'true'})
        try:
            if div_element:
                job_description = div_element.text.strip()
                return APIResponse(status="success", message="Job description extracted successfully", data={"job_description": job_description})
            else:
                return APIResponse(status="success", message="No job description found")
        except Exception as e:
            self.logger.error(f"Error extracting job description from HTML: {e}")
            return APIResponse(status="failure", message="Error extracting job description from HTML")

    def extract_job_title(self, soup: BeautifulSoup) -> APIResponse:
        self.logger.debug("Extracting job title from HTML")
        try:
            title = soup.title
            if title:
                job_title = title.text.strip()
                return APIResponse(status="success", message="Job title extracted successfully", data={"job_title": job_title})
            else:
                return APIResponse(status="success", message="No job title found")
        except Exception as e:
            self.logger.error(f"Error extracting job title from HTML: {e}")
            return APIResponse(status="failure", message="Error extracting job title from HTML")

    def extract_budget(self, soup: BeautifulSoup) -> APIResponse:
        self.logger.debug("Extracting budget from HTML")
        try:
            budget = soup.find('h2', {'data-size-desktop': 'xlarge'})
            if budget:
                job_budget = budget.text.strip()
                return APIResponse(status="success", message="Job budget extracted successfully", data={"job_budget": job_budget})
            else:
                return APIResponse(status="success", message="No job budget found")
        except Exception as e:
            self.logger.error(f"Error extracting job budget from HTML: {e}")
            return APIResponse(status="failure", message="Error extracting job budget from HTML")   

    def extract_jobs_from_email(self, message, user_id) -> APIResponse:       
        """
        Extract job links and details from an email message, process the job if found, and ensure it's stored in the database.

        Args:
            message (email.message.Message): The email message object to process.
            user_id (str): The ID of the user who owns the email.

        Returns:
            APIResponse: A response with the status of job extraction and processing, including job details if successful.
        """
        seen_jobs = set()
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
                                    try:
                                        response = requests.get(link)
                                        self.logger.debug("Fetched response from job link: %s", response.text[:100])
                                        soup = BeautifulSoup(response.text, 'html.parser')

                                        job_description = self.extract_job_description(soup)
                                        job_title = self.extract_job_title(soup)
                                        job_budget = self.extract_budget(soup)

                                        if job_description is not None and job_title is not None:
                                            self.logger.info("Job found: %s", job_title)

                                            # Check if the job already exists
                                            if not self.job_manager.job_exists(job_title):
                                                # Extract the email date
                                                email_date = parsedate_to_datetime(message['Date'])

                                                # Create a new job entry in job_details
                                                job_id = self.job_manager.create_job(
                                                    job_title=job_title,
                                                    job_description=job_description,
                                                    budget=job_budget,
                                                    status="open",
                                                    email_date=email_date
                                                )

                                                # Return a successful APIResponse with the new job
                                                return APIResponse(
                                                    status="success",
                                                    message="New job found",
                                                    data={
                                                        'job_id': job_id,
                                                        'title': job_title,
                                                        'description': job_description,
                                                        'budget': job_budget,
                                                        'link': link_without_query,
                                                        'email_date': email_date
                                                    }
                                                )
                                            else:
                                                self.logger.debug("Job already exists: %s", job_title)
                                    except Exception as e:
                                        self.logger.error(f"Error processing job link {link_without_query}: {e}")
                                        return APIResponse(
                                            status="failure",
                                            message=f"Error processing job link {link_without_query}: {str(e)}"
                                        )


                            # Add the link to seen jobs
                            seen_jobs.add(link_without_query)
                    else:
                        self.logger.debug("No links found in message body.")
            else:
                self.logger.debug("Message not from target sender: %s", message['from'])
        else:
            self.logger.debug("Message not from target sender: %s", message['from'])

        return APIResponse(status="success", message="No new jobs found")

    def retrieve_email_jobs(self, index, user_id, max_retries=3) -> APIResponse:
        """
        Retrieve the jobs in an email by index from the mailbox, ensuring it's not already processed.

        Args:
            index (int): The index of the email to fetch.
            user_id (str): The ID of the user requesting the email.
            max_retries (int): The maximum number of retry attempts in case of failure (default: 3).

        Returns:
            APIResponse: A response object indicating the status of the operation and email details, if successful.
        """
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
                    return APIResponse(status="success", message="Email already processed")

                # Process the message and return the APIResponse
                return self.extract_jobs_from_email(message, user_id)

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
                    return APIResponse(status="failure", message=f"Failed to fetch email {index} due to SSL error")

            except Exception as e:
                self.logger.error(f"An unexpected error occurred while fetching email {index}: {e}")
                return APIResponse(status="failure", message=f"Failed to fetch email {index}: {str(e)}")

        self.logger.error(f"Failed to fetch email {index} after {max_retries} attempts.")
        return APIResponse(status="failure", message=f"Failed to fetch email {index} after {max_retries} attempts")

    def fetch_and_process_email(self, index, user_id) -> APIResponse:
        """
        Retrieve an email by index, process its content, and handle job extraction if applicable.

        Args:
            index (int): The index of the email to retrieve and process.
            user_id (str): The ID of the user.

        Returns:
            APIResponse: A response indicating the result of email processing and job extraction.
        """
        self.logger.debug(f"Fetching and processing email {index}")
        result = self.retrieve_email_jobs(index, user_id)
        if result.status == "success" and "job_id" in result.data:
            job = result.data
            try:
                job_application_processor = JobApplicationProcessor(get_db())
                job_application_processor.process_job(job)
                pem = ProcessedEmailManager(get_db(), user_id)
                pem.mark_email_as_processed(job["message_id"], user_id)
                return APIResponse(status="success", message="Job processed successfully")
            except Exception as e:
                self.logger.error(f"Failed to process job: {job['title']} from email {job['message_id']}: {e}")
                return APIResponse(status="failure", message=f"Failed to process job: {job['title']}: {str(e)}")
        else:
            self.logger.warning(f"Skipping email {index} due to errors or no jobs found.")
            return result

        
    def handle_extracted_jobs(self, jobs, message_id, job_application_processor, user_id) -> APIResponse:
        """
        Process a list of job data extracted from an email and mark the email as processed upon success.

        Args:
            jobs (list): List of job data to process.
            message_id (str): The ID of the processed email.
            job_application_processor (JobApplicationProcessor): Processor object to handle job applications.
            user_id (str): The ID of the user associated with the jobs.

        Returns:
            APIResponse: A response indicating the result of job processing, including any failed jobs.
        """

        failed_jobs = []
        for job in jobs:
            try:
                job_application_processor.process_job(job)
            except Exception as e:
                self.logger.error(f"Failed to process job: {job['title']} from email {message_id}: {e}")
                failed_jobs.append(job['title'])

        if failed_jobs:
            return APIResponse(
                status="partial_failure",
                message=f"Some jobs failed to process from email {message_id}",
                data={"failed_jobs": failed_jobs}
            )
        else:
            pem = ProcessedEmailManager(get_db(), user_id)
            pem.mark_email_as_processed(message_id, user_id)
            return APIResponse(status="success", message="All jobs processed successfully")

    def fetch_jobs_from_email(self, user_id) -> APIResponse:
        try:
            self.establish_mailbox_connection()
            num_messages = len(self.mailbox.list()[1])  # Fetch the number of messages
            self.logger.info(f"Number of messages in the mailbox: {num_messages}")

            # Iterate through the most recent emails, starting from the last one
            for i in range(max(1, num_messages - self.num_messages_to_read + 1), num_messages + 1):
                self.logger.info(f"Fetching email {i} out of {num_messages}")
                result = self.retrieve_email_jobs(i, user_id)
                if result.status == "failure":
                    return result

            # Return a successful APIResponse
            return APIResponse(status="success", message="Jobs fetched successfully")

        except Exception as e:
            self.logger.error(f"Failed to fetch jobs from email: {e}")
            return APIResponse(status="failure", message="Failed to fetch jobs from email")

        finally:
            if self.mailbox:
                try:
                    self.mailbox.quit()
                    self.logger.info("Disconnected from mailbox")
                except Exception as e:
                    self.logger.error(f"Error while disconnecting from mailbox: {e}")

