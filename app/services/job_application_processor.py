import logging
import os
import json
import hashlib
from flask_login import current_user
import psycopg2
import requests
from concurrent.futures import ThreadPoolExecutor
import re
import traceback
import time
from datetime import datetime
from app.db.db_utils import get_api_response_value
from app.managers.job_manager import JobManager
from app.managers.user_preferences_manager import UserPreferencesManager
from app.services.email_sender import EmailSender
class JobApplicationProcessor:
    def __init__(self):
        self.email_sender = EmailSender()
        self.logger = logging.getLogger(__name__)

        self.last_api_call_time = 0
        self.gemini_api_key = None
        self.logger.info("JobApplicationProcessor initialized.")

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


    def send_to_gemini(self, prompt, response_schema=None, max_tokens=4000, max_retries=5):
        """Send a prompt to the Gemini model and return the response based on the provided schema."""
        self.delay_if_necessary()  # Ensure rate limiting

        response = None
        retries = 0
        wait_time = 10
        if self.gemini_api_key is None:
            self.logger.error("Gemini API key is not set.")
            return None
        while retries < max_retries:
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
                querystring = {"key": self.gemini_api_key}

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
        """AI is creating summary for parse_budget

        Returns:
            [type]: [description]
        """
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

    def is_budget_acceptable(self, analysis_summary, budget_info):
        """Determine if the budget is acceptable based on the estimated time in hours and rate."""
        try:
            # Directly extract the estimated total time in hours from the analysis summary
            estimated_hours = int(analysis_summary['total_estimated_time'].replace('hours', '').strip())

            # Extract budget details
            min_budget = float(budget_info["min_budget_cad"])
            max_budget = float(budget_info["max_budget_cad"])
            rate_type = budget_info["rate_type"]

            hourly_rate = float(os.getenv('MIN_HOURLY_RATE') or 0.0)

            # Calculate the total cost based on the estimated hours and hourly rate
            total_cost = estimated_hours * hourly_rate

            if rate_type == "hourly" and min_budget < hourly_rate:
                self.logger.info("The min budget is less than the minimum hourly rate.")
                return False  # Not acceptable if the hourly rate is less than the minimum

            if rate_type == "fixed":
                is_acceptable = min_budget <= total_cost <= max_budget
            else:
                is_acceptable = total_cost <= max_budget

            self.logger.info(f"Total estimated time: {estimated_hours} hours")
            self.logger.info(f"Total cost: {total_cost:.2f}, Budget range: {min_budget} - {max_budget}")
            self.logger.info(f"Is budget acceptable: {is_acceptable}")
            
            return is_acceptable

        except ValueError as e:
            self.logger.error(f"Invalid budget information provided: {e}")
            return False

    def generate_application_letter(self, job_description, freelancer_profile):
        """Generate an application letter using Gemini based on the job description and freelancer profile."""
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

        # Define the response schema
        response_schema = {
            "type": "object",
            "properties": {
                "introduction": {"type": "string"},
                "fit": {"type": "string"},
                "approach": {"type": "string"},
                "closing": {"type": "string"}
            },
            "required": ["introduction", "fit", "approach", "closing"]
        }

        # Send the prompt to Gemini with the response schema
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
                "fit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5
                },
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

    def summarize_analysis(self, detailed_steps):
        """Summarize the analysis including the total estimated time and assumptions."""
        prompt = f"""
        Detailed Steps: {json.dumps(detailed_steps['steps'], indent=2)}

        Based on the detailed steps provided, summarize the overall analysis including:
        - Assumptions made during the estimation.
        - Total estimated time in hours. Ensure that the time is provided directly in hours (e.g., "160 hours").
        - Any additional considerations or potential challenges.

        The summary should be concise and structured for inclusion in a project proposal.
        """

        # Define the response schema with instructions for clarity
        response_schema = {
            "type": "object",
            "properties": {
                "assumptions": {
                    "type": "string",
                    "description": "Assumptions made during the time estimation process."
                },
                "total_estimated_time": {
                    "type": "string",
                    "description": "Total estimated time in hours, formatted as 'XXX hours'. Ensure the time is calculated in hours."
                },
                "additional_considerations": {
                    "type": "string",
                    "description": "Any additional considerations or challenges that could affect the project."
                }
            },
            "required": ["assumptions", "total_estimated_time"]
        }

        # Send the prompt to Gemini with the response schema
        response_text = self.send_to_gemini(prompt, response_schema)
        if response_text:
            try:
                json_str = self.extract_json_string(response_text)
                if not json_str:
                    return None
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to decode structured response: {response_text}")
                return None
        return None



    def get_detailed_steps(self, job_description):
        """Generate detailed steps for approaching the job based on the description."""
        prompt = f"""
        Job Description: {job_description}

        Write a detailed step-by-step plan to approach the tasks described in the job description.
        Provide the response in a clear, structured format.
        """
        
        # Define the response schema
        response_schema = {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "estimatedTime": {"type": "string"}
                        },
                        "required": ["title", "description", "estimatedTime"]
                    }
                }
            },
            "required": ["steps"]
        }

        # Send the prompt to Gemini with the response schema
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

    def load_profile(self):
        """Load the profile.txt content."""
        profile_path = 'profile.txt'
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as file:
                return file.read().strip()
        else:
            self.logger.error(f"Profile file {profile_path} not found.")
            return ""
        
    def process_job(self, user_id, job_id):
        """Process a single job by analyzing, preparing an application letter, and sending an email."""
        try:
            user_prefrences_manager = UserPreferencesManager()
            user_preferences_answer = user_prefrences_manager.get_preferences(user_id)
            user_preferences = UserPreferencesManager.get_api_response_value(user_preferences_answer, 'value')
            
            job_does_not_fit_threshold = int(user_preferences.get('job_does_not_fit_threshold', 3))
            process_job_even_if_job_does_not_fit = bool(user_preferences.get('process_job_even_if_job_does_not_fit', False))
            generate_application_letter_even_if_budget_not_acceptable = bool(user_preferences.get('generate_application_letter_even_if_budget_not_acceptable', False))

            job_manager = JobManager()
            job_response = job_manager.get_job_by_id(job_id)
            job = get_api_response_value(job_response, 'value')
            if not job:
                self.logger.error(f"Job with ID {job_id} not found.")
                return
            self.logger.info(f"Processing job: {job['job_title']}")
            
            # Load the profile.txt content
            profile = self.load_profile()

            gemini_results = {}

            # Analyze if the job fits the freelancer's profile
            job_fit = self.analyze_job_fit(job['job_description'], profile)
            gemini_results["analyze_job_fit"] = job_fit
            if not job_fit:
                self._store_job_details(job, gemini_results, "error analyzing job fit")
                self.logger.error(f"Failed to analyze job fit for job '{job['job_title']}'")
                return

            if job_fit['fit'] < job_does_not_fit_threshold and not process_job_even_if_job_does_not_fit:
                self._store_job_details(job, gemini_results, "not fitting")
                self.logger.info(f"Skipping job '{job['job_title']}' because it does not fit the freelancer's profile.")
                return

            # Generate detailed steps for the application
            detailed_steps = self.get_detailed_steps(job['job_description'])
            gemini_results["generate_detailed_steps"] = detailed_steps
            if not detailed_steps:
                self._store_job_details(job, gemini_results, "error generating steps")
                self.logger.error(f"Failed to generate detailed steps for job '{job['job_title']}'")
                return

            # Summarize the analysis including assumptions and total estimated time
            analysis_summary = self.summarize_analysis(detailed_steps)
            gemini_results["summarize_analysis"] = analysis_summary
            if not analysis_summary:
                self._store_job_details(job, gemini_results, "error summarizing analysis")
                self.logger.error(f"Failed to summarize analysis for job '{job['job_title']}'")
                return

            # Parse the budget
            budget_info = self.parse_budget(job['budget'])
            gemini_results["parse_budget"] = budget_info
            if not budget_info:
                self._store_job_details(job, gemini_results, "invalid_budget_information")
                self.logger.warning(f"Skipping job '{job['job_title']}' due to invalid budget information.")
                return

            # Check if the budget is acceptable
            if not self.is_budget_acceptable(analysis_summary, budget_info) and not generate_application_letter_even_if_budget_not_acceptable:
                self._store_job_details(job, gemini_results, "budget_not_acceptable")
                self.logger.info(f"Skipping job '{job['job_title']}' because the budget is not acceptable.")
                return

            # Generate the application letter
            application_letter = self.generate_application_letter(job['job_description'], job['profile'])
            gemini_results["generate_application_letter"] = application_letter
            if not application_letter:
                self._store_job_details(job, gemini_results, "error_generating_letter")
                self.logger.error(f"Failed to generate application letter for job '{job['job_title']}'")
                return

            # Send the application email
            self.send_email(
                job['job_title'], job['job_description'], analysis_summary['total_estimated_time'],
                analysis_summary['assumptions'], job['budget'], application_letter, detailed_steps
            )
            self._store_job_details(job, gemini_results, "processed")

        except Exception as e:
            self.logger.error(f"Failed to process job: {e}")
            self._store_job_details(job, gemini_results, "error", {e})

        except Exception as e:
            self.logger.error(f"Failed to process job: {e}")
            self._store_job_details(job, gemini_results, "error", {e})

    def _store_job_details(self, job, gemini_results, status, performance_metrics=None):
        """Helper function to store job details in the database."""
        job["gemini_results"] = gemini_results or {}
        job["status"] = status
        job["performance_metrics"] = performance_metrics or {}

        job_manager = JobManager()
        job_manager.update_job(job)
        
