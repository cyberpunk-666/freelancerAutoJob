import logging
from datetime import datetime
from app.models.api_response import APIResponse
from app.db.db_utils import get_db
from enum import Enum, auto


job_status = [{
    "id": 1,
    "name": "Fetched",
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
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def create_table(self) -> APIResponse:
        """Create the jobs and job_applications tables if they don't exist."""
        try:
            # Initialize the database
            db = get_db()

            # Example table creation SQL
            create_table_query = """
            CREATE TABLE IF NOT EXISTS job_details (
                job_id VARCHAR(32) PRIMARY KEY, -- MD5 hash of job_title
                job_title TEXT NOT NULL,
                job_description TEXT,
                budget VARCHAR(50),
                email_date TIMESTAMP, -- When the job was received via email
                gemini_results JSONB, -- JSON array/object of all Gemini results
                status VARCHAR(50),
                performance_metrics JSONB,
                user_id INTEGER NOT NULL, -- User who posted the job
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status_id INTEGER NOT NULL, -- Status of the job
            );
            """

            # Create the table
            db.create_table(create_table_query)
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

    def post_job(self, job_data) -> APIResponse:
        """Post a new job."""
        try:
            self.db.add_object("jobs", job_data)
            self.logger.info(f"New job posted: {job_data['title']}")
            return APIResponse(status="success", message="Job posted successfully")
        except Exception as e:
            self.logger.error(f"Failed to post job: {job_data['title']}", exc_info=True)
            return APIResponse(status="failure", message="Failed to post job")

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
