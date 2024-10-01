import json
import logging

from flask import current_app
from app.db.db_utils import get_db
from app.db.postgresdb import PostgresDB
from app.models.api_response import APIResponse


class UserPreferencesManager:
    def __init__(self, config_file_path = None) -> None:
        self.config_file_path = config_file_path
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
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE (user_id, key)
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

    def get_preference_by_id(self, user_id: int, key: str) -> APIResponse:
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

    def get_preference_by_name(self, user_id: int, name: str) -> APIResponse:
        self.logger.info(f"Retrieving preference for user {user_id} with name {name}")
        try:
            query = "SELECT value FROM user_preferences WHERE user_id = %s AND name = %s"
            preference = self.db.fetch_one(query, (user_id, name))
            if preference:
                self.logger.info(f"Preference retrieved for user {user_id} with name {name}: {preference[0]}")
                return APIResponse(status="success", message="Preference retrieved successfully", data=preference[0])
            else:
                self.logger.info(f"No preference found for user {user_id} with name {name}")
                return APIResponse(status="success", message="No preference found", data=None)
        except Exception as e:
            self.logger.error(f"Failed to retrieve preference for user {user_id} with name {name}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve preference for user {user_id} with name {name}: {str(e)}")

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

    def get_preference_value(self, user_id: int, key: str) -> APIResponse:
        self.logger.info(f"Getting value for preference key {key} for user {user_id}")
        try:
            query = "SELECT value FROM user_preferences WHERE user_id = %s AND key = %s"
            value = self.db.fetch_one(query, (user_id, key))
            if value:
                self.logger.info(f"Value for {key} retrieved: {value[0]}")
                return APIResponse(status="success", message="Value retrieved successfully", data=value[0])
            else:
                default_value = self.get_default_value(key)
                if default_value:
                    return APIResponse(status="success", message="Default value retrieved successfully", data=default_value)
                else:
                    return APIResponse(status="success", message="No value found and no default value available")
        except Exception as e:
            self.logger.error(f"Failed to retrieve value for preference key {key}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve value: {str(e)}")

    def get_default_value(self, key: str) -> APIResponse:
        self.logger.info(f"Getting default value for preference key {key}")
        preferences_fields = self.get_preferences_fields()
        for pref in preferences_fields:
            if pref['key'] == key:
                default_value = pref.get('default')
                if default_value is not None:
                    self.logger.info(f"Default value for {key} retrieved: {default_value}")
                    return APIResponse(status="success", message="Default value retrieved successfully", data=default_value)
                else:
                    return APIResponse(status="failure", message="Default value not found")
        return APIResponse(status="failure", message="Preference key not found")

    def get_preferences_categories(self):
        # Load and process the JSON configuration

        with open(self.config_file_path, 'r') as config_file:
            preferences_config = json.load(config_file)
        # Organize preferences by category
        preferences_by_category = {}
        for pref in preferences_config['preferences']:
            category = pref.get('category', 'General')
            if category not in preferences_by_category:
                preferences_by_category[category] = []
            preferences_by_category[category].append(pref)
            
        return preferences_by_category

    def get_preferences_fields(self):
        preferences_fields = self.get_preferences_categories()
        preferences_fields_list = []
        for category, prefs in preferences_fields.items():
            for pref in prefs:
                preferences_fields_list.append(pref)
        return preferences_fields_list

    @staticmethod
    def get_api_response_value(response: APIResponse, property_name: str):
        """
        Helper function to handle APIResponses and return the value of a specific property.

        Args:
            response (APIResponse): The APIResponse object to process.
            property_name (str): The name of the property to retrieve from the response data.

        Returns:
            Optional[Any]: The value of the specified property if it exists, None otherwise.
        """
        if response.status == "success" and response.data is not None:
            if property_name == "value":
                # Handle the case where the entire data is the value we're looking for
                return response.data            
            elif isinstance(response.data, dict):
                return response.data.get(property_name)

        return None
    
    def get_preferences_values(self, user_id: int) -> APIResponse:
        preferences = self.get_preferences_fields()
        if preferences:
            preferences_values = {}
            for preference in preferences:
                value_pre_answer = self.get_preference_value(user_id, preference["key"])
                value_answer = UserPreferencesManager.get_api_response_value(value_pre_answer, "value")
                if value_answer and hasattr(value_answer, "status"):
                    value = UserPreferencesManager.get_api_response_value(value_answer, "value")
                    preferences_values[preference["key"]] = value
                else:
                    preferences_values[preference["key"]] = value_answer
            return APIResponse(status="success", message="Preferences values retrieved successfully", data=preferences_values)
        else:
            return APIResponse(status="failure", message="Failed to retrieve preferences values")