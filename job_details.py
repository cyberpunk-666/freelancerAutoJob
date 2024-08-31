import json
import hashlib
from datetime import datetime
from postgres_db import PostgresDB

class JobDetails:
    def __init__(self, db):
        """
        Initialize the JobDetails class with a PostgresDB instance.
        :param db: An instance of the PostgresDB class for database operations.
        """
        self.db = db

    def generate_job_id(self, job_title):
        """Generate a unique job ID using the MD5 hash of the job title."""
        return hashlib.md5(job_title.encode('utf-8')).hexdigest()

    def create_job(self, job_title, job_description, budget, email_date, gemini_results, status, performance_metrics):
        """
        Create a new job entry in the job_details table.
        :param job_title: The title of the job.
        :param job_description: The description of the job.
        :param budget: The budget for the job.
        :param email_date: The date the job was received via email.
        :param gemini_results: JSON data with Gemini results.
        :param status: The status of the job (e.g., processed, pending).
        :param performance_metrics: JSON data with performance metrics.
        """
        job_id = self.generate_job_id(job_title)
        data = {
            'job_id': job_id,
            'job_title': job_title,
            'job_description': job_description,
            'budget': budget,
            'email_date': email_date,
            'gemini_results': json.dumps(gemini_results),
            'status': status,
            'performance_metrics': json.dumps(performance_metrics)
        }
        self.db.add_object('job_details', data)
        return job_id

    def read_job(self, job_id):
        """Read a job entry from the job_details table."""
        query = "SELECT * FROM job_details WHERE job_id = %s"
        result = self.db.fetch_one(query, (job_id,))
        if result:
            job_details = {
                'job_id': result[0],
                'job_title': result[1],
                'job_description': result[2],
                'budget': result[3],
                'email_date': result[4],
                'gemini_results': result[5],
                'status': result[6],
                'performance_metrics': result[7],
                'last_occurrence': result[8],
                'occurrence_count': result[9]
            }
            return job_details
        return None

    def update_job(self, job_id, data):
        """
        Update a job entry in the job_details table.
        :param job_id: The unique ID of the job.
        :param data: A dictionary containing the columns to update and their new values.
        """
        self.db.update_object('job_details', data, {'job_id': job_id})

    def delete_job(self, job_id):
        """
        Delete a job entry from the job_details table.
        :param job_id: The unique ID of the job.
        """
        self.db.delete_object('job_details', {'job_id': job_id})

    def job_exists(self, job_title):
        """
        Check if a job exists in the job_details table based on the job title.
        :param job_title: The title of the job.
        :return: True if the job exists, False otherwise.
        """
        job_id = self.generate_job_id(job_title)
        result = self.db.fetch_one("SELECT job_id FROM job_details WHERE job_id = %s", (job_id,))
        return result is not None
    
    def create_table(self):
        """Create the job_details table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS job_details (
            job_id VARCHAR(32) PRIMARY KEY,
            job_title TEXT NOT NULL,
            job_description TEXT,
            budget VARCHAR(50),
            email_date TIMESTAMP,
            gemini_results JSONB,
            status VARCHAR(50),
            performance_metrics JSONB,
            last_occurrence TIMESTAMP,
            occurrence_count INTEGER DEFAULT 1             
        );
        """
        self.db.create_table(create_table_query)

# # Example usage
# if __name__ == "__main__":
#     # Configure logging
#     import logging
#     logging.basicConfig(level=logging.DEBUG)

#     # Database configuration
#     db_config = {
#         "host": "localhost",
#         "database": "test",
#         "user": "postgres",
#         "password": "tdk2hdD!"
#     }

#     # Initialize the PostgresDB instance
#     db = PostgresDB(**db_config)

#     # Initialize the JobDetails instance
#     job_details = JobDetails(db)

#     # Example: Create a job
#     job_id = job_details.create_job(
#         job_title="Example Job",
#         job_description="This is an example job description.",
#         budget="1000",
#         email_date=datetime.now(),
#         gemini_results={
#     "analyze_job_fit": {
#         "fit": True,
#         "reasons": "The job requirements closely match the freelancer's skill set in Python and AI development.",
#         "confidence_score": 0.92,
#         "response_time": "2024-08-28T12:00:00Z"
#     },
#     "analyse_job_and_time": {
#         "estimated_time": "15 hours",
#         "assumptions": "Assuming standard Python libraries and no unexpected issues during development.",
#         "confidence_score": 0.85,
#         "response_time": "2024-08-28T12:01:00Z"
#     },
#     "generate_application_letter": {
#         "application_letter": "Dear Client, I am writing to express my interest in your job posting for a Python and AI developer...",
#         "confidence_score": 0.88,
#         "response_time": "2024-08-28T12:02:00Z"
#     },
#     "additional_analysis": {
#         "budget_suitability": {
#             "within_budget": True,
#             "reason": "The client's budget range matches the freelancer's expected rate.",
#             "confidence_score": 0.90
#         },
#         "technical_feasibility": {
#             "feasible": True,
#             "potential_risks": "Potential risk in integrating with legacy systems.",
#             "confidence_score": 0.80
#         },
#         "response_time": "2024-08-28T12:03:00Z"
#     }
# }
# ,
#         status="processed",
#         performance_metrics=None
#     )
#     print(f"Job created with job_id: {job_id}")

#     # Example: Read a job
#     job = job_details.read_job(job_id)
#     print(f"Job details: {job}")

#     # Example: Update a job
#     job_details.update_job(job_id, {'status': 'completed'})
#     print(f"Job updated with status 'completed'.")

#     # Example: Check if a job exists
#     exists = job_details.job_exists("Example Job")
#     print(f"Job exists: {exists}")

#     # Example: Delete a job
#     job_details.delete_job(job_id)
#     print(f"Job deleted.")

#     # Close the database connection
#     db.close()
