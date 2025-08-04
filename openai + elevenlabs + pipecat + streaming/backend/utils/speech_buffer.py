"""
Speech Buffer Utility
Handles accumulating and processing speech transcription chunks
"""

import asyncio
from typing import Set


class SpeechBuffer:
    """Buffer for accumulating speech transcription chunks"""
    
    def __init__(self):
        self.buffer = ""
        self.last_activity = asyncio.get_event_loop().time()
        self.sentence_endings: Set[str] = {'.', '!', '?', '。', '！', '？'}
        
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
    
    def clear(self):
        """Clear the buffer"""
        self.buffer = ""
        
    def get_content(self) -> str:
        """Get buffer content without clearing"""
        return self.buffer.strip()
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return not self.buffer.strip()
    
    def word_count(self) -> int:
        """Get word count in buffer"""
        if not self.buffer.strip():
            return 0
        return len(self.buffer.strip().split())
    
    def time_since_last_activity(self) -> float:
        """Get time since last activity in seconds"""
        return asyncio.get_event_loop().time() - self.last_activity
    
    def should_process(self, min_words: int = 3, timeout_seconds: float = 2.5) -> bool:
        """Check if buffer should be processed based on content or timeout"""
        return (self.has_complete_sentence() or 
                self.has_enough_words(min_words) or 
                self.is_timeout(timeout_seconds)) and not self.is_empty()


class ConversationHistory:
    """Manages conversation history with size limits"""
    
    def __init__(self, max_messages: int = 20):
        self.messages = []
        self.max_messages = max_messages
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})
        
        # Keep only the last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 10) -> list:
        """Get the most recent messages"""
        return self.messages[-count:] if self.messages else []
    
    def clear(self):
        """Clear all conversation history"""
        self.messages = []
    
    def get_all_messages(self) -> list:
        """Get all messages in history"""
        return self.messages.copy()
    
    def message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)
    
    def get_context_window(self, max_tokens: int = 1000) -> list:
        """Get messages that fit within a token limit (rough estimation)"""
        # Rough token estimation: 1 token ≈ 4 characters
        estimated_tokens = 0
        context_messages = []
        
        # Start from the most recent messages and work backwards
        for message in reversed(self.messages):
            message_tokens = len(message["content"]) // 4
            if estimated_tokens + message_tokens > max_tokens:
                break
            context_messages.insert(0, message)
            estimated_tokens += message_tokens
        
        return context_messages