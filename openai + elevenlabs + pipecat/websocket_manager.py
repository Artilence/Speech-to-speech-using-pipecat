"""
WebSocket Manager module
Handles WebSocket connections and message broadcasting
"""
import json
import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manager for WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, message: dict, client_id: str) -> None:
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: dict) -> None:
        """Broadcast a message to all connected clients"""
        if self.active_connections:
            disconnected_clients = []
            for client_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
    
    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected"""
        return client_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connected_clients(self) -> list:
        """Get list of connected client IDs"""
        return list(self.active_connections.keys())