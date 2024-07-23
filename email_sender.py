import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailSender:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, to_email, subject, body):
        self.logger.info(f"Preparing to send email to {to_email} with subject '{subject}'")
        
        # Create the message
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # Create the server connection
            self.logger.info("Connecting to the SMTP server")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Use TLS
            server.login(self.username, self.password)
            self.logger.info("Successfully logged in to the SMTP server")
            
            # Send the email
            text = msg.as_string()
            server.sendmail(self.username, to_email, text)
            self.logger.info(f"Email sent successfully to {to_email}")
            
            # Terminate the SMTP session
            server.quit()
            self.logger.info("SMTP session terminated")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")

# Example usage:
# sender = EmailSender("smtp.gmail.com", 587, "your_email@gmail.com", "your_password")
# sender.send_email("recipient_email@gmail.com", "Test Subject", "This is the body of the email.")