"""
Configuration service for managing API keys and settings for Pipecat + Groq + Browser TTS/STT
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
        self.elevenlabs_api_key: Optional[str] = None
        
        # Load configuration
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Load environment variables from .env file
        load_dotenv()
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        # LLM settings
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # WebSocket settings
        self.websocket_timeout = int(os.getenv("WEBSOCKET_TIMEOUT", "30"))
        
        # Audio settings (for browser compatibility)
        self.audio_sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", "24000"))
        self.audio_chunk_size = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
        self.audio_channels = int(os.getenv("AUDIO_CHANNELS", "1"))
        
        # Pipecat settings
        self.enable_interruptions = os.getenv("ENABLE_INTERRUPTIONS", "true").lower() == "true"
        self.vad_enabled = os.getenv("VAD_ENABLED", "false").lower() == "true"  # Disabled by default for browser
        
        logger.info("📋 Configuration loaded successfully")
    
    def _validate_config(self):
        """Validate required configuration"""
        if not self.groq_api_key:
            logger.error("❌ GROQ_API_KEY is required")
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        logger.info("✅ Configuration validation passed")
        logger.info(f"🤖 Using Groq model: {self.groq_model}")
        logger.info(f"🗣️ Using Browser TTS (Web Speech API)")
        logger.info(f"🎤 Using Browser STT (Web Speech API)")
    
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
            "chunk_size": self.audio_chunk_size,
            "channels": self.audio_channels
        }
    
    def get_pipecat_config(self) -> dict:
        """Get Pipecat framework configuration"""
        return {
            "enable_interruptions": self.enable_interruptions,
            "vad_enabled": self.vad_enabled,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_channels": self.audio_channels
        }
    
    def is_ready(self) -> bool:
        """Check if all required configuration is available"""
        return bool(self.groq_api_key)
    
    def get_service_info(self) -> dict:
        """Get information about configured services"""
        return {
            "groq": {
                "enabled": bool(self.groq_api_key),
                "model": self.groq_model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            },
            "browser_tts": {
                "enabled": True,
                "service": "Web Speech API",
                "type": "browser"
            },
            "browser_stt": {
                "enabled": True,
                "service": "Web Speech API",
                "type": "browser"
            },
            "pipecat": {
                "interruptions": self.enable_interruptions,
                "vad": self.vad_enabled
            },
            "audio": {
                "sample_rate": self.audio_sample_rate,
                "channels": self.audio_channels,
                "chunk_size": self.audio_chunk_size
            }
        }