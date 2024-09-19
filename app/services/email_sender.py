import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import re
from threading import Lock
import os
import ssl

class EmailSender:
    _instance = None
    _lock = Lock()  # This will make it thread-safe

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                logging.info("Creating a new instance of EmailSender")
                cls._instance = super(EmailSender, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Ensure that the __init__ is only called once in the lifecycle
        if not hasattr(self, '_initialized'):
            self.smtp_server = os.getenv('SMTP_SERVER')
            self.smtp_port = int(os.getenv('SMTP_PORT', 465))  # Cast to int and provide default
            self.username = os.getenv('SMTP_USERNAME')
            self.password = os.getenv('SMTP_PASSWORD')
            
            if not self.smtp_server or not self.smtp_port or not self.username or not self.password:
                logging.error("Missing SMTP configuration in environment variables")

            self._initialized = True  # Mark the class as initialized

    def send_email(self, recipient, subject, text_body, html_body=None):
        if not self.validate_email_address(recipient):
            logging.error(f"Invalid email address: {recipient}")
            return False

        logging.info("Creating the email message")
        context = ssl.create_default_context()  # Default context already handles check_hostname and verify_mode
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = recipient

        logging.info("Attaching plain text part to the email")
        part1 = MIMEText(text_body, 'plain')
        msg.attach(part1)

        if html_body:
            logging.info("Attaching HTML part to the email")
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

        logging.info("Connecting to SMTP server")
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.set_debuglevel(1)
                server.ehlo()  # Identify ourselves to the SMTP server

                logging.info("Attempting to log in to the SMTP server")
                server.login(self.username, self.password)
                logging.info("Login successful")

                logging.info("Sending the email")
                server.sendmail(self.username, recipient, msg.as_string())
                logging.info(f"Email sent successfully to {recipient}")
                return True

        except smtplib.SMTPException as e:
            logging.error(f"SMTP error occurred: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred while sending email: {e}")

        return False

    def validate_email_address(self, email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None
