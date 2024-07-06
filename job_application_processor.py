from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class JobApplicationProcessor:
    def __init__(self, config_path='config.cfg'):
        # Initialize from config or parameters
        self.cv_path = "cv.pdf"  # Path to your CV
        self.introduction_letter = self.load_introduction_letter("profile.txt")

    def load_introduction_letter(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Introduction letter file '{file_path}' not found.")
            return ""
    
    def process_jobs(self, jobs, freelancer_profile):
        # Initialize Chrome driver (you can use other browsers as well)
        driver = webdriver.Chrome()
        driver.maximize_window()

        try:
            for job in jobs:
                job_title = job['title']
                job_link = job['link']
                job_description = job['description']
                budget_text = job['budget']

                # Parse budget
                min_budget, max_budget = self.parse_budget(budget_text)
                if min_budget is None or max_budget is None:
                    print(f"Skipping job '{job_title}' due to missing budget information.")
                    continue

                # Check job fit
                job_fit = self.analyze_job_fit(job_description, freelancer_profile)
                if not job_fit['fit']:
                    print(f"Skipping job '{job_title}' because it does not fit the freelancer's profile.")
                    continue

                # Estimate cost and time
                cost_and_time_estimate = self.estimate_cost_and_time(job_description)
                estimated_cost = float(cost_and_time_estimate["estimated_cost"].replace('$', '').strip())

                # Check if budget is acceptable
                if not self.is_budget_acceptable(estimated_cost, min_budget, max_budget):
                    print(f"Skipping job '{job_title}' because the estimated cost is not within the budget range.")
                    continue

                # Apply for job using Selenium
                # self.apply_for_job_with_selenium(driver, job_title, job_link)

        finally:
            # Close the browser window
            driver.quit()

    def apply_for_job_with_selenium(self, driver, job_title, job_link):
        # Open the job link
        driver.get(job_link)
        time.sleep(3)  # Wait for the page to load (adjust as needed)

        try:
            # Example interaction with the apply button (you need to find the actual button)
            apply_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[@id="apply-button"]'))
            )
            apply_button.click()

            # Fill out the application form fields
            cover_letter_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'cover_letter'))
            )
            cover_letter_field.send_keys(self.introduction_letter)

            # Upload CV
            cv_upload_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'cv_upload'))
            )
            cv_upload_field.send_keys(self.cv_path)

            # Submit the application (example)
            submit_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[@id="submit-button"]'))
            )
            submit_button.click()

            print(f"Application submitted successfully for job: {job_title}")

        except Exception as e:
            print(f"Failed to apply for job '{job_title}'. Error: {str(e)}")