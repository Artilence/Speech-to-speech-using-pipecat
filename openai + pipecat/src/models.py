"""
Data models and types for the OpenAI + Pipecat Voice Assistant
"""
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel
from fastapi import WebSocket

class MessageType(str, Enum):
    """WebSocket message types"""
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    VOICE_CHUNK = "voice_chunk"
    TEXT = "text"
    PING = "ping"
    PONG = "pong"
    MESSAGE = "message"
    AUDIO = "audio"
    ERROR = "error"
    INFO = "info"
    KEEPALIVE = "keepalive"

class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: MessageType
    content: Optional[str] = None

class ConversationMessage(BaseModel):
    """Individual conversation message"""
    role: str  # "system", "user", "assistant"
    content: str

class ConversationHistory:
    """Manages conversation history for a session"""
    
    def __init__(self, system_message: dict):
        self.messages: List[ConversationMessage] = [
            ConversationMessage(**system_message)
        ]
    
    def add_user_message(self, content: str):
        """Add a user message to the conversation"""
        self.messages.append(ConversationMessage(role="user", content=content))
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation"""
        self.messages.append(ConversationMessage(role="assistant", content=content))
    
    def get_messages_dict(self) -> List[Dict[str, str]]:
        """Get messages in OpenAI API format"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self):
        """Clear conversation history except system message"""
        self.messages = [self.messages[0]]  # Keep only system message
    
    def get_last_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """Get the last N messages (including system message)"""
        if len(self.messages) <= count:
            return self.get_messages_dict()
        return [self.messages[0].dict()] + [msg.dict() for msg in self.messages[-(count-1):]]

class ClientSession:
    """Represents a client WebSocket session"""
    
    def __init__(self, websocket: WebSocket, conversation_history: ConversationHistory):
        self.websocket = websocket
        self.conversation_history = conversation_history
        self.is_recording = False
        self.session_id = id(websocket)  # Simple session identifier
    
    def __str__(self):
        return f"ClientSession(id={self.session_id}, recording={self.is_recording})"