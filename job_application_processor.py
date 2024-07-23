from openai import OpenAI
import json
import configparser
import logging
import requests
import re
import os
import hashlib

class JobApplicationProcessor:
    def __init__(self, config_path='config.cfg'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.api_key = self.config.get('API', 'OPENAI_API_KEY')
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(
            api_key = self.api_key
        )
        self.cache = self.load_cache()

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
            with open("cache.json",  'w') as file:
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
                        return json.dumps(json_obj)  # Return the valid JSON string

            self.logger.warning('No JSON string found in the input')
            return None
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.error(f'Error during extraction or validation: {str(e)}')
            return None

    def send_to_gpt(self, prompt, max_tokens=300, model="gpt-3.5-turbo"):
        self.logger.info(f'sending prompt: {prompt}')
        
        # Create a unique cache key
        cache_key = hashlib.md5(f'{prompt}{max_tokens}{model}'.encode()).hexdigest()
        if cache_key in self.cache:
            self.logger.info(f'Using cached response for prompt: {prompt}')
            return self.cache[cache_key]
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            data = {
                'model': model,
                'messages': [
                    {"role": "system", "content": "You are an intelligent assistant."},
                    {"role": "user", "content": prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': 0.7
            }

            response = requests.post('https://api.aimlapi.com/chat/completions', headers=headers, json=data)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
            response_data = response.json()
            
            response_str = response_data['choices'][0]['message']['content'].strip()
            self.logger.info(f'GPT answer: {response_str}')
            
            # Cache the response if it does not contain "ERROR"
            if "ERROR" not in response_str:
                self.cache[cache_key] = response_str
                self.save_cache()
            
            return response_str
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get response from GPT-4: {str(e)}")
            return None


    def parse_budget(self, budget_text):
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
                self.logger.error(f"Failed to decode JSON response: {response_text}")
                return None
        return None
        
    def extract_first_number(self, input_string):
        self.logger.info('Starting number extraction process')
        
        try:
            self.logger.info('Attempting to find the first numeric value in the input')
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
        estimated_time = self.extract_first_number(assumption_and_time["estimated_time"])  # Time in hours
        min_budget = budget_info["min_budget_cad"]
        max_budget = budget_info["max_budget_cad"]
        rate_type = budget_info["rate_type"]
    
        hourly_rate = float(self.config.get('GENERAL', 'MIN_HOURLY_RATE'))
        total_cost = estimated_time * hourly_rate
        
        self.logger.info(f'total_cost: {total_cost}')
        is_acceptable = min_budget <= total_cost <= max_budget
        self.logger.info(f"is acceptable:{is_acceptable}")
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
                self.logger.error(f"Failed to decode JSON response: {response_text}")
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
                self.logger.error(f"Failed to decode JSON response: {response_text}")
                return None
        return None

    def process_jobs(self, jobs, freelancer_profile):
        for job in jobs:
            job_title = job['title']
            job_description = job['description']
            budget_text = job['budget']

            self.logger.info(f"Processing job: {job_title}")

            # Parse budget
            budget_info = self.parse_budget(budget_text)
            if budget_info is None:
                self.logger.warning(f"Skipping job '{job_title}' due to missing or invalid budget information.")
                continue

            # Check job fit
            job_fit = self.analyze_job_fit(job_description, freelancer_profile)
            if not job_fit or not job_fit['fit']:
                self.logger.info(f"Skipping job '{job_title}' because it does not fit the freelancer's profile.")
                continue

            # Estimate time
            assumption_and_time = self.analyse_job_and_time(job_description)
            if not assumption_and_time:
                self.logger.warning(f"Skipping job '{job_title}' due to failure in estimating job")
                continue

            # Check if budget is acceptable
            if not self.is_budget_acceptable(assumption_and_time, budget_info):
                self.logger.info(f"Skipping job '{job_title}' because the estimated cost is not within the budget range.")
                continue
            estimated_time = self.extract_first_number(assumption_and_time['estimated_time'])
            self.logger.info(f"Applying for job '{job_title}'")
            self.logger.info(f"Estimated time: {estimated_time}")
            self.logger.info(f"Assumptions: {assumption_and_time['assumptions']}")
            
            # Apply for job using Selenium
            # self.apply_for_job_with_selenium(driver, job_title, job_link)
