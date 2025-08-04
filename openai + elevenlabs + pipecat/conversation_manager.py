"""
Conversation Manager module
Handles conversation history and state management
"""
import logging
from typing import Dict, List
try:
    from .config import config
except ImportError:
    from config import config

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation history for multiple clients"""
    
    def __init__(self):
        self.conversations: Dict[str, List] = {}
    
    def initialize_conversation(self, client_id: str) -> None:
        """Initialize conversation with system message for a client"""
        if client_id not in self.conversations:
            self.conversations[client_id] = [config.get_system_message()]
            logger.info(f"Initialized conversation for client {client_id}")
    
    def add_user_message(self, client_id: str, message: str) -> None:
        """Add user message to conversation history"""
        self.initialize_conversation(client_id)
        self.conversations[client_id].append({"role": "user", "content": message})
    
    def add_ai_message(self, client_id: str, message: str) -> None:
        """Add AI response to conversation history"""
        self.conversations[client_id].append({"role": "assistant", "content": message})
        self._trim_conversation(client_id)
    
    def get_conversation_history(self, client_id: str) -> List:
        """Get conversation history for a client"""
        self.initialize_conversation(client_id)
        return self.conversations[client_id].copy()
    
    def _trim_conversation(self, client_id: str) -> None:
        """Keep conversation history manageable"""
        if len(self.conversations[client_id]) > config.max_conversation_history:
            # Keep system message + last 10 messages
            self.conversations[client_id] = (
                self.conversations[client_id][:1] + 
                self.conversations[client_id][-10:]
            )
            logger.info(f"Trimmed conversation history for client {client_id}")
    
    def cleanup_conversation(self, client_id: str) -> None:
        """Clean up conversation history for disconnected client"""
        if client_id in self.conversations:
            del self.conversations[client_id]
            logger.info(f"Cleaned up conversation for client {client_id}")
    
    def get_active_clients(self) -> List[str]:
        """Get list of active client IDs"""
        return list(self.conversations.keys())