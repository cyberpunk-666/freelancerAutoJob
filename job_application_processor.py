import openai
import json
import configparser
import logging
import os

class JobApplicationProcessor:
    def __init__(self, config_path='config.cfg'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        openai.api_key = self.config.get('API', 'OPENAI_API_KEY')

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def parse_budget(self, budget_text):
        try:
            budget_range = budget_text.replace('$', '').strip().split('-')
            min_budget = float(budget_range[0].strip())
            max_budget = float(budget_range[1].strip()) if len(budget_range) > 1 else min_budget
            return min_budget, max_budget
        except ValueError:
            self.logger.error(f"Failed to parse budget: {budget_text}")
            return None, None

    def is_budget_acceptable(self, estimated_cost, min_budget, max_budget):
        return min_budget <= estimated_cost <= max_budget

    def send_to_gpt(self, prompt, max_tokens=300, model="gpt-4"):
        try:
            messages = [
                {"role": "system", "content": "You are an intelligent assistant."},
                {"role": "user", "content": prompt}
            ]

            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )

            return response.choices[0].message["content"].strip()
        except Exception as e:
            self.logger.error(f"Failed to get response from GPT-4: {str(e)}")
            return None

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

    def estimate_cost_and_time(self, job_description):
        prompt = f"""
        Job Description: {job_description}

        Analyze the tasks described in the job description. Provide an estimated cost and time to complete the tasks in the following JSON format:

        {{
            "estimated_cost": "string (e.g., '$500')",
            "estimated_time": "string (e.g., '2 weeks')",
            "assumptions": "string (a brief explanation of assumptions and methodology)"
        }}
        """
        
        response_text = self.send_to_gpt(prompt, max_tokens=300)
        if response_text:
            try:
                return json.loads(response_text)
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
                return json.loads(response_text)
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
            min_budget, max_budget = self.parse_budget(budget_text)
            if min_budget is None or max_budget is None:
                self.logger.warning(f"Skipping job '{job_title}' due to missing or invalid budget information.")
                continue

            # Check job fit
            job_fit = self.analyze_job_fit(job_description, freelancer_profile)
            if not job_fit or not job_fit['fit']:
                self.logger.info(f"Skipping job '{job_title}' because it does not fit the freelancer's profile.")
                continue

            # Estimate cost and time
            cost_and_time_estimate = self.estimate_cost_and_time(job_description)
            if not cost_and_time_estimate:
                self.logger.warning(f"Skipping job '{job_title}' due to failure in estimating cost and time.")
                continue

            estimated_cost = float(cost_and_time_estimate["estimated_cost"].replace('$', '').strip())

            # Check if budget is acceptable
            if not self.is_budget_acceptable(estimated_cost, min_budget, max_budget):
                self.logger.info(f"Skipping job '{job_title}' because the estimated cost is not within the budget range.")
                continue

            self.logger.info(f"Applying for job '{job_title}' with estimated cost {estimated_cost}")
            # Apply for job using Selenium
            # self.apply_for_job_with_selenium(driver, job_title, job_link)

# Usage example:
# processor = JobApplicationProcessor()
# jobs = [
#     {
#         "title": "Example Job 1",
#         "description": "This is an example job description.",
#         "budget": "$300-$500"
#     },
#     # Add more jobs as needed
# ]
# freelancer_profile = "This is a sample freelancer profile."
# processor.process_jobs(jobs, freelancer_profile)