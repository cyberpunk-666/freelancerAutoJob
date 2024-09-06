import logging
from datetime import datetime
from app.db.postgresdb import PostgresDB

class SchemaVersionsManager:
    def __init__(self, db: PostgresDB):
        """
        Initialize the SchemaVersionsManager class with a PostgresDB instance.
        :param db: An instance of the PostgresDB class for database operations.
        """
        self.logger = logging.getLogger(__name__)
        self.db = db

    def create_table(self):
        """Create the schema_versions table if it doesn't exist."""
        self.logger.info("Creating schema_versions table")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
        self.db.create_table(create_table_query)
        self.logger.info("schema_versions table created successfully")

    def add_version(self, version: str):
        """
        Add a new version to the schema_versions table.
        :param version: The version of the migration script (e.g., 001_create_users_table.sql).
        """
        data = {
            'version': version,
            'applied_at': datetime.now()
        }
        self.db.add_object('schema_versions', data)
        self.logger.info(f"Version '{version}' added to schema_versions")

    def get_applied_versions(self) -> list:
        """
        Fetch all applied versions from the schema_versions table.
        :return: A list of applied version strings.
        """
        query = "SELECT version FROM schema_versions"
        self.logger.info("Fetching applied schema versions")
        results = self.db.fetch_all(query)
        applied_versions = [result[0] for result in results]
        return applied_versions

    def version_exists(self, version: str) -> bool:
        """
        Check if a specific version exists in the schema_versions table.
        :param version: The version string to check.
        :return: True if the version exists, False otherwise.
        """
        query = "SELECT version FROM schema_versions WHERE version = %s"
        self.logger.info(f"Checking if version '{version}' exists in schema_versions")
        result = self.db.fetch_one(query, (version,))
        return result is not None

    def delete_version(self, version: str):
        """
        Delete a specific version from the schema_versions table.
        :param version: The version string to delete.
        """
        self.logger.info(f"Deleting version '{version}' from schema_versions")
        self.db.delete_object('schema_versions', {'version': version})
        self.logger.info(f"Version '{version}' deleted successfully")
