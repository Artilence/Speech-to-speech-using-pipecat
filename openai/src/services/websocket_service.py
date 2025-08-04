"""
WebSocket Service module
Handles WebSocket connection management and message broadcasting
"""
from typing import Set, Dict, Any
from fastapi import WebSocket
import json
from loguru import logger

from ..models import ClientSession, ConversationHistory, MessageType

class WebSocketService:
    """Service for managing WebSocket connections and sessions"""
    
    def __init__(self):
        self.connected_clients: Set[WebSocket] = set()
        self.client_sessions: Dict[WebSocket, ClientSession] = {}
        logger.info("WebSocket Service initialized")
    
    async def connect_client(self, websocket: WebSocket, conversation_history: ConversationHistory) -> ClientSession:
        """
        Accept a new WebSocket connection and create session
        
        Args:
            websocket: WebSocket connection
            conversation_history: Initial conversation history
            
        Returns:
            Created client session
        """
        await websocket.accept()
        self.connected_clients.add(websocket)
        
        session = ClientSession(websocket, conversation_history)
        self.client_sessions[websocket] = session
        
        logger.info(f"New WebSocket connection established. Total clients: {len(self.connected_clients)}")
        return session
    
    def disconnect_client(self, websocket: WebSocket):
        """
        Remove a WebSocket connection and clean up session
        
        Args:
            websocket: WebSocket connection to remove
        """
        self.connected_clients.discard(websocket)
        self.client_sessions.pop(websocket, None)
        logger.info(f"WebSocket connection closed. Remaining clients: {len(self.connected_clients)}")
    
    async def send_message(self, websocket: WebSocket, message_type: MessageType, content: str = None):
        """
        Send a message to a specific WebSocket client
        
        Args:
            websocket: Target WebSocket connection
            message_type: Type of message to send
            content: Message content (optional)
        """
        try:
            message = {"type": message_type.value}
            if content is not None:
                message["content"] = content
            
            await websocket.send_text(json.dumps(message))
            logger.debug(f"Sent message type '{message_type.value}' to client")
            
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect_client(websocket)
    
    async def broadcast_message(self, message_type: MessageType, content: str = None):
        """
        Broadcast a message to all connected clients
        
        Args:
            message_type: Type of message to broadcast
            content: Message content (optional)
        """
        if not self.connected_clients:
            logger.debug("No clients connected for broadcast")
            return
        
        message = {"type": message_type.value}
        if content is not None:
            message["content"] = content
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for websocket in self.connected_clients:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send broadcast to client: {e}")
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.disconnect_client(websocket)
        
        logger.debug(f"Broadcasted message type '{message_type.value}' to {len(self.connected_clients)} clients")
    
    def get_session(self, websocket: WebSocket) -> ClientSession:
        """
        Get the client session for a WebSocket connection
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            Client session or None if not found
        """
        return self.client_sessions.get(websocket)
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections
        
        Returns:
            Number of active WebSocket connections
        """
        return len(self.connected_clients)
    
    def is_connected(self, websocket: WebSocket) -> bool:
        """
        Check if a WebSocket is connected
        
        Args:
            websocket: WebSocket connection to check
            
        Returns:
            True if connected, False otherwise
        """
        return websocket in self.connected_clients