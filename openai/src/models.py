"""
Data models and types for the OpenAI Voice Assistant
"""
from typing import List, Dict, Optional, Union
from enum import Enum
from pydantic import BaseModel

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
    """Conversation message structure"""
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
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages in OpenAI API format"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def clear(self):
        """Clear conversation history except system message"""
        self.messages = [self.messages[0]]  # Keep only system message

class ClientSession:
    """Represents a client WebSocket session"""
    
    def __init__(self, websocket, conversation_history: ConversationHistory):
        self.websocket = websocket
        self.conversation_history = conversation_history
        self.is_recording = False