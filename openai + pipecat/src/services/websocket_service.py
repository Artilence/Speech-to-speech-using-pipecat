"""
WebSocket Service module
Handles WebSocket connection management and session tracking
"""
from typing import Set, Dict
from fastapi import WebSocket
from loguru import logger

from ..models import ClientSession, ConversationHistory

class WebSocketService:
    """Service for managing WebSocket connections and client sessions"""
    
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
        
        logger.info(f"New WebSocket connection established. Session: {session}. Total clients: {len(self.connected_clients)}")
        return session
    
    def disconnect_client(self, websocket: WebSocket):
        """
        Remove a WebSocket connection and clean up session
        
        Args:
            websocket: WebSocket connection to remove
        """
        session = self.client_sessions.get(websocket)
        session_info = str(session) if session else "unknown"
        
        self.connected_clients.discard(websocket)
        self.client_sessions.pop(websocket, None)
        
        logger.info(f"WebSocket connection closed. Session: {session_info}. Remaining clients: {len(self.connected_clients)}")
    
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
    
    def get_all_sessions(self) -> Dict[WebSocket, ClientSession]:
        """
        Get all active client sessions
        
        Returns:
            Dictionary mapping WebSocket connections to client sessions
        """
        return self.client_sessions.copy()
    
    async def broadcast_to_all(self, message_data: dict):
        """
        Broadcast a message to all connected clients
        
        Args:
            message_data: Message to broadcast
        """
        if not self.connected_clients:
            logger.debug("No clients connected for broadcast")
            return
        
        disconnected_clients = []
        
        for websocket in self.connected_clients:
            try:
                await websocket.send_json(message_data)
            except Exception as e:
                logger.warning(f"Failed to send broadcast to client: {e}")
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.disconnect_client(websocket)
        
        logger.debug(f"Broadcasted message to {len(self.connected_clients)} clients")