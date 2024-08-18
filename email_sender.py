import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

class EmailSender:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, recipient, subject, body, html_body=None):
        logging.info("Creating the email message")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = recipient

        logging.info("Attaching plain text part to the email")
        part1 = MIMEText(body, 'plain')
        msg.attach(part1)

        if html_body:
            logging.info("Attaching HTML part to the email")
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

        logging.info("Connecting to SMTP server")
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.set_debuglevel(1)  # Enable debug output for the SMTP session
            server.ehlo()  # Identify ourselves to the SMTP server

            if server.has_extn('STARTTLS'):
                logging.info("STARTTLS is supported by the server. Starting TLS.")
                server.starttls()
                server.ehlo()  # Re-identify ourselves over TLS connection
            else:
                logging.warning("STARTTLS is not supported by the server.")

            logging.info("Attempting to log in to the SMTP server")
            try:
                server.login(self.username, self.password)
                logging.info("Login successful")
            except smtplib.SMTPException as e:
                logging.error(f"Login failed: {e}")
                raise

            logging.info("Sending the email")
            server.sendmail(self.username, recipient, msg.as_string())
            logging.info(f"Email sent successfully to {recipient}")

