import json
import psycopg2
import logging
import os
class PostgresDB:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.logger.info("PostgresDB instance initialized")
        self.init_database()
        self.connect()

    def init_database(self):
        """Check if the database exists, and create it if it does not."""
        try:
            self.logger.info(f"Checking if database '{self.database}' exists")
            # Connect to the PostgreSQL server (without specifying a database)
            conn = psycopg2.connect(
                host=self.host,
                database='postgres',  # Connect to the default 'postgres' database
                user=self.user,
                password=self.password
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Check if the database exists
                cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (self.database,))
                exists = cursor.fetchone()
                if not exists:
                    # Create the database if it does not exist
                    self.logger.info(f"Creating database '{self.database}'")
                    cursor.execute(f'CREATE DATABASE "{self.database}"')
                    self.logger.info(f"Database '{self.database}' created successfully.")
                else:
                    self.logger.info(f"Database '{self.database}' already exists.")
            conn.close()
        except Exception as e:
            self.logger.error(f"Error checking or creating the database: {e}")
            raise

    def connect(self):
        """Establish a connection to the PostgreSQL database."""
        try:
            self.logger.info(f"Connecting to database '{self.database}'")
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.set_session(autocommit=True)
            self.logger.info("Database connection established successfully.")
        except Exception as e:
            self.logger.error(f"Error connecting to the database: {e}")
            raise

    def execute_query(self, query, params=None):
        """Execute a query with optional parameters."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                # Si la requête contient un INSERT, utiliser RETURNING pour obtenir l'ID
                if "RETURNING" in query:
                    last_id = cursor.fetchone()[0]
                    self.connection.commit()
                    self.logger.debug(f"Query executed successfully")
                    return last_id
                self.connection.commit()
                self.logger.debug(f"Query executed successfully")
        except Exception as e:
            self.logger.error(f"Error executing query: {e}\n Query: {query}")
            self.connection.rollback()
            raise


    def fetch_one_with_column_names(self, query, params=None):
        try:
            with self.connection.cursor() as cur:
                cur.execute(query, params)
                
                # Get the column names
                column_names = [desc[0] for desc in cur.description]
                
                # Fetch the row
                row = cur.fetchone()
                
                if row:
                    # Combine column names with values
                    result = dict(zip(column_names, row))
                    return result
                else:
                    return None
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def fetch_one(self, query, params=None):
        """Fetch a single result from a query."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                self.logger.debug(f"Query executed successfully")
                return result
        except Exception as e:
            self.logger.error(f"Error fetching data: {e}\n Query: {query}")
            raise

    def fetch_all(self, query, params=None):
        try:
            with self.connection.cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching data: {e}\nQuery: {query}")
            self.connection.rollback()  # Roll back the transaction
            raise  # Re-raise the exception after rolling back


    def create_table(self, create_table_sql):
        """Create a table using the provided SQL statement."""
        try:
            self.execute_query(create_table_sql)
            self.logger.info("Table creation query executed successfully.")
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            raise

    def add_object(self, table, data):
        """
        Add a new object (row) to the specified table.
        :param table: Name of the table.
        :param data: Dictionary where keys are column names and values are the corresponding values.
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute_query(query, values)
        self.logger.info(f"Inserted object into {table}: {data}")

    def update_object(self, table, data, condition):
        """
        Update an existing object (row) in the specified table.
        :param table: Name of the table.
        :param data: Dictionary where keys are column names to update and values are the new values.
        :param condition: Dictionary where keys are column names to match and values are the values to match.
        """
        set_clause = []
        values = []
        
        for k, v in data.items():
            if isinstance(v, dict):
                # Convert dict to JSON string
                set_clause.append(f"{k} = %s::jsonb")
                values.append(json.dumps(v))
            else:
                set_clause.append(f"{k} = %s")
                values.append(v)
        
        set_clause = ', '.join(set_clause)
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        values.extend(condition.values())
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        self.execute_query(query, tuple(values))
        self.logger.info(f"Updated object in {table} where {condition}: {data}")

    def delete_object(self, table, condition):
        """
        Delete an object (row) from the specified table.
        :param table: Name of the table.
        :param condition: Dictionary where keys are column names to match and values are the values to match.
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        values = tuple(condition.values())
        
        query = f"DELETE FROM {table} WHERE {where_clause}"
        self.execute_query(query, values)
        self.logger.info(f"Deleted object from {table} where {condition}")

    def get_object(self, table, condition):
        """
        Get an object (row) from the specified table.
        :param table: Name of the table.
        :param condition: Dictionary where keys are column names to match and values are the values to match.
        :return: The object (row) matching the condition, or None if not found.
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        values = tuple(condition.values())

        query = f"SELECT * FROM {table} WHERE {where_clause}"
        result = self.fetch_one_with_column_names(query, values)
        if result:
            self.logger.info(f"Found object in {table} where {condition}: {result}")
            return result
        else:
            self.logger.info(f"No object found in {table} where {condition}")
            return None


    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed.")

# # Example usage
# if __name__ == "__main__":
#     # Configure logging
#     logging.basicConfig(level=logging.DEBUG)

#     # Database configuration
#     db_config = {
#         "host": os.getenv("DB_HOST", "localhost"),
#         "database": os.getenv("DB_NAME", "test"),
#         "user": os.getenv("DB_USER", "postgres"),
#         "password": os.getenv("DB_PASSWORD")
#     }

#     # Initialize the database
#     db = PostgresDB(**db_config)

#     # Example table creation SQL
#     create_table_query = """
#     CREATE TABLE IF NOT EXISTS job_details (
#         job_id VARCHAR(32) PRIMARY KEY, -- MD5 hash of job_title
#         job_title TEXT NOT NULL,
#         job_description TEXT,
#         budget VARCHAR(50),
#         email_date TIMESTAMP, -- When the job was received via email
#         gemini_results JSONB, -- JSON array/object of all Gemini results
#         status VARCHAR(50),
#         performance_metrics JSONB
#     );
#     """

#     # Create the table
#     db.create_table(create_table_query)

#     # Add a new object (row) to the job_details table
#     db.add_object('job_details', {
#         'job_id': 'abc123',
#         'job_title': 'Example Job',
#         'job_description': 'This is an example job description.',
#         'budget': '1000',
#         'email_date': '2024-08-28 12:34:56',
#         'gemini_results': '{}',
#         'status': 'processed',
#         'performance_metrics': '{}'
#     })

#     # Update an existing object in the job_details table
#     db.update_object('job_details', 
#         {'status': 'completed'}, 
#         {'job_id': 'abc123'}
#     )

#     # Delete an object from the job_details table
#     db.delete_object('job_details', 
#         {'job_id': 'abc123'}
#     )

#     # Close the database connection
#     db.close()
