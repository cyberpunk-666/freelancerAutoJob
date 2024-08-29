import logging
import os
import json
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor
from utils import str_to_bool
import re
import traceback
import time
import datetime
class JobApplicationProcessor:
    def __init__(self, email_sender, job_details):
        self.job_details = job_details
        self.email_sender = email_sender
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.use_gpt_cache = str_to_bool(os.getenv('USE_GPT_CACHE', 'true'))
        self.cache = self.load_cache() if self.use_gpt_cache else {}
        self.last_api_call_time = 0
        self.logger.info("JobApplicationProcessor initialized.")

    def load_cache(self):
        """Load the GPT response cache from a file if it exists."""
        if os.path.exists("cache.json"):
            try:
                with open("cache.json", 'r') as file:
                    cache = json.load(file)
                self.logger.info('Cache loaded from file.')
                return cache
            except Exception as e:
                self.logger.error(f'Failed to load cache from file: {e}')
        return {}

    def save_cache(self):
        """Save the GPT response cache to a file."""
        try:
            with open("cache.json", 'w') as file:
                json.dump(self.cache, file)
            self.logger.info('Cache saved to file.')
        except Exception as e:
            self.logger.error(f'Failed to save cache to file: {e}')

    def extract_json_string(self, input_string):
        """Extract a JSON string from a larger text string."""
        self.logger.info('Starting extraction process.')
        try:
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
                        json_obj = json.loads(json_str)
                        self.logger.info('JSON string is valid.')
                        return json.dumps(json_obj)
            self.logger.warning('No JSON string found in the input.')
            return None
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.error(f'Error during extraction or validation: {e}')
            return None

    def delay_if_necessary(self, delay=3):
        """Ensure at least two seconds between API calls."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        if time_since_last_call < delay:
            time_to_wait = delay - time_since_last_call
            self.logger.info(f"Waiting for {time_to_wait:.2f} seconds before the next API call.")
            time.sleep(time_to_wait)
        self.last_api_call_time = time.time()

    def send_to_gpt(self, prompt, max_tokens=4000, model="gpt-3.5-turbo-1106", max_retries=5):
        """Send a prompt to the GPT model and return the response."""
        self.logger.info(f'Sending prompt to GPT: {prompt}')

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
                    'model': model,
                    'messages': [{"role": "system", "content": "You are an intelligent assistant."}, {"role": "user", "content": prompt}],
                    'max_tokens': max_tokens,
                    'temperature': 0.7
                }

                response = requests.post(
                    'https://api.aimlapi.com/chat/completions', headers=headers, json=data)
                response.raise_for_status()
                response_data = response.json()
                response_str = response_data['choices'][0]['message']['content'].strip(
                )
                self.logger.info(f'GPT response received: {response_str}')

                if self.use_gpt_cache and "ERROR" not in response_str:
                    self.cache[cache_key] = response_str
                    self.save_cache()

                return response_str

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to get response from GPT: {e}")
                if response is not None:
                    self.logger.error(f"Response content: {response.text}")

                if response is not None and response.status_code == 429:
                    self.logger.error(
                        "Too many requests. Stopping further execution.")
                    raise SystemExit("Too many requests. Execution stopped.")

                retries += 1
        self.logger.error(f"Exceeded maximum retries for prompt: {prompt}")
        return None

    def send_to_gemini(self, prompt, response_schema=None, max_tokens=4000, max_retries=5):
        """Send a prompt to the Gemini model and return the response based on the provided schema."""
        self.delay_if_necessary()  # Ensure rate limiting

        self.logger.info(f'Sending prompt to Gemini: {prompt}')
        cache_key = hashlib.md5(f'{prompt}'.encode()).hexdigest()

        if self.use_gpt_cache and cache_key in self.cache:
            self.logger.info(f'Using cached response for prompt: {prompt}')
            return self.cache[cache_key]

        retries = 0
        while retries < max_retries:
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
                querystring = {"key": self.api_key}

                data = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 1,
                        "topK": 64,
                        "topP": 0.95,
                        "maxOutputTokens": max_tokens,
                        "responseMimeType": "application/json",
                        "responseSchema": response_schema
                    }
                }

                payload = json.dumps(data)
                headers = {
                    'Content-Type': 'application/json'
                }

                response = requests.post(url, headers=headers, params=querystring, data=payload)
                response.raise_for_status()
                response_data = response.json()

                # Adapt this part based on your response schema
                response_str = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
                self.logger.info(f'Gemini response received: {response_str}')

                if self.use_gpt_cache and "ERROR" not in response_str:
                    self.cache[cache_key] = response_str
                    self.save_cache()

                return response_str

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to get response from Gemini: {e}")
                if response is not None:
                    self.logger.error(f"Response content: {response.text}")

                if response is not None and response.status_code == 429:
                    retries += 1
                    wait_time = 2 ** retries  # Exponential backoff
                    self.logger.warning(f"Too many requests. Retrying in {wait_time} seconds (Attempt {retries}/{max_retries}).")
                    time.sleep(wait_time)
                else:
                    break  # Exit loop if the error is not due to rate limiting
            
        self.logger.error(f"Exceeded maximum retries for prompt: {prompt}")
        return None

    def parse_budget(self, budget_text):
        """Parse the budget text using Gemini and return it in a structured format."""
        if not budget_text:
            self.logger.error("Budget text is missing or empty.")
            return None

        prompt = f"""
        Budget: {budget_text}

        Please convert the budget to CAD, and determine if it is an hourly or fixed rate. Provide the structured information accordingly.
        """

        response_schema = {
            "type": "object",
            "properties": {
                "min_budget_cad": {"type": "number", "format": "float"},
                "max_budget_cad": {"type": "number", "format": "float"},
                "rate_type": {
                    "type": "string",
                    "enum": ["hourly", "fixed"]
                }
            },
            "required": ["min_budget_cad", "max_budget_cad", "rate_type"]
        }

        response_text = self.send_to_gemini(prompt, response_schema)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Failed to decode structured response: {response_text}")
                return None
        return None

    def extract_first_number(self, input_string):
        """Extract the first numeric value found in a string."""
        self.logger.info('Starting number extraction process.')

        try:
            match = re.search(r'\d+', input_string)
            if match:
                number = int(match.group())
                self.logger.info(f'Found numeric value: {number}')
                return number
            else:
                self.logger.warning('No numeric value found in the input.')
                return None
        except Exception as e:
            self.logger.error(f'Error during number extraction: {e}')
            return None

    def is_budget_acceptable(self, assumption_and_time, budget_info):
        """Determine if the budget is acceptable based on the estimated time and rate."""
        estimated_time = self.extract_first_number(
            assumption_and_time["estimated_time"])
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
        try:
            is_acceptable = total_cost <= float(max_budget)
        except ValueError:
            # Gérer le cas où max_budget ne peut pas être converti en float
            self.logger.error(f"Invalid max_budget value: {max_budget}")
            is_acceptable = False
        self.logger.info(f"Is budget acceptable: {is_acceptable}")
        return is_acceptable

    def generate_application_letter(self, job_description, freelancer_profile):
        """Generate an application letter using GPT based on the job description and freelancer profile."""
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

        return self.send_to_gemini(prompt)

    def analyse_job_and_time(self, job_description):
        """Analyze the job description and estimate the time required to complete it."""
        prompt = f"""
        Job Description: {job_description}

        Analyze the tasks described in the job description. Provide an estimated time to complete the tasks and include any assumptions or methodology used.
        """

        response_schema = {
            "type": "object",
            "properties": {
                "estimated_time": {"type": "string"},
                "assumptions": {"type": "string"}
            },
            "required": ["estimated_time", "assumptions"]
        }

        response_text = self.send_to_gemini(prompt, response_schema)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Failed to decode structured response: {response_text}")
                return None
        return None

    def analyze_job_fit(self, job_description, freelancer_profile):
        """Analyze if the job fits the freelancer's profile using Gemini."""
        prompt = f"""
        Job Description: {job_description}
        Freelancer Profile: {freelancer_profile}

        Analyze if the job fits the freelancer's profile and explain the reasoning behind your conclusion.
        """

        response_schema = {
            "type": "object",
            "properties": {
                "fit": {"type": "boolean"},
                "reasons": {"type": "string"}
            },
            "required": ["fit", "reasons"]
        }

        response_text = self.send_to_gemini(prompt, response_schema)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(
                    f"Failed to decode structured response: {response_text}")
                return None
        return None

    def send_job_details_email(self, job_title, job_description, estimated_time, assumptions, budget_text):
        """Send an email with the details of the job found."""
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
            self.logger.error(f"Failed to send email: {e}")

    def send_email(self, job_title, job_description, estimated_time, assumptions, budget_text, application_letter, detailed_steps):
        """Send an email with the application details for the job."""
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
        recipient = os.getenv('SMTP_RECIPIENT')

        try:
            self.email_sender.send_email(recipient, subject, body)
            self.logger.info(
                f"Application email sent to {recipient} for job {job_title}.")
        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Failed to send application email: {e}\n{error_details}")            

    def get_detailed_steps(self, job_description):
        """Generate detailed steps for approaching the job based on the description."""
        prompt = f"""
        Job Description: {job_description}

        Write a detailed step-by-step plan to approach the tasks described in the job description. Provide the response in a clear, structured format.
        """
        return self.send_to_gemini(prompt)

    def process_jobs_from_email(self, jobs, message_id, email_processor):
        """Process all jobs from a single email and mark the email as processed if successful."""
        try:
            # Process jobs in parallel
            self.process_jobs(jobs)
            email_processor.mark_email_as_processed(message_id)
        except Exception as e:
            self.logger.error(
                f"An error occurred while processing jobs from email {message_id}: {e}")
            # Do not mark the email as processed
            
    def process_jobs(self, jobs):
        """Process a list of jobs sequentially."""
        for job in jobs:
            # Generate the job ID
            job_id = self.job_details.generate_job_id(job['title'])

            # Check if the job already exists in the database
            existing_job = self.job_details.read_job(job_id)
            if existing_job:
                # Update the existing job with the new occurrence timestamp and increment the count
                updated_data = {
                    'last_occurrence': datetime.now(),
                    'occurrence_count': existing_job['occurrence_count'] + 1
                }
                self.job_details.update_job(job_id, updated_data)
                self.logger.info(f"Updated job '{job['title']}' with new occurrence timestamp and count.")
                continue
            
            # Process the job if it's not in the database
            self.process_job(job)

            



    def load_profile(self):
        """Load the profile.txt content."""
        profile_path = 'profile.txt'
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as file:
                return file.read().strip()
        else:
            self.logger.error(f"Profile file {profile_path} not found.")
            return ""
        
    def process_job(self, job):
        """Process a single job by analyzing, preparing an application letter, and sending an email."""
        try:
            self.logger.info(f"Processing job: {job['title']}")

            # Load the profile.txt content
            job['profile'] = self.load_profile()

            gemini_results = {}

            # Analyze the job and determine the time required
            assumption_and_time = self.analyse_job_and_time(job['description'])
            if not assumption_and_time:
                self._store_job_details(job, gemini_results, "error_estimating_time")
                self.logger.warning(f"Skipping job '{job['title']}' due to failure in estimating time.")
                return
            gemini_results["analyse_job_and_time"] = assumption_and_time

            # Parse the budget
            budget_info = self.parse_budget(job['budget'])
            if not budget_info:
                self._store_job_details(job, gemini_results, "invalid_budget_information")
                self.logger.warning(f"Skipping job '{job['title']}' due to invalid budget information.")
                return
            gemini_results["parse_budget"] = budget_info

            # Check if the budget is acceptable
            if not self.is_budget_acceptable(assumption_and_time, budget_info):
                self._store_job_details(job, gemini_results, "budget_not_acceptable")
                self.logger.info(f"Skipping job '{job['title']}' because the budget is not acceptable.")
                return

            # Analyze if the job fits the freelancer's profile
            job_fit = self.analyze_job_fit(job['description'], job['profile'])
            if not job_fit or not job_fit['fit']:
                self._store_job_details(job, gemini_results, "not_a_fit")
                self.logger.info(f"Skipping job '{job['title']}' because it does not fit the freelancer's profile.")
                return
            gemini_results["analyze_job_fit"] = job_fit

            # Generate the application letter
            application_letter = self.generate_application_letter(job['description'], job['profile'])
            if not application_letter:
                self._store_job_details(job, gemini_results, "error_generating_letter")
                self.logger.error(f"Failed to generate application letter for job '{job['title']}'")
                return
            gemini_results["generate_application_letter"] = application_letter

            # Generate detailed steps for the application
            detailed_steps = self.get_detailed_steps(job['description'])
            if not detailed_steps:
                self._store_job_details(job, gemini_results, "error_generating_steps")
                self.logger.error(f"Failed to generate detailed steps for job '{job['title']}'")
                return
            gemini_results["generate_detailed_steps"] = detailed_steps

            # Send the application email
            self.send_email(
                job['title'], job['description'], assumption_and_time['estimated_time'],
                assumption_and_time['assumptions'], job['budget'], application_letter, detailed_steps
            )
            self._store_job_details(job, gemini_results, "processed")

        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Failed to process job '{job['title']}': {e}\n{error_details}")
            self._store_job_details(job, gemini_results, "error", {"error_details": error_details})

    def _store_job_details(self, job, gemini_results, status, performance_metrics=None):
        """Helper function to store job details in the database."""
        self.job_details.create_job(
            job_title=job['title'],
            job_description=job.get('description', ''),
            budget=job.get('budget', ''),
            email_date=job.get('email_date', datetime.now()),
            gemini_results=gemini_results,
            status=status,
            performance_metrics=performance_metrics or {}
        )