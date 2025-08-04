"""
WebSocket service for real-time communication
"""

import json
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect

from ..models.message_models import WebSocketMessage, MessageType
from ..models.session_models import VoiceSession, SessionState
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class WebSocketService:
    """Service for managing WebSocket connections and sessions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, VoiceSession] = {}
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept WebSocket connection and create session
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            Session ID
        """
        await websocket.accept()
        session_id = f"session_{id(websocket)}"
        
        # Create new session
        session = VoiceSession(session_id=session_id)
        session.update_state(SessionState.CONNECTED)
        
        # Store session and connection
        self.active_sessions[session_id] = session
        self.active_connections[session_id] = websocket
        
        logger.info(f"📞 WebSocket connected: {session_id}")
        
        # Send welcome message
        await self.send_message(session_id, WebSocketMessage(
            type=MessageType.SYSTEM,
            content="📞 Ready for voice call - click the call button to start!"
        ))
        
        return session_id
    
    async def disconnect(self, session_id: str):
        """
        Handle WebSocket disconnection
        
        Args:
            session_id: Session to disconnect
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.update_state(SessionState.DISCONNECTED)
            
        # Clean up
        self.active_sessions.pop(session_id, None)
        self.active_connections.pop(session_id, None)
        
        logger.info(f"📞 WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: WebSocketMessage):
        """
        Send message to WebSocket client
        
        Args:
            session_id: Target session
            message: Message to send
        """
        websocket = self.active_connections.get(session_id)
        if not websocket:
            logger.warning(f"⚠️  No WebSocket connection for session: {session_id}")
            return
            
        try:
            await websocket.send_json(message.to_dict())
            logger.debug(f"📤 Sent {message.type.value} to {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send message to {session_id}: {e}")
            await self.disconnect(session_id)
    
    async def receive_message(self, session_id: str) -> Optional[Dict]:
        """
        Receive message from WebSocket client
        
        Args:
            session_id: Source session
            
        Returns:
            Parsed message or None if error
        """
        websocket = self.active_connections.get(session_id)
        if not websocket:
            logger.warning(f"⚠️  No WebSocket connection for session: {session_id}")
            return None
            
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.debug(f"📨 Received {message.get('type', 'unknown')} from {session_id}")
            return message
            
        except WebSocketDisconnect:
            logger.info(f"📞 Client disconnected: {session_id}")
            await self.disconnect(session_id)
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON from {session_id}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error receiving message from {session_id}: {e}")
            return None
    
    async def broadcast_to_session(self, session_id: str, message_type: MessageType, 
                                 content: str, **kwargs):
        """
        Convenience method to broadcast message to a session
        
        Args:
            session_id: Target session
            message_type: Type of message
            content: Message content
            **kwargs: Additional message fields
        """
        message = WebSocketMessage(
            type=message_type,
            content=content,
            **kwargs
        )
        await self.send_message(session_id, message)
    
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def update_session_state(self, session_id: str, state: SessionState):
        """Update session state"""
        session = self.active_sessions.get(session_id)
        if session:
            session.update_state(state)
            logger.info(f"🔄 Session {session_id} state: {state.value}")
    
    async def ping_session(self, session_id: str):
        """Send ping to keep connection alive"""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.ping()
                logger.debug(f"🏓 Ping sent to {session_id}")
            except Exception as e:
                logger.error(f"❌ Ping failed for {session_id}: {e}")
                await self.disconnect(session_id)
    
    def get_session_stats(self) -> Dict:
        """Get statistics about active sessions"""
        return {
            "active_sessions": len(self.active_sessions),
            "session_ids": list(self.active_sessions.keys()),
            "session_states": {
                sid: session.state.value 
                for sid, session in self.active_sessions.items()
            }
        }