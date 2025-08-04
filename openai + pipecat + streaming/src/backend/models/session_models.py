"""
Session models for managing voice chat sessions
"""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from .message_models import ConversationMessage


class SessionState(str, Enum):
    """Voice chat session states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ON_CALL = "on_call"
    PROCESSING = "processing"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class SpeechBuffer:
    """Buffer for accumulating speech transcription chunks"""
    buffer: str = ""
    last_activity: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    sentence_endings: set = field(default_factory=lambda: {'.', '!', '?', '。', '！', '？'})
    
    def add_chunk(self, text: str):
        """Add a transcription chunk to the buffer"""
        self.buffer += " " + text.strip()
        self.last_activity = asyncio.get_event_loop().time()
        
    def has_complete_sentence(self) -> bool:
        """Check if buffer contains a complete sentence"""
        if not self.buffer.strip():
            return False
        return any(ending in self.buffer for ending in self.sentence_endings)
    
    def has_enough_words(self, min_words: int = 3) -> bool:
        """Check if buffer has enough words to process"""
        if not self.buffer.strip():
            return False
        words = self.buffer.strip().split()
        return len(words) >= min_words
        
    def is_timeout(self, timeout_seconds: float = 2.5) -> bool:
        """Check if buffer has timed out (no activity for X seconds)"""
        return (asyncio.get_event_loop().time() - self.last_activity) > timeout_seconds
        
    def get_and_clear(self) -> str:
        """Get buffer content and clear it"""
        content = self.buffer.strip()
        self.buffer = ""
        return content


@dataclass
class VoiceSession:
    """Voice chat session management"""
    session_id: str
    state: SessionState = SessionState.CONNECTING
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    speech_buffer: SpeechBuffer = field(default_factory=SpeechBuffer)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, audio_data: Optional[str] = None):
        """Add a message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            audio_data=audio_data
        )
        self.conversation_history.append(message)
        self.last_activity = datetime.now()
        
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get recent messages for context"""
        return self.conversation_history[-limit:]
        
    def update_state(self, new_state: SessionState):
        """Update session state"""
        self.state = new_state
        self.last_activity = datetime.now()