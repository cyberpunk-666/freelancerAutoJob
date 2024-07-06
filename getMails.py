import poplib
poplib._MAXLINE = 200480
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


def extract_job_description(soup):
    div_element = soup.find('div', {'data-line-break': 'true'})
    if div_element:
        return div_element.text.strip()
    return None

def extract_job_title(soup):
    title =  soup.title
    if title:
        return title.text.strip()
    return None

def extract_links_from_body(body):
    pattern = r'originalsrc="([^"]+)"'
    links = re.findall(pattern, body)
    decoded_links = [html.unescape(unquote(link)) for link in links]
    return decoded_links

def extract_budget(soup):
    budget = soup.find(attrs={'data-size': 'mid'})
    if budget:
        return budget.text.strip()
    return None

def process_message(message):
    if TARGET_SENDER in message['from']:
        payload = message.get_payload()
        if isinstance(payload, list):
            for part in payload:
                body = part.get_payload(decode=True).decode('utf-8')
                links = extract_links_from_body(body)
                if links:
                    for link in links:
                        if link.startswith(JOB_LINK_PREFIX):
                            response = requests.get(link)
                            soup = BeautifulSoup(response.text, 'html.parser')                                                    
                            job_description = extract_job_description(soup)
                            job_title = extract_job_title(soup)
                            job_budget = extract_budget(soup)
                            if job_description is not None:
                                print('Job title:', job_title)
                                print('budget: ',job_budget)
                                print('description: ',job_description)
                                print('-------------------------')

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
