"""
Configuration module for Voice Conversation Agent
Handles environment variables and application settings
"""
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

class Config:
    """Configuration class for managing environment variables and settings"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        # Server settings
        self.host = "127.0.0.1"
        self.port = 8000
        self.reload = True
        self.log_level = "info"
        
        # AI settings
        self.ai_model = "gpt-3.5-turbo"
        self.max_tokens = 150
        self.temperature = 0.7
        
        # TTS settings
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        self.model_id = "eleven_flash_v2_5"  # Fast model for low latency
        
        # Conversation settings
        self.max_conversation_history = 11  # system + 10 messages
        
        # Streaming settings
        self.chunk_size = 100
        self.chunk_delay = 0.01
        
        # Validate required settings
        self._validate_config()
        
        # Setup logging
        self._setup_logging()
    
    def _validate_config(self):
        """Validate that required environment variables are set"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    def _setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_openai_client(self):
        """Get configured OpenAI client"""
        return OpenAI(api_key=self.openai_api_key)
    
    def get_system_message(self):
        """Get the system message for AI conversations"""
        return {
            "role": "system", 
            "content": "You are a helpful, friendly voice assistant. Keep your responses concise and conversational, typically 1-2 sentences unless more detail is specifically requested."
        }
    
    def get_voice_settings(self):
        """Get optimized voice settings for low latency"""
        return {
            "stability": 0.4,  # Lower for faster generation
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": False  # Disable for lower latency
        }
    
    def get_generation_config(self):
        """Get generation config for aggressive chunking"""
        return {
            "chunk_length_schedule": [50, 90, 120, 150]  # Smaller chunks for faster response
        }

# Global config instance
config = Config()