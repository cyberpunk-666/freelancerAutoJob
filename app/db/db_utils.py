from app.db.postgresdb import PostgresDB
from app.models.api_response import APIResponse
from app.models.config import Config

current_db = None

def get_db():
    global current_db
    if not current_db:
        current_db = PostgresDB(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD)

    return current_db

def close_db(e=None):
    global current_db 
    if current_db is not None:
        current_db.close()
        current_db = None
        
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