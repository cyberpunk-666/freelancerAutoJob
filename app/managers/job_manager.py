import hashlib
import logging
from datetime import datetime, timezone
import os

from flask_login import current_user
import requests
from app.db.postgresdb import PostgresDB
from app.models.api_response import APIResponse
from app.db.db_utils import get_db
from enum import Enum, auto


job_status = [{
    "id": 1,
    "name": "New",
    "color": "green"
},{
    "id": 2,
    "name": "In Progress",
    "color": "yellow"
},{
    "id": 3,
    "name": "Processed",
    "color": "blue"
},{
    "id": 4,
    "name": "Failed",
    "color": "red"
},{
    "id": 5,
    "name": "Not a Fit",
    "color": "black"
},{
    "id": 6,
    "name": "Applied",
    "color": "purple"
}]

class JobManager:
    def __init__(self):
        self.db:PostgresDB = get_db()
        self.logger = logging.getLogger(__name__)

    def create_table(self) -> APIResponse:
        """Create the jobs and job_applications tables if they don't exist."""
        try:

            # Example table creation SQL
            create_table_query = """
            CREATE TABLE IF NOT EXISTS job_details (
                job_id VARCHAR(32) PRIMARY KEY, -- MD5 hash of job_title
                job_title TEXT NOT NULL,
                job_description TEXT,
                budget VARCHAR(50),
                email_date TIMESTAMP, -- When the job was received via email
                gemini_results JSONB, -- JSON array/object of all Gemini results
                job_fit INTEGER CHECK (job_fit >= 1 AND job_fit <= 5), -- Job fit score
                status VARCHAR(50),
                performance_metrics JSONB,
                user_id INTEGER NOT NULL, -- User who posted the job
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status_id INTEGER NOT NULL -- Status of the job
            );

            """

            # Create the table
            self.db.create_table(create_table_query)
            create_job_applications_table_query = """
            CREATE TABLE IF NOT EXISTS job_applications (
                application_id SERIAL PRIMARY KEY,
                job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                status VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.db.execute_query(create_job_applications_table_query)

            self.logger.info("Jobs and job_applications tables created successfully")
            return APIResponse(status="success", message="Tables created successfully")
        except Exception as e:
            self.logger.error("Failed to create jobs and job_applications tables", exc_info=True)
            return APIResponse(status="failure", message="Failed to create tables")

    def add_new_job(self, job_data) -> APIResponse:
        """Post a new job."""
        try:
            self.db.add_object("job_details", job_data)
            self.logger.info(f"New job posted")
            return APIResponse(status="success", message="Job posted successfully")
        except Exception as e:
            self.logger.error(f"Failed to add new job", exc_info=True)
            return APIResponse(status="failure", message="Failed to post job")

    def update_job(self, job_data):
        try:
            self.db.update_object("job_details", job_data, {"job_id": job_data["job_id"]})
            self.logger.info(f"Job {job_data['job_id']} updated")
            return APIResponse(status="success", message="Job updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update job {job_data['job_id']}", exc_info=True)
            return APIResponse(status="failure", message="Failed to update job")

    def get_job_by_id(self, job_id):
        try:
            job_detail = self.db.get_object("job_details", {"job_id": job_id})
            self.logger.info(f"Retrieved job {job_id}")
            return APIResponse(status="success", message="Job retrieved successfully", data=job_detail)
        except Exception as e:
            self.logger.error(f"Failed to retrieve job {job_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve job")

    def apply_for_job(self, job_id, user_id) -> APIResponse:
        """Apply for a job."""
        try:
            application_data = {
                "job_id": job_id,
                "user_id": user_id,
                "status": "applied"
            }
            self.db.add_object("job_applications", application_data)
            self.logger.info(f"User {user_id} applied for job {job_id}")
            return APIResponse(status="success", message="Job application submitted successfully")
        except Exception as e:
            self.logger.error(f"Failed to apply for job {job_id} for user {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to apply for job")

    def get_job_applications(self, job_id) -> APIResponse:
        """Get all applications for a job."""
        try:
            query = """
            SELECT ja.application_id, ja.user_id, ja.status, ja.applied_at
            FROM job_applications ja
            WHERE ja.job_id = %s
            """
            results = self.db.fetch_all(query, (job_id,))
            applications = [
                {
                    "application_id": row[0],
                    "user_id": row[1],
                    "status": row[2],
                    "applied_at": row[3].isoformat()
                }
                for row in results
            ]
            self.logger.info(f"Retrieved {len(applications)} applications for job {job_id}")
            return APIResponse(status="success", message="Job applications retrieved successfully", data=applications)
        except Exception as e:
            self.logger.error(f"Failed to retrieve applications for job {job_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve job applications")

    def update_application_status(self, application_id, new_status) -> APIResponse:
        """Update the status of a job application."""
        try:
            self.db.update_object(
                "job_applications",
                {"status": new_status},
                {"application_id": application_id}
            )
            self.logger.info(f"Updated application {application_id} status to {new_status}")
            return APIResponse(status="success", message="Application status updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update status for application {application_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to update application status")

    def get_user_job_applications(self, user_id) -> APIResponse:
        """Get all job applications for a user."""
        try:
            query = """
            SELECT ja.application_id, j.title, j.company, ja.status, ja.applied_at
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.job_id
            WHERE ja.user_id = %s
            """
            results = self.db.fetch_all(query, (user_id,))
            applications = [
                {
                    "application_id": row[0],
                    "job_title": row[1],
                    "company": row[2],
                    "status": row[3],
                    "applied_at": row[4].isoformat()
                }
                for row in results
            ]
            self.logger.info(f"Retrieved {len(applications)} job applications for user {user_id}")
            return APIResponse(status="success", message="User job applications retrieved successfully", data=applications)
        except Exception as e:
            self.logger.error(f"Failed to retrieve job applications for user {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve user job applications")

    def get_jobs_for_user(self, user_id) -> APIResponse:
        """Get all jobs for a user."""
        try:
            query = """
            SELECT job_id, job_title, job_description, budget, email_date, gemini_results, status, performance_metrics, user_id, created_at, status_id
            FROM job_details
            WHERE user_id = %s
            """
            results = self.db.fetch_all(query, (user_id, ))
            jobs = [
                {
                    "job_id": row[0],
                    "job_title": row[1],
                    "job_description": row[2],
                    "budget": row[3],
                    "email_date": row[4].isoformat() if row[4] else None,
                    "gemini_results": row[5],
                    "status": row[6],
                    "performance_metrics": row[7],
                    "user_id": row[8],
                    "created_at": row[9].isoformat(),
                    "status_id": row[10]
                }
                for row in results
            ]
            self.logger.info(f"Retrieved {len(jobs)} jobs for user {user_id}")
            return APIResponse(status="success", message="User jobs retrieved successfully", data=jobs)
        except Exception as e:
            self.logger.error(f"Failed to retrieve jobs for user {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve user jobs")
        

    def fetch_and_store_jobs(self) -> APIResponse:
        """Fetch jobs from Freelancer API and store them in the database."""
        try:
            # Fetch job categories for the current user
            job_categories = [6, 9, 13, 22]
            user_currency = "cad" #current_user.currency  # Assumed to be part of the user profile
            
            # Get the limit from environment variables or use a default value
            limit = os.environ.get('FREELANCER_API_LIMIT', 2)

            # Base URL for Freelancer API
            freelancer_api_base_url = "https://www.freelancer.com/api/projects/0.1/projects/active"
            
            # Construct the jobs[] query parameters dynamically from job_categories
            job_params = "&".join([f"jobs[]={job}" for job in job_categories])

            # Build full URL, including the limit from environment variables
            freelancer_api_url = f"{freelancer_api_base_url}?limit={limit}&offset=0&full_description&{job_params}&languages[]=en&sort_field=submitdate&compact=true"
            
            # Make request to Freelancer API
            response = requests.get(freelancer_api_url)
            freelancer_data = response.json()

            # Check if the response status is success
            if response.status_code == 200 and freelancer_data.get('status') == 'success':
                projects = freelancer_data['result']['projects']

                for project in projects:
                    # Convert budget to user's currency
                    converted_budget = self.convert_budget(
                        project['currency']['code'], 
                        user_currency, 
                        project['budget']['minimum'], 
                        project['budget']['maximum']
                    )

                    # Prepare job data for insertion
                    job_data = {
                        'job_id': hashlib.md5(project['title'].encode()).hexdigest(),
                        'job_title': project['title'],
                        'job_description': project['description'],
                        'budget': converted_budget,
                        'email_date': datetime.fromtimestamp(
                            project.get('time_updated', project.get('time_submitted')), tz=timezone.utc
                        ),
                        'gemini_results': "{}",  # Placeholder for future use
                        'status': project['status'],
                        'performance_metrics': "{}",  # Placeholder for future use
                        'user_id': current_user.user_id,
                        'status_id': 1  # Default status for new jobs
                    }

                    # Store job data in the database
                    self.add_new_job(job_data)

                self.logger.info(f"Successfully fetched and stored {len(projects)} jobs for user {current_user.user_id}.")
                return APIResponse(status="success", message="Jobs fetched and stored successfully", data={"jobs_fetched": len(projects)})
            
            else:
                error_message = freelancer_data.get('message', 'No error message provided')
                self.logger.error(f"Failed to fetch data from Freelancer API: {error_message}")
                return APIResponse(status="failure", message=f"Failed to fetch jobs: {error_message}")

        except Exception as e:
            self.logger.error(f"Error while fetching and storing jobs: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message="Error while fetching and storing jobs")

    def convert_budget(self, from_currency, to_currency, min_budget, max_budget) -> str:
        """Convert budget from one currency to another."""
        try:
            from_currency = from_currency.lower()
            # Base URL structure for the new API
            base_url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{from_currency}.json"
            
            response = requests.get(base_url)
            data = response.json()

            if response.status_code == 200 and to_currency in data[from_currency]:
                # Fetch the conversion rate for the target currency
                rate = data[from_currency].get(to_currency)
                if rate:
                    # Perform the conversion
                    converted_min = float(rate) * min_budget
                    converted_max = float(rate) * max_budget
                    self.logger.info(f"Converted {min_budget}-{max_budget} {from_currency} to {converted_min:.2f}-{converted_max:.2f} {to_currency}.")
                    return f"{converted_min:.2f}-{converted_max:.2f} {to_currency}"

            # Log error if rate not found
            self.logger.error(f"Failed to find conversion rate for {to_currency} in the API response.")
            return f"{min_budget}-{max_budget} {from_currency}"  # Fallback to original values

        except Exception as e:
            self.logger.error(f"Currency conversion error: {str(e)}", exc_info=True)
            return f"{min_budget}-{max_budget} {from_currency}"  # Fallback in case of error
