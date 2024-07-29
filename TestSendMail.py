import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, body, to_email):
    # SMTP server details
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    smtp_username = "fantasiiio@hotmail.com"
    smtp_password = "tdk2hDDDD!"
    
    # Email details
    from_email = smtp_username
    to_email = to_email

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_username, smtp_password)

        # Send email
        server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()

# Example usage
send_email("Test Subject", "This is the body of the email.", "fantasiiio@hotmail.com")
