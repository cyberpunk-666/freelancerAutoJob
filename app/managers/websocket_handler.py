import logging
from app.managers.user_connection_manager import UserConnectionManager
from app.models.api_response import APIResponse
import websockets


class WebSocketHandler:
    def __init__(self, connection_manager: UserConnectionManager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    async def handle_websocket(self, websocket, user_id):
        """
        Manages WebSocket connections, processes messages, and interacts with connection manager.
        """
        response = await self.connection_manager.add_connection(user_id, websocket)
        self.logger.info(response.message)

        try:
            while await self.connection_manager.is_connected(user_id).data["connected"]:
                message = await websocket.recv()
                self.logger.info(f"Received message from {user_id}: {message}")
                response = self.process_message(user_id, message)
                await self.send_message(user_id, response)
        except websockets.ConnectionClosed:
            self.logger.warning(f"WebSocket connection closed for {user_id}")
        finally:
            response = await self.connection_manager.remove_connection(user_id)
            self.logger.info(response.message)

    def process_message(self, user_id, message) -> str:
        """
        Process the incoming WebSocket message.
        """
        self.logger.debug(f"Processing message from {user_id}: {message}")
        try:
            # Placeholder for actual message processing logic
            response = APIResponse(status="success", message="Message processed successfully", data={"message": message})
            return response.json()
        except Exception as e:
            self.logger.error(f"Error processing message from {user_id}: {e}")
            return APIResponse(status="failure", message="Message processing failed").json()

    async def send_message(self, user_id, message: str):
        """
        Send a WebSocket message to the user if they are connected.
        """
        connection_status = await self.connection_manager.is_connected(user_id)
        if connection_status.data["connected"]:
            websocket = self.connection_manager.active_connections[user_id]
            try:
                await websocket.send(message)
                self.logger.info(f"Message sent to {user_id}: {message}")
            except Exception as e:
                self.logger.error(f"Failed to send message to {user_id}: {e}")
        else:
            self.logger.warning(f"Cannot send message; user {user_id} is not connected.")

    async def notify_new_job(self, user_id, job_data):
        """
        Notify the user about a new job if they are connected.
        """
        message = APIResponse(status="success", message="New job available", data=job_data).json()
        await self.send_message(user_id, message)
