import json
from datetime import datetime
from app.db.postgresdb import PostgresDB
import logging

class ProcessedEmailManager:
    def __init__(self, db: PostgresDB, user_id):
        """
        Initialize the ProcessedEmails class with a PostgresDB instance.
        :param db: An instance of the PostgresDB class for database operations.
        """
        self.db = db
        self.user_id = user_id

    def mark_email_as_processed(self, message_id, user_id, email_date=None):
        """
        Mark an email as processed by inserting it into the processed_emails table.
        :param message_id: The unique ID of the email.
        :param user_id: The ID of the user who processed the email.
        :param email_date: The date the email was received (optional).
        """
        data = {
            'message_id': message_id,
            'user_id': user_id,
            'email_date': email_date or datetime.now()
        }
        self.db.add_object('processed_emails', data)
        logging.info(f"Marked email as processed: {message_id} for user: {user_id}")

    def is_email_processed(self, message_id, user_id):
        """
        Check if an email has already been processed by a specific user.
        :param message_id: The unique ID of the email.
        :param user_id: The ID of the user.
        :return: True if the email is processed for the given user, False otherwise.
        """
        result = self.db.fetch_one("SELECT message_id FROM processed_emails WHERE message_id = %s AND user_id = %s", (message_id, user_id))
        return result is not None

    def delete_processed_email(self, message_id, user_id):
        """
        Delete a processed email entry for a specific user from the processed_emails table.
        :param message_id: The unique ID of the email.
        :param user_id: The ID of the user.
        """
        self.db.delete_object('processed_emails', {'message_id': message_id, 'user_id': user_id})

    def load_all_processed_emails(self, user_id):
        """
        Load all processed emails for a specific user from the processed_emails table.
        :param user_id: The ID of the user.
        :return: A list of all processed email message IDs for the user.
        """
        query = "SELECT message_id FROM processed_emails WHERE user_id = %s"
        results = self.db.fetch_all(query, (user_id,))
        return [result[0] for result in results]

    def create_table(self):
        """Create the processed_emails table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id VARCHAR(255) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            email_date TIMESTAMP
        );
        """
        self.db.create_table(create_table_query)
