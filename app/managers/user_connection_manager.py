import logging
import asyncio
from app.models.api_response import APIResponse

class UserConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.heartbeats = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def add_connection(self, user_id, connection) -> APIResponse:
        """
        Adds a connection and starts heartbeat management.
        """
        try:
            self.active_connections[user_id] = connection
            self.heartbeats[user_id] = asyncio.create_task(self.heartbeat(user_id))
            self.logger.info(f"User {user_id} connected.")
            return APIResponse(status="success", message=f"User {user_id} connected successfully.")
        except Exception as e:
            self.logger.error(f"Error adding connection for {user_id}: {e}")
            return APIResponse(status="failure", message=f"Failed to connect user {user_id}.")

    async def remove_connection(self, user_id) -> APIResponse:
        """
        Removes the user's connection and stops heartbeat tracking.
        """
        try:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            if user_id in self.heartbeats:
                self.heartbeats[user_id].cancel()
                del self.heartbeats[user_id]
            self.logger.info(f"User {user_id} disconnected.")
            return APIResponse(status="success", message=f"User {user_id} disconnected successfully.")
        except Exception as e:
            self.logger.error(f"Error removing connection for {user_id}: {e}")
            return APIResponse(status="failure", message=f"Failed to disconnect user {user_id}.")

    async def is_connected(self, user_id) -> APIResponse:
        """
        Checks if a user is currently connected.
        """
        connected = user_id in self.active_connections
        message = f"User {user_id} is {'connected' if connected else 'not connected'}."
        self.logger.info(message)
        return APIResponse(status="success", message=message, data={"connected": connected})

    async def heartbeat(self, user_id):
        """
        Heartbeat mechanism to ensure user remains connected.
        """
        while user_id in self.active_connections:
            try:
                connection = self.active_connections[user_id]
                await connection.ping()  # Assume the connection has a ping method
                self.logger.debug(f"Heartbeat sent to user {user_id}.")
                await asyncio.sleep(10)  # Heartbeat interval
            except Exception as e:
                self.logger.error(f"Heartbeat failed for user {user_id}: {e}")
                await self.remove_connection(user_id)
                break
