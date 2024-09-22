# app.py

from app import create_flask_app
import logging

import asyncio
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send

from app.managers.user_connection_manager import UserConnectionManager
from app.managers.websocket_handler import WebSocketHandler


# Flask setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Initialize user connection manager and WebSocket handler
connection_manager = UserConnectionManager()
websocket_handler = WebSocketHandler(connection_manager)

@app.route('/')
def web_socket_client():
    return render_template('web_socket_client.html')

@socketio.on('connect')
async def handle_connect():
    user_id = request.args.get("user_id")
    websocket = request.sid  # Use the WebSocket connection ID
    await websocket_handler.handle_websocket(websocket, user_id)

@socketio.on('disconnect')
async def handle_disconnect():
    user_id = request.args.get("user_id")
    await connection_manager.remove_connection(user_id)

@socketio.on('message')
async def handle_message(message):
    user_id = request.args.get("user_id")
    await websocket_handler.send_message(user_id, message)

if __name__ == '__main__':
    socketio.run(app, debug=True,port=8080)
