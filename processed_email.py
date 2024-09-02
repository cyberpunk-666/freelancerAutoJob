import json
from datetime import datetime
from app.db.postgresdb import PostgresDB
import logging

class ProcessedEmails:
    def __init__(self, db):
        """
        Initialize the ProcessedEmails class with a PostgresDB instance.
        :param db: An instance of the PostgresDB class for database operations.
        """
        self.db = db

    def mark_email_as_processed(self, message_id, email_date=None):
        """
        Mark an email as processed by inserting it into the processed_emails table.
        :param message_id: The unique ID of the email.
        :param email_date: The date the email was received (optional).
        """
        data = {
            'message_id': message_id,
            'email_date': email_date or datetime.now()
        }
        self.db.add_object('processed_emails', data)
        logging.info(f"Marked email as processed: {message_id}")

    def is_email_processed(self, message_id):
        """
        Check if an email has already been processed.
        :param message_id: The unique ID of the email.
        :return: True if the email is processed, False otherwise.
        """
        result = self.db.fetch_one("SELECT message_id FROM processed_emails WHERE message_id = %s", (message_id,))
        return result is not None

    def delete_processed_email(self, message_id):
        """
        Delete a processed email entry from the processed_emails table.
        :param message_id: The unique ID of the email.
        """
        self.db.delete_object('processed_emails', {'message_id': message_id})

    def load_all_processed_emails(self):
        """
        Load all processed emails from the processed_emails table.
        :return: A list of all processed email message IDs.
        """
        query = "SELECT message_id FROM processed_emails"
        results = self.db.fetch_all(query)
        return [result[0] for result in results]

    def create_table(self):
        """Create the processed_emails table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id VARCHAR(255) PRIMARY KEY,
            email_date TIMESTAMP
        );
        """
        self.db.create_table(create_table_query)
