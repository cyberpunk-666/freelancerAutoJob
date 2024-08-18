from openai import OpenAI
import json
import logging
import requests
import re
import os
import hashlib
from email_sender import EmailSender
import time
from datetime import datetime, timedelta
import time
from utils import str_to_bool

import os


class JobApplicationProcessor:

    def __init__(self, email_sender, summary_storage):
        self.email_sender = email_sender
        self.summary_storage = summary_storage
        self.logger = logging.getLogger(__name__)
        self.cache = self.load_cache()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.use_gpt_cache = str_to_bool(os.getenv('USE_GPT_CACHE', 'true'))
        self.cache = self.load_cache() if self.use_gpt_cache else {}

    def load_cache(self):
        if os.path.exists("cache.json"):
            try:
                with open("cache.json", 'r') as file:
                    cache = json.load(file)
                self.logger.info('Cache loaded from file')
                return cache
            except Exception as e:
                self.logger.error(f'Failed to load cache from file: {str(e)}')
        return {}

    def save_cache(self):
        try:
            with open("cache.json", 'w') as file:
                json.dump(self.cache, file)
            self.logger.info('Cache saved to file')
        except Exception as e:
            self.logger.error(f'Failed to save cache to file: {str(e)}')

    def extract_json_string(self, input_string):
        self.logger.info('Starting extraction process')

        try:
            self.logger.info('Attempting to find JSON string in the input')
            # Use a stack to handle nested braces
            stack = []
            json_start = None

            for i, char in enumerate(input_string):
                if char == '{':
                    if not stack:
                        json_start = i
                    stack.append(char)
                elif char == '}':
                    stack.pop()
                    if not stack and json_start is not None:
                        json_str = input_string[json_start:i + 1]
                        self.logger.info(f'Found JSON string: {json_str}')

                        # Load the found JSON string to verify its validity
                        json_obj = json.loads(json_str)
                        self.logger.info('JSON string is valid')
                        return json.dumps(
                            json_obj)  # Return the valid JSON string

            self.logger.warning('No JSON string found in the input')
            return None
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.error(
                f'Error during extraction or validation: {str(e)}')
            return None

    def send_to_gpt(self,
                    prompt,
                    max_tokens=300,
                    model="gpt-3.5-turbo-1106",
                    max_retries=5):
        self.logger.info(f'Sending prompt: {prompt}')

        # Create a unique cache key
        cache_key = hashlib.md5(
            f'{prompt}{max_tokens}{model}'.encode()).hexdigest()

        if self.use_gpt_cache and cache_key in self.cache:
            self.logger.info(f'Using cached response for prompt: {prompt}')
            return self.cache[cache_key]

        retries = 0
        while retries < max_retries:
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }
                data = {
                    'model':
                    model,
                    'messages': [{
                        "role": "system",
                        "content": "You are an intelligent assistant."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    'max_tokens':
                    max_tokens,
                    'temperature':
                    0.7
                }

                response = requests.post(
                    'https://api.aimlapi.com/chat/completions',
                    headers=headers,
                    json=data)
                response.raise_for_status(
                )  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

                response_data = response.json()
                response_str = response_data['choices'][0]['message'][
                    'content'].strip()
                self.logger.info(f'GPT answer: {response_str}')

                # Cache the response if caching is enabled and response is valid
                if self.use_gpt_cache and "ERROR" not in response_str:
                    self.cache[cache_key] = response_str
                    self.save_cache()

                return response_str

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to get response from GPT: {str(e)}")
                self.logger.error(
                    f"Request payload: {json.dumps(data, indent=2)}")

                if response is not None:
                    self.logger.error(f"Response content: {response.text}")

                    # Check for 429 status code
                    if response.status_code == 429:
                        self.logger.error(
                            "Too many requests. Stopping further execution.")
                        raise SystemExit(
                            "Too many requests. Execution stopped."
                        )  # Stop execution

                retries += 1
        self.logger.error(f"Exceeded maximum retries for prompt: {prompt}")
        return None

    def parse_budget(self, budget_text):
        if not budget_text:
            self.logger.error("Budget text is missing or empty.")
            return None

        prompt = f"""
        Budget: {budget_text}

        Please convert the budget to CAD, and determine if it is an hourly or fixed rate. Provide the response in the following JSON format:

        {{
            "min_budget_cad": float,
            "max_budget_cad": float,
            "rate_type": "string (hourly or fixed)"
        }}
        """
        response_text = self.send_to_gpt(prompt)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Failed to decode JSON response: {response_text}")
                return None
        return None

    def extract_first_number(self, input_string):
        self.logger.info('Starting number extraction process')

        try:
            self.logger.info(
                'Attempting to find the first numeric value in the input')
            # Use regular expression to find the first numeric value in the input string
            match = re.search(r'\d+', input_string)
            if match:
                number = int(match.group())
                self.logger.info(f'Found numeric value: {number}')
                return number
            else:
                self.logger.warning('No numeric value found in the input')
                return None
        except Exception as e:
            self.logger.error(f'Error during number extraction: {str(e)}')
            return None

    def is_budget_acceptable(self, assumption_and_time, budget_info):
        estimated_time = self.extract_first_number(
            assumption_and_time["estimated_time"])  # Time in hours
        estimated_time = estimated_time or 0  # Default to 0 if not found
        min_budget = budget_info["min_budget_cad"]
        max_budget = budget_info["max_budget_cad"]
        rate_type = budget_info["rate_type"]

        hourly_rate = float(os.getenv('MIN_HOURLY_RATE') or 0.0)
        total_cost = estimated_time * hourly_rate

        if rate_type == "hourly" and min_budget < hourly_rate:
            self.logger.info(
                "The min budget is less than the minimum hourly rate.")
            return True

        self.logger.info(f'total_cost: {total_cost}')
        is_acceptable = total_cost <= max_budget
        self.logger.info(f"is acceptable: {is_acceptable}")
        return is_acceptable

    def generate_application_letter(self, job_description, freelancer_profile):
        prompt = f"""
        Job Description: {job_description}
        Freelancer Profile: {freelancer_profile}

        Write an application letter ensuring the text does not exceed the maximum allowed length. 
        Include:
        - A brief introduction of the freelancer
        - Specific reasons why the freelancer is a good fit for the job
        - A concise explanation of how the freelancer plans to approach the task technically
        - A closing statement emphasizing enthusiasm for the opportunity and availability for further discussion
        """

        return self.send_to_gpt(prompt, max_tokens=500)

    def analyse_job_and_time(self, job_description):
        prompt = f"""
        Job Description: {job_description}

        Analyze the tasks described in the job description. Provide an estimated time to complete the tasks in the following JSON format:

        {{
            "estimated_time": "string (e.g., '200 hours'')",
            "assumptions": "string (a brief explanation of assumptions and methodology)"
        }}
        """

        response_text = self.send_to_gpt(prompt, max_tokens=300)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Failed to decode JSON response: {response_text}")
                return None
        return None

    def analyze_job_fit(self, job_description, freelancer_profile):
        prompt = f"""
        Job Description: {job_description}
        Freelancer Profile: {freelancer_profile}

        Analyze if the job fits the freelancer's profile. Provide the response in the following JSON format:

        {{
            "fit": "boolean (true if the job fits the profile, false otherwise)",
            "reasons": "string (a brief explanation of why the job does or does not fit the profile)"
        }}
        """

        response_text = self.send_to_gpt(prompt, max_tokens=300)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Failed to decode JSON response: {response_text}")
                return None
        return None

    def send_job_details_email(self, job_title, job_description,
                               estimated_time, assumptions, budget_text):
        subject = f"New Job Found: {job_title}"
        body = f"""
        Job Title: {job_title}
        Job Description: {job_description}
        Budget: {budget_text}
        Estimated Time: {estimated_time} hours
        Assumptions: {assumptions}

        This job fits the profile and the budget is acceptable.
        """
        recipient = os.getenv('SMTP_RECIPIENT')

        try:
            self.email_sender.send_email(subject, body, recipient)
            self.logger.info(f"Email sent to {recipient} with job details.")
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")

    def send_email(self, job_title, job_description, estimated_time,
                   assumptions, budget_text, application_letter,
                   detailed_steps):
        subject = f"Application for {job_title}"
        body = f"""
        Job Title: {job_title}
        Job Description: {job_description}
        Estimated Time: {estimated_time}
        Assumptions: {assumptions}
        Budget: {budget_text}
        Application Letter: {application_letter}
        Detailed Steps: {detailed_steps}
        """
        self.email_sender.send_email(os.getenv('SMTP_RECIPIENT'), subject,
                                     body)

    def get_detailed_steps(self, job_description):
        prompt = f"""
        Job Description: {job_description}

        Write a detailed step-by-step plan to approach the tasks described in the job description. Provide the response in a clear, structured format.
        """
        return self.send_to_gpt(prompt, max_tokens=500)

    def process_jobs(self, jobs, freelancer_profile):
        summary = {
            "total_jobs": 0,
            "job_not_fit": 0,
            "budget_not_acceptable": 0,
            "applications_sent": 0,
        }

        job_titles_and_budgets = []
        job_not_fit_indices = []
        budget_not_acceptable_indices = []

        for job in jobs:
            job_title = job['title']
            job_description = job['description']
            budget_text = job['budget']
            summary["total_jobs"] += 1
            self.logger.info(f'Full job data: {job}')
            self.logger.info(f"Processing job: {job_title}")


            # Parse budget
            budget_info = self.parse_budget(budget_text)
            if budget_info is None:
                self.logger.warning(
                    f"Skipping job '{job_title}' due to missing or invalid budget information."
                )
                continue

          # Log budget_text to ensure it's populated
            self.logger.info(
                f'Extracted budget text for job "{job_title}": {budget_text}')

            if not budget_text:
                self.logger.warning(
                    f"No budget information found for job '{job_title}'. Skipping..."
                )
                continue

            # Collect job titles and budgets
            job_titles_and_budgets.append(
                f"{len(job_titles_and_budgets) + 1}. Job Title: {job_title}, Budget: {budget_text}"
            )

            # Check job fit
            job_fit = self.analyze_job_fit(job_description, freelancer_profile)
            if not job_fit or not job_fit['fit']:
                self.logger.info(
                    f"Skipping job '{job_title}' because it does not fit the freelancer's profile."
                )
                summary["job_not_fit"] += 1
                job_not_fit_indices.append(len(job_titles_and_budgets))
                continue

            # Estimate time
            assumption_and_time = self.analyse_job_and_time(job_description)
            if not assumption_and_time:
                self.logger.warning(
                    f"Skipping job '{job_title}' due to failure in estimating job"
                )
                continue

            # Check if budget is acceptable
            if not self.is_budget_acceptable(assumption_and_time, budget_info):
                self.logger.info(
                    f"Skipping job '{job_title}' because the estimated cost is not within the budget range."
                )
                summary["budget_not_acceptable"] += 1
                budget_not_acceptable_indices.append(
                    len(job_titles_and_budgets))
                continue

            estimated_time = self.extract_first_number(
                assumption_and_time['estimated_time'])
            self.logger.info(f"Applying for job '{job_title}'")
            self.logger.info(f"Estimated time: {estimated_time}")
            self.logger.info(
                f"Assumptions: {assumption_and_time['assumptions']}")

            # Generate application letter
            application_letter = self.generate_application_letter(
                job_description, freelancer_profile)
            if application_letter:
                # Get detailed steps
                detailed_steps = self.get_detailed_steps(job_description)

                # Send email
                self.send_email(job_title, job_description, estimated_time,
                                assumption_and_time['assumptions'],
                                budget_text, application_letter,
                                detailed_steps)
                self.logger.info(f"Email sent for job '{job_title}'")
                summary["applications_sent"] += 1
            else:
                self.logger.error(
                    f"Failed to generate application letter for job '{job_title}'"
                )


        summary_content = (
            "\nJob Titles and Budgets:\n" +
            "\n".join(job_titles_and_budgets) + "\n\n" +
            f"Total jobs processed: {summary['total_jobs']}\n" +
            f"Jobs that don't fit profile: {', '.join(map(str, job_not_fit_indices))}\n" +
            f"Jobs with unacceptable budget: {', '.join(map(str, budget_not_acceptable_indices))}\n" +
            f"Applications sent: {summary['applications_sent']}\n" +
            "-----------------------------------------------------------------------------------\n"
        )
        self.logger.info(f"Summary: {summary_content}")
        if summary["total_jobs"] > 0:
            self.summary_storage.append_summary(summary_content)


