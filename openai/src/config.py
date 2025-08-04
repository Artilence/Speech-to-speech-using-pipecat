"""
Configuration module for OpenAI Voice Assistant
Handles environment variables and application settings
"""
import os
import sys
from typing import Optional
from dotenv import load_dotenv
from loguru import logger

class Config:
    """Configuration class for managing application settings"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        
        # Setup logging
        logger.add(sys.stderr, level="DEBUG")
        
        # API Configuration
        self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
        
        # Server Configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("FAST_API_PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # AI Model Configuration
        self.ai_model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "300"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # TTS Configuration
        self.tts_language = os.getenv("TTS_LANGUAGE", "en")
        
        # WebSocket Configuration
        self.websocket_timeout = int(os.getenv("WEBSOCKET_TIMEOUT", "60"))
        self.keepalive_interval = int(os.getenv("KEEPALIVE_INTERVAL", "30"))
        
        # CORS Configuration
        self.cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
        
        # Validate configuration
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"{key} is required in environment variables")
        return value
    
    def _validate_config(self):
        """Validate configuration values"""
        if self.max_tokens <= 0:
            raise ValueError("MAX_TOKENS must be positive")
        
        if not 0 <= self.temperature <= 2:
            raise ValueError("TEMPERATURE must be between 0 and 2")
        
        if self.websocket_timeout <= 0:
            raise ValueError("WEBSOCKET_TIMEOUT must be positive")
    
    def get_system_message(self) -> dict:
        """Get the system message for AI conversations"""
        return {
            "role": "system",
            "content": "You are a helpful AI assistant. Respond to user messages in a friendly, conversational way. Keep responses concise but informative. Provide clear, actionable answers when possible."
        }

# Global config instance
config = Config()