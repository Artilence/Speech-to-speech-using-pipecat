"""
Configuration service for managing API keys and settings
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing configuration and API keys"""
    
    def __init__(self):
        self.groq_api_key: Optional[str] = None
        self.openai_api_key: Optional[str] = None
        
        # Load configuration
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Load environment variables from .env file
        load_dotenv()
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")  # Optional fallback
        
        # LLM settings
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # WebSocket settings
        self.websocket_timeout = int(os.getenv("WEBSOCKET_TIMEOUT", "30"))
        
        # Audio settings
        self.audio_sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", "24000"))
        self.audio_chunk_size = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
        
        logger.info("📋 Configuration loaded successfully")
    
    def _validate_config(self):
        """Validate required configuration"""
        if not self.groq_api_key:
            logger.error("❌ GROQ_API_KEY is required")
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        logger.info("✅ Configuration validation passed")
        logger.info(f"🤖 Using Groq model: {self.groq_model}")
        logger.info(f"🗣️ Using Browser TTS (ElevenLabs removed)")
    
    def get_groq_config(self) -> dict:
        """Get Groq LLM configuration"""
        return {
            "api_key": self.groq_api_key,
            "model": self.groq_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    def get_audio_config(self) -> dict:
        """Get audio processing configuration"""
        return {
            "sample_rate": self.audio_sample_rate,
            "chunk_size": self.audio_chunk_size
        }
    
    def is_ready(self) -> bool:
        """Check if all required configuration is available"""
        return bool(self.groq_api_key)