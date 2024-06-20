import poplib
from email import parser
import re
from urllib.parse import unquote
import html
from bs4 import BeautifulSoup
import requests

# Constants for credentials and server settings
USERNAME = 'fantasiiio@hotmail.com'
PASSWORD = 'tdk2hDDDD!'
POP3_SERVER = 'outlook.office365.com'
POP3_PORT = 995
NUM_MESSAGES_TO_READ = 10
TARGET_SENDER = '<noreply@notifications.freelancer.com>'
JOB_LINK_PREFIX = 'https://www.freelancer.com/projects/python'
JOB_DESCRIPTION_CLASSES = ['ng-star-inserted']  # Example classes

def connect_to_mailbox(username, password, server, port):
    mailbox = poplib.POP3_SSL(server, port)
    mailbox.user(username)
    mailbox.pass_(password)
    return mailbox


def fetch_job_description(url):
    response = requests.get(url)
    decoded_string = html.unescape(response.text)
    soup = BeautifulSoup(decoded_string, 'html.parser')
    
    # Function to check if an element has all specified classes
    def has_all_classes(tag):
        classes = set(tag.get('class', []))
        if classes:
            print(classes)
        return all(cls in classes for cls in JOB_DESCRIPTION_CLASSES)
    
    # Find the element using the function
    job_description = soup.find(has_all_classes, 'div')
    
    if job_description:
        return job_description.text.strip()  # Use .strip() to remove leading/trailing whitespace
    else:
        return None

def extract_links_from_body(body):
    pattern = r'originalsrc="([^"]+)"'
    links = re.findall(pattern, body)
    decoded_links = [html.unescape(unquote(link)) for link in links]
    return decoded_links

def process_message(message):
    if TARGET_SENDER in message['from']:
        payload = message.get_payload()
        if isinstance(payload, list):
            for part in payload:
                body = part.get_payload(decode=True).decode('utf-8')
                links = extract_links_from_body(body)
                if links:
                    print('Subject:', message['subject'])
                    print('From:', message['from'])
                    for link in links:
                        if link.startswith(JOB_LINK_PREFIX):
                            job_description = fetch_job_description(link)
                            if job_description is not None:
                                print(job_description)

def main():
    mailbox = connect_to_mailbox(USERNAME, PASSWORD, POP3_SERVER, POP3_PORT)
    num_messages = len(mailbox.list()[1])
    num_messages_to_read = min(NUM_MESSAGES_TO_READ, num_messages)

    for i in range(num_messages - num_messages_to_read + 1, num_messages + 1):
        retr_result = mailbox.retr(i)
        response, lines, octets = retr_result
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        message = parser.Parser().parsestr(msg_content)
        process_message(message)
    
    mailbox.quit()


if __name__ == '__main__':
    main()
