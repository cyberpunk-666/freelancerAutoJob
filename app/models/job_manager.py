import json
import hashlib
from datetime import datetime, timezone
import logging
from app.db.postgresdb import PostgresDB

class JobManager:
    def __init__(self, db: PostgresDB, user_id: int):
        """
        Initialize the JobManager class with a PostgresDB instance.
        :param db: An instance of the PostgresDB class for database operations.
        :param user_id: The ID of the authenticated user.
        """
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.user_id = user_id

    def generate_job_id(self, job_title: str) -> str:
        """Generate a unique job ID using the SHA-256 hash of the job title."""
        return hashlib.sha256(job_title.encode('utf-8')).hexdigest()

    def create_job(self, job_title: str, job_description: str, budget: str, status: str, 
                   email_date: datetime = None, gemini_results=None, performance_metrics=None) -> str:
        """
        Create a new job entry in the job_details table.
        :param job_title: The title of the job.
        :param job_description: The description of the job.
        :param budget: The budget for the job.
        :param status: The status of the job (e.g., open, closed).
        :param email_date: The date the job was received via email (optional).
        :param gemini_results: JSON data with Gemini results (optional).
        :param performance_metrics: JSON data with performance metrics (optional).
        :return: The job_id of the created job.
        """
        self.logger.info(f"Creating new job: {job_title}")
        job_id = self.generate_job_id(job_title)
        data = {
            'job_id': job_id,
            'job_title': job_title,
            'job_description': job_description,
            'budget': budget,
            'email_date': email_date or datetime.now(tz=timezone.utc),
            'gemini_results': json.dumps(gemini_results or {}),
            'status': status,
            'performance_metrics': json.dumps(performance_metrics or {})
        }
        self.db.add_object('job_details', data)
        self.logger.info(f"Job created successfully with ID: {job_id}")
        return job_id

    def read_job(self, job_id: str) -> dict:
        """Read a job entry from the job_details table."""
        query = "SELECT * FROM job_details WHERE job_id = %s AND user_id = %s"
        self.logger.info(f"Fetching job with ID: {job_id}")
        result = self.db.fetch_one(query, (job_id, self.user_id))
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
                'occurrence_count': result[9],
                'user_id': result[10]
            }
            self.logger.info(f"Job found: {job_id}")
            return job_details
        self.logger.warning(f"Job not found: {job_id}")
        return None

    def update_job(self, job_id: str, data: dict):
        """
        Update a job entry in the job_details table.
        :param job_id: The unique ID of the job.
        :param data: A dictionary containing the columns to update and their new values.
        """
        self.logger.info(f"Updating job: {job_id}")
        data['user_id'] = self.user_id
        rows_affected = self.db.update_object('job_details', data, {'job_id': job_id, 'user_id': self.user_id})
        if rows_affected > 0:
            self.logger.info(f"Job updated successfully: {job_id}")
        else:
            self.logger.warning(f"Job update failed: {job_id}")

    def delete_job(self, job_id: str):
        """
        Delete a job entry from the job_details table.
        :param job_id: The unique ID of the job.
        """
        self.logger.info(f"Deleting job: {job_id}")
        rows_affected = self.db.delete_object('job_details', {'job_id': job_id, 'user_id': self.user_id})
        if rows_affected > 0:
            self.logger.info(f"Job deleted successfully: {job_id}")
        else:
            self.logger.warning(f"Job deletion failed: {job_id}")

    def job_exists(self, job_title: str) -> bool:
        """
        Check if a job exists in the job_details table based on the job title.
        :param job_title: The title of the job.
        :return: True if the job exists, False otherwise.
        """
        job_id = self.generate_job_id(job_title)
        self.logger.info(f"Checking if job exists: {job_title}")
        result = self.db.fetch_one("SELECT job_id FROM job_details WHERE job_id = %s", (job_id,))
        return result is not None
    
    def fetch_all_jobs(self) -> list:
        """
        Fetch all job entries from the job_details table for the authenticated user.
        :return: A list of dictionaries, each containing a job's details.
        """
        query = "SELECT * FROM job_details WHERE user_id = %s"
        self.logger.info("Fetching all jobs")
        results = self.db.fetch_all(query, (self.user_id,))
        jobs = []
        for result in results:
            job = {
                'job_id': result[0],
                'job_title': result[1],
                'job_description': result[2],
                'budget': result[3],
                'email_date': result[4],
                'gemini_results': result[5],
                'status': result[6],
                'performance_metrics': result[7],
                'last_occurrence': result[8],
                'occurrence_count': result[9],
                'user_id': result[10]
            }
            jobs.append(job)
        return jobs

    def create_table(self):
        """Create the job_details table if it doesn't exist."""
        self.logger.info("Creating job_details table")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS job_details (
            job_id VARCHAR(64) PRIMARY KEY,
            job_title TEXT NOT NULL,
            job_description TEXT,
            budget VARCHAR(50),
            email_date TIMESTAMP,
            gemini_results JSONB,
            status VARCHAR(50),
            performance_metrics JSONB,
            last_occurrence TIMESTAMP,
            occurrence_count INTEGER DEFAULT 1,
            user_id INTEGER NOT NULL             
        );
        """
        self.db.create_table(create_table_query)
        self.logger.info("job_details table created successfully")
