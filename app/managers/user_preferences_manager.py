import json
import logging
from app.db.db_utils import get_db
from app.db.postgresdb import PostgresDB
from app.models.api_response import APIResponse


class UserPreferencesManager:
    def __init__(self) -> None:
        self.db:PostgresDB = get_db()
        self.logger = logging.getLogger(__name__)
    

    def create_table(self) -> APIResponse:
        """Create the user_preferences table if it doesn't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    preference_id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    key VARCHAR(255) NOT NULL,
                    value JSONB NOT NULL,
                    category VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)
            self.logger.info("User preferences table created successfully")
            return APIResponse(status="success", message="User preferences table created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create user preferences table: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to create user preferences table: {str(e)}")

    def get_preferences(self, user_id: int) -> APIResponse:
        self.logger.info(f"Retrieving preferences for user with ID {user_id}")
        try:
            query = "SELECT key, value FROM user_preferences WHERE user_id = %s"
            preferences = self.db.fetch_all(query, (user_id,))
            preferences_dict = {row[0]: row[1] for row in preferences}
            self.logger.info(f"Preferences retrieved for user with ID {user_id}: {', '.join([f'{key}={value}' for key, value in preferences_dict.items()])}")
            return APIResponse(status="success", message="Preferences retrieved successfully", data=preferences_dict)
        except Exception as e:
            self.logger.error(f"Failed to retrieve preferences for user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve preferences for user {user_id}: {str(e)}")

    def get_preference(self, user_id: int, key: str) -> APIResponse:
        self.logger.info(f"Retrieving preference for user {user_id}: {key}")
        try:
            query = "SELECT value FROM user_preferences WHERE user_id = %s AND key = %s"
            preference = self.db.fetch_one(query, (user_id, key))
            if preference:
                self.logger.info(f"Preference retrieved for user {user_id}: {key} = {preference[0]}")
                return APIResponse(status="success", message="Preference retrieved successfully", data=preference[0])
            else:
                self.logger.info(f"No preference found for user {user_id}: {key}")
                return APIResponse(status="success", message="No preference found", data=None)
        except Exception as e:
            self.logger.error(f"Failed to retrieve preference for user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve preference for user {user_id}: {str(e)}")

    def set_preference(self, user_id: int, key: str, value: str) -> APIResponse:
        self.logger.info(f"Setting preference for user {user_id}: {key} = {value}")
        try:
            # Attempt to convert the value to JSON
            json_value = json.dumps(value)  # Convert to JSON string
            query = """
                INSERT INTO user_preferences (user_id, key, value)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (user_id, key) DO UPDATE SET value = EXCLUDED.value
            """
            self.db.execute_query(query, (user_id, key, json_value))
            self.logger.info(f"Preference set successfully for user {user_id}: {key} = {json_value}")
            return APIResponse(status="success", message="Preference set successfully")
        except json.JSONDecodeError as jde:
            self.logger.error(f"Invalid JSON format for value: {value}", exc_info=True)
            return APIResponse(status="failure", message=f"Invalid JSON format for value: {str(jde)}")
        except Exception as e:
            self.logger.error(f"Failed to set user preference for user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to set user preference: {str(e)}")

    def delete_preference(self, user_id: int, key: str) -> APIResponse:
        self.logger.info(f"Deleting preference for user {user_id}: {key}")
        try:
            query = "DELETE FROM user_preferences WHERE user_id = %s AND key = %s"
            self.db.execute_query(query, (user_id, key))
            self.logger.info(f"Preference deleted successfully for user {user_id}: {key}")
            return APIResponse(status="success", message="Preference deleted successfully")
        except Exception as e:
            self.logger.error(f"Failed to delete user preference for user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to delete user preference: {str(e)}")

    def rename_preference_for_all(self, old_key: str, new_key: str) -> APIResponse:
        self.logger.info(f"Renaming preference key {old_key} to {new_key} for all users")
        try:
            query = "UPDATE user_preferences SET key = %s WHERE key = %s"
            self.db.execute_query(query, (new_key, old_key))
            self.logger.info(f"Preference key renamed successfully from {old_key} to {new_key}")
            return APIResponse(status="success", message="Preference key renamed successfully")
        except Exception as e:
            self.logger.error(f"Failed to rename preference key from {old_key} to {new_key}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to rename preference key: {str(e)}")

    def get_preference_type(self, user_id: int, key: str) -> APIResponse:
        self.logger.info(f"Getting data type for preference key {key} for user {user_id}")
        try:
            query = "SELECT jsonb_typeof(value) FROM user_preferences WHERE user_id = %s AND key = %s"
            data_type = self.db.fetch_one(query, (user_id, key))
            if data_type:
                self.logger.info(f"Data type for {key} retrieved: {data_type[0]}")
                return APIResponse(status="success", message="Data type retrieved successfully", data=data_type[0])
            else:
                return APIResponse(status="failure", message="Preference not found")
        except Exception as e:
            self.logger.error(f"Failed to retrieve data type for preference key {key}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve data type: {str(e)}")
