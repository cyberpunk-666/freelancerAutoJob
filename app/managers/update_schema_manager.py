import os
import logging
from app.db.postgresdb import PostgresDB
from app.managers.schema_versions_manager import SchemaVersionsManager

class UpdateSchemaManager:
    def __init__(self, db: PostgresDB, migrations_folder: str = "db_migrations"):
        """
        Initialize the UpdateSchemaManager class with a PostgresDB instance and the folder for migration scripts.
        :param db: An instance of the PostgresDB class for database operations.
        :param migrations_folder: Path to the folder containing migration scripts.
        """
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.migrations_folder = migrations_folder
        self.schema_versions_manager = SchemaVersionsManager(db)
        
        # Ensure the schema_versions table exists
        self.schema_versions_manager.create_table()
        
        # ensure the directory exists, create it if it doesn't
        if not os.path.exists(self.migrations_folder):
            os.makedirs(self.migrations_folder)
            self.logger.info(f"Created directory: {self.migrations_folder}")

    def get_pending_migrations(self) -> list:
        """
        Get the list of migration scripts that haven't been applied yet.
        :return: List of pending migration script filenames.
        """
        applied_versions = self.schema_versions_manager.get_applied_versions()
        all_migrations = sorted(os.listdir(self.migrations_folder))
        
        # Filter out the migrations that have already been applied
        pending_migrations = [migration for migration in all_migrations if migration not in applied_versions]
        self.logger.info(f"Pending migrations: {pending_migrations}")
        return pending_migrations

    def apply_migration(self, migration_file: str):
        """
        Apply a single migration script.
        :param migration_file: The filename of the migration script to apply.
        """
        migration_path = os.path.join(self.migrations_folder, migration_file)
        
        try:
            with open(migration_path, 'r') as file:
                migration_sql = file.read()

            self.logger.info(f"Applying migration: {migration_file}")
            
            # Execute the SQL migration
            self.db.execute_query(migration_sql)
            
            # Mark the migration as applied in schema_versions table
            self.schema_versions_manager.add_version(migration_file)
            self.logger.info(f"Migration '{migration_file}' applied successfully.")
            
        except Exception as e:
            self.logger.error(f"Failed to apply migration '{migration_file}': {e}")
            raise

    def update_schema(self):
        """
        Apply all pending migration scripts in the correct order.
        """
        self.logger.info("Starting schema update process")

        # Fetch all pending migrations
        pending_migrations = self.get_pending_migrations()

        # Apply each pending migration in order
        for migration in pending_migrations:
            self.apply_migration(migration)

        self.logger.info("Schema update completed successfully.")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Database configuration
    db_config = {
        "host": "localhost",
        "database": "your_database",
        "user": "your_user",
        "password": "your_password"
    }

    # Folder containing the migration scripts
    migrations_folder = "db_migrations"

    # Initialize the database
    db = PostgresDB(**db_config)

    # Initialize and run the schema updater
    schema_updater = UpdateSchemaManager(db, migrations_folder)
    schema_updater.update_schema()

    # Close the database connection
    db.close()
