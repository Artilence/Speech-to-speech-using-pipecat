"""
Voice Conversation Agent Package
Modular voice conversation agent with AI and TTS capabilities
"""

from .config import config
from .ai_service import AIService
from .conversation_manager import ConversationManager
from .websocket_manager import WebSocketManager
from .audio_streaming import AudioStreamingService

__version__ = "1.0.0"
__author__ = "Voice Cat Team"

__all__ = [
    'config',
    'AIService',
    'ConversationManager', 
    'WebSocketManager',
    'AudioStreamingService'
]