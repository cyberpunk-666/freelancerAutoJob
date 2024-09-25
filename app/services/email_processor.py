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
from urllib.parse import urlparse, urlunparse
from app.models.api_response import APIResponse
import logging
from app.managers.processed_email_manager import ProcessedEmailManager
from app.db.db_utils import get_db
from app.managers.job_manager import JobManager
import time
import imaplib
import smtplib
import email
import json
from email.message import EmailMessage
class EmailProcessor:
    def __init__(self):
        self.logger = logging.getLogger()
        self.job_manager = JobManager()

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
        self.send_message_callback = None
        



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

    def extract_job_links(self, emails):
        job_links = []
        for email in emails:
            if self.target_sender in email['from']:
                payload = email.get_payload()
                if isinstance(payload, list):
                    for part in payload:
                        body = part.get_payload(decode=True).decode('utf-8')
                        links_response = self.extract_links_from_body(body)
                        if links_response.status == "success":
                            for link in links_response.data["links"]:
                                parsed_url = urlparse(link)
                                link_without_query = urlunparse(parsed_url._replace(query=""))
                                if link_without_query.startswith(self.job_link_prefix):
                                    job_links.append(link_without_query)
        
        return APIResponse(status="success", message=f"Extracted {len(job_links)} job links", data={"job_links": job_links})

    def scrape_job_details(self, job_link):
        try:
            response = requests.get(job_link)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_description = self.extract_job_description(soup)
            job_title = self.extract_job_title(soup)
            job_budget = self.extract_budget(soup)

            if job_description.status == "success" and job_title.status == "success":
                job_detail = {
                    "title": job_title.data.get("job_title"),
                    "description": job_description.data.get("job_description"),
                    "budget": job_budget.data.get("job_budget") if job_budget.status == "success" else None,
                    "link": job_link
                }
                return APIResponse(status="success", message="Job details scraped successfully", data={"job_detail": job_detail})
            else:
                return APIResponse(status="failure", message="Failed to extract all required details for job link", data={"link": job_link})

        except Exception as e:
            self.logger.error(f"Error scraping job details from {job_link}: {str(e)}")
            return APIResponse(status="failure", message=f"Error scraping job details: {str(e)}", data={"link": job_link})

    def fetch_emails(self, num_messages_to_read=10):
        specific_email = self.target_sender
        self.establish_mailbox_connection()
        if not self.is_connected():
            return APIResponse(status="failure", message="Failed to connect to email server")

        try:
            emails = []
            if self.connection_type == 'imap':
                emails = self._fetch_imap_emails(specific_email, num_messages_to_read)
            elif self.connection_type == 'pop3':
                emails = self._fetch_pop3_emails(specific_email, num_messages_to_read)
            else:
                return APIResponse(status="failure", message="Unsupported connection type")

            return APIResponse(status="success", message=f"Fetched {len(emails)} emails", data={"emails": emails})

        except Exception as e:
            self.logger.error(f"Error fetching emails: {str(e)}")
            return APIResponse(status="failure", message=f"Error fetching emails: {str(e)}")

    def _fetch_imap_emails(self, specific_email=None, num_messages_to_read=None):
        self.mailbox.select('INBOX')
        search_criteria = f'FROM "{specific_email}"' if specific_email else 'ALL'
        _, message_numbers = self.mailbox.search(None, search_criteria)
        
        email_ids = message_numbers[0].split()
        latest_emails = email_ids[-num_messages_to_read:]
        
        emails = []
        for email_id in latest_emails:
            _, msg_data = self.mailbox.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            emails.append(email_message)
        
        return emails

    def _fetch_pop3_emails(self, specific_email=None, num_messages_to_read=None):
        emails = []
        num_messages = len(self.mailbox.list()[1])
        
        for i in range(num_messages, max(1, num_messages - num_messages_to_read), -1):
            raw_email = b"\n".join(self.mailbox.retr(i)[1])
            email_message = email.message_from_bytes(raw_email)
            
            if not specific_email or (specific_email and specific_email.lower() in email_message['From'].lower()):
                emails.append(email_message)
            
            if len(emails) >= num_messages_to_read:
                break
        
        return emails



    def serialize_email(self, email_obj):
        if isinstance(email_obj, EmailMessage):
            # Convert EmailMessage object to a dictionary
            email_dict = {
                "subject": email_obj["Subject"],
                "from": email_obj["From"],
                "to": email_obj["To"],
                "body": email_obj.get_content()
            }
            # Serialize to JSON
            return json.dumps(email_dict)
        else:
            raise TypeError("Expected an EmailMessage object")

    def deserialize_email(self, serialized_email):
        try:
            # Deserialize from JSON
            email_dict = json.loads(serialized_email)
            
            # Create a new EmailMessage object
            email_obj = EmailMessage()
            email_obj["Subject"] = email_dict["subject"]
            email_obj["From"] = email_dict["from"]
            email_obj["To"] = email_dict["to"]
            email_obj.set_content(email_dict["body"])
            
            return email_obj
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
