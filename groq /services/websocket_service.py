"""
WebSocket manager for handling real-time connections
"""

import json
import logging
import time
from typing import Dict, Optional, List, Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for voice chat sessions"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.connection_times: Dict[str, float] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.connections[session_id] = websocket
        self.connection_times[session_id] = time.time()
        
        logger.info(f"🔗 WebSocket connected: {session_id}")
        
        # Send connection confirmation
        await self.send_to_session(session_id, {
            "type": "connected",
            "session_id": session_id,
            "timestamp": time.time()
        })
    
    def disconnect(self, session_id: str):
        """Disconnect a WebSocket connection"""
        if session_id in self.connections:
            del self.connections[session_id]
        
        if session_id in self.connection_times:
            connection_duration = time.time() - self.connection_times[session_id]
            del self.connection_times[session_id]
            logger.info(f"🔌 WebSocket disconnected: {session_id} (duration: {connection_duration:.2f}s)")
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to a specific session"""
        if session_id not in self.connections:
            logger.warning(f"⚠️  Attempt to send to disconnected session: {session_id}")
            return False
        
        try:
            websocket = self.connections[session_id]
            message_json = json.dumps(message)
            await websocket.send_text(message_json)
            
            logger.debug(f"📤 Message sent to {session_id}: {message.get('type', 'unknown')}")
            return True
            
        except WebSocketDisconnect:
            logger.warning(f"📡 WebSocket already disconnected: {session_id}")
            self.disconnect(session_id)
            return False
        except Exception as e:
            logger.error(f"❌ Error sending message to {session_id}: {e}")
            return False
    
    async def broadcast(self, message: dict, exclude_sessions: Optional[List[str]] = None):
        """Broadcast a message to all connected sessions"""
        exclude_sessions = exclude_sessions or []
        sent_count = 0
        
        for session_id in list(self.connections.keys()):
            if session_id not in exclude_sessions:
                if await self.send_to_session(session_id, message):
                    sent_count += 1
        
        logger.info(f"📡 Broadcast sent to {sent_count} sessions")
        return sent_count
    
    def get_active_sessions(self) -> List[str]:
        """Get list of currently active session IDs"""
        return list(self.connections.keys())
    
    def get_session_count(self) -> int:
        """Get the number of active sessions"""
        return len(self.connections)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Get information about a specific session"""
        if session_id not in self.connections:
            return None
        
        return {
            "session_id": session_id,
            "connected_at": self.connection_times.get(session_id),
            "connection_duration": time.time() - self.connection_times.get(session_id, time.time()),
            "is_connected": True
        }
    
    async def ping_session(self, session_id: str) -> bool:
        """Ping a specific session to check connectivity"""
        try:
            if session_id in self.connections:
                await self.connections[session_id].ping()
                return True
        except Exception as e:
            logger.warning(f"🏓 Ping failed for {session_id}: {e}")
            self.disconnect(session_id)
        
        return False
    
    async def ping_all_sessions(self) -> int:
        """Ping all active sessions"""
        active_count = 0
        
        for session_id in list(self.connections.keys()):
            if await self.ping_session(session_id):
                active_count += 1
        
        logger.debug(f"🏓 Pinged {active_count} active sessions")
        return active_count