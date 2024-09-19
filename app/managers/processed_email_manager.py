import json
from datetime import datetime
from app.db.postgresdb import PostgresDB
import logging
from app.models.api_response import APIResponse

class ProcessedEmailManager:
    def __init__(self, db: PostgresDB, user_id):
        """
        Initialize the ProcessedEmails class with a PostgresDB instance.
        :param db: An instance of the PostgresDB class for database operations.
        """
        self.db = db
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)

    def mark_email_as_processed(self, message_id, user_id, email_date=None) -> APIResponse:
        """
        Mark an email as processed by inserting it into the processed_emails table.
        :param message_id: The unique ID of the email.
        :param user_id: The ID of the user who processed the email.
        :param email_date: The date the email was received (optional).
        """
        try:
            data = {
                'message_id': message_id,
                'user_id': user_id,
                'email_date': email_date or datetime.now()
            }
            self.db.add_object('processed_emails', data)
            self.logger.info(f"Marked email as processed: {message_id} for user: {user_id}")
            return APIResponse(status="success", message="Email marked as processed successfully")
        except Exception as e:
            self.logger.error(f"Failed to mark email as processed: {message_id} for user: {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to mark email as processed")

    def is_email_processed(self, message_id, user_id) -> APIResponse:
        """
        Check if an email has already been processed by a specific user.
        :param message_id: The unique ID of the email.
        :param user_id: The ID of the user.
        :return: True if the email is processed for the given user, False otherwise.
        """
        try:
            result = self.db.fetch_one("SELECT message_id FROM processed_emails WHERE message_id = %s AND user_id = %s", (message_id, user_id))
            is_processed = result is not None
            self.logger.info(f"Email {message_id} {'is' if is_processed else 'is not'} processed for user: {user_id}")
            return APIResponse(status="success", message="Email processed check successful", data={"is_processed": is_processed})
        except Exception as e:
            self.logger.error(f"Failed to check if email {message_id} is processed for user: {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to check if email is processed")

    def delete_processed_email(self, message_id, user_id) -> APIResponse:
        """
        Delete a processed email entry for a specific user from the processed_emails table.
        :param message_id: The unique ID of the email.
        :param user_id: The ID of the user.
        """
        try:
            self.db.delete_object('processed_emails', {'message_id': message_id, 'user_id': user_id})
            self.logger.info(f"Deleted processed email: {message_id} for user: {user_id}")
            return APIResponse(status="success", message="Processed email deleted successfully")
        except Exception as e:
            self.logger.error(f"Failed to delete processed email: {message_id} for user: {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to delete processed email")

    def load_all_processed_emails(self, user_id) -> APIResponse:
        """
        Load all processed emails for a specific user from the processed_emails table.
        :param user_id: The ID of the user.
        :return: A list of all processed email message IDs for the user.
        """
        try:
            query = "SELECT message_id FROM processed_emails WHERE user_id = %s"
            results = self.db.fetch_all(query, (user_id,))
            processed_emails = [result[0] for result in results]
            self.logger.info(f"Loaded {len(processed_emails)} processed emails for user: {user_id}")
            return APIResponse(status="success", message="Processed emails loaded successfully", data=processed_emails)
        except Exception as e:
            self.logger.error(f"Failed to load processed emails for user: {user_id}", exc_info=True)
            return APIResponse(status="failure", message="Failed to load processed emails")

    def create_table(self) -> APIResponse:
        """Create the processed_emails table if it doesn't exist."""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS processed_emails (
                message_id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                email_date TIMESTAMP
            );
            """
            self.db.create_table(create_table_query)
            self.logger.info("Created processed_emails table successfully")
            return APIResponse(status="success", message="Processed emails table created successfully")
        except Exception as e:
            self.logger.error("Failed to create processed_emails table", exc_info=True)
            return APIResponse(status="failure", message="Failed to create processed emails table")
