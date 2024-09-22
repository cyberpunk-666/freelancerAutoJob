import os
import logging
from dotenv import load_dotenv
from flask_login import current_user
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send
from app.services.email_processor import EmailProcessor
from app.managers.user_connection_manager import UserConnectionManager
from app.managers.websocket_handler import WebSocketHandler
from services.task_queue import TaskQueue
import eventlet

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Flask and SocketIO setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

# Initialize user connection manager and WebSocket handler
connection_manager = UserConnectionManager()
websocket_handler = WebSocketHandler(connection_manager)

# Load environment variables
load_dotenv()

# Task queue-related functions
def handle_email_task(task_data):
    logging.info(f"Received email task data: {task_data}")
    
    try:
        email_processor = EmailProcessor()
        user_id = current_user.user_id
        logging.info(f"Fetching jobs from email for user_id: {user_id}")
        email_processor.fetch_jobs_from_email(user_id)
        logging.info("Email task completed successfully.")
    except Exception as e:
        logging.error(f"Error in handle_email_task: {str(e)}")

def run_task_queue_listener():
    logging.info("Initializing task queue listener...")
    
    # Create a TaskQueue instance
    task_queue = TaskQueue()
    task_queue.register_callback('fetch_email_jobs', handle_email_task)

    try:
        logging.info("Starting task queue processing.")
        task_queue.start_processing()

        # Keep the main thread running
        while True:
            eventlet.sleep(1)
    except KeyboardInterrupt:
        logging.info("Task queue processing interrupted by KeyboardInterrupt.")
        task_queue.stop_processing()
    except Exception as e:
        logging.error(f"An error occurred in task queue listener: {str(e)}")
        task_queue.stop_processing()

# Flask routes and socket events
@app.route('/')
def web_socket_client():
    logging.info("Rendering WebSocket client page.")
    return render_template('web_socket_client.html')

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get("user_id")
    websocket = request.sid  # Use the WebSocket connection ID
    logging.info(f"User {user_id} connected with websocket ID: {websocket}")
    
    try:
        eventlet.spawn(websocket_handler.handle_websocket, websocket, user_id)
        logging.info(f"WebSocket handler spawned for user {user_id}.")
    except Exception as e:
        logging.error(f"Error handling WebSocket connect for user {user_id}: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.args.get("user_id")
    logging.info(f"User {user_id} disconnected.")
    
    try:
        eventlet.spawn(connection_manager.remove_connection, user_id)
        logging.info(f"Removed connection for user {user_id}.")
    except Exception as e:
        logging.error(f"Error handling WebSocket disconnect for user {user_id}: {str(e)}")

@socketio.on('message')
def handle_message(message):
    user_id = request.args.get("user_id")
    logging.info(f"Received message from user {user_id}: {message}")
    
    try:
        eventlet.spawn(websocket_handler.send_message, user_id, message)
        logging.info(f"Message sent to user {user_id}.")
    except Exception as e:
        logging.error(f"Error sending message to user {user_id}: {str(e)}")

# Main function to run both task queue and Flask app
if __name__ == '__main__':
    logging.info("Starting application...")

    # Run task queue listener in a separate green thread
    eventlet.spawn(run_task_queue_listener)
    logging.info("Task queue listener started in a green thread.")

    # Run Flask-SocketIO app
    try:
        logging.info("Starting Flask-SocketIO server.")
        socketio.run(app, debug=True, port=8080)
    except Exception as e:
        logging.error(f"Error starting Flask-SocketIO server: {str(e)}")
