import poplib
from email import parser
import re
from urllib.parse import unquote
import html

# Your Hotmail credentials
username = 'fantasiiio@hotmail.com'
password = 'tdk2hDDDD!'

# Connect to the Hotmail POP3 server
pop3_server = 'outlook.office365.com'
pop3_port = 995

# Connect to the server
mailbox = poplib.POP3_SSL(pop3_server, pop3_port)
mailbox.user(username)
mailbox.pass_(password)

# Get the number of messages
num_messages = len(mailbox.list()[1])

# Read the last 10 messages or fewer if less than 10 messages
num_messages_to_read = min(10, num_messages)
for i in range(num_messages - num_messages_to_read + 1, num_messages + 1):
    response, lines, octets = mailbox.retr(i)
    msg_content = b'\r\n'.join(lines).decode('utf-8')
    message = parser.Parser().parsestr(msg_content)
    
    if '<noreply@notifications.freelancer.com>' in message['from']:        # Extract links from the email message payload
        payload = message.get_payload()
        if isinstance(payload, list):
            for part in payload:
                body = part.get_payload(decode=True).decode('utf-8')
                # Regex pattern to find text between <a href="...">
                pattern = r'originalsrc="([^"]+)"'
                if links := re.findall(pattern, body):
                    # Print the subject, sender, and extracted links
                    print('Subject:', message['subject'])
                    print('From:', message['from'])
                    decoded_links = [html.unescape(unquote(link)) for link in links]
                    for link in decoded_links:
                        if link.startswith('https://www.freelancer.com/projects/python'):
                            print(link)


# Close the connection
mailbox.quit()