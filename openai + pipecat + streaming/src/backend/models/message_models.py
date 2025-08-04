"""
Message models for WebSocket communication
"""

from enum import Enum
from typing import Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime


class MessageType(str, Enum):
    """WebSocket message types"""
    USER_SPEECH = "user_speech"
    AI_TYPING = "ai_typing"
    AI_RESPONSE_START = "ai_response_start"
    AI_CHUNK = "ai_chunk"
    AI_RESPONSE_COMPLETE = "ai_response_complete"
    AUDIO_CHUNK = "audio_chunk"
    SYSTEM = "system"
    ERROR = "error"
    TRANSCRIPTION = "transcription"
    LIVE_TRANSCRIPTION = "live_transcription"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    content: str
    full_text: Optional[str] = None
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "type": self.type.value,
            "content": self.content
        }
        
        if self.full_text is not None:
            result["full_text"] = self.full_text
        if self.text is not None:
            result["text"] = self.text
        if self.metadata:
            result.update(self.metadata)
            
        return result


@dataclass
class ConversationMessage:
    """Conversation history message"""
    role: str  # "user" or "assistant" or "system"
    content: str
    timestamp: datetime
    audio_data: Optional[str] = None  # Base64 encoded audio
    
    def to_openai_format(self) -> Dict[str, str]:
        """Convert to OpenAI API format"""
        return {
            "role": self.role,
            "content": self.content
        }