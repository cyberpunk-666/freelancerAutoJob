# test_env.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
email_username = os.getenv('EMAIL_USERNAME')
email_password = os.getenv('EMAIL_PASSWORD')
openai_api_key = os.getenv('OPENAI_API_KEY')

print(f"EMAIL_USERNAME: {email_username}")
print(f"EMAIL_PASSWORD: {email_password}")
print(f"OPENAI_API_KEY: {openai_api_key}")
