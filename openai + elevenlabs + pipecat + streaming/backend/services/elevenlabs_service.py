"""
ElevenLabs Service Module
Handles text-to-speech synthesis using ElevenLabs API
"""

import os
import time
import base64
from typing import Optional
import httpx
from loguru import logger


class ElevenLabsService:
    """Service for handling ElevenLabs TTS operations"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is required")
        
        # Default voice ID (you can make this configurable)
        self.default_voice_id = "pNInz6obpgDQGcFmaJgB"
        
        # API endpoints
        self.base_url = "https://api.elevenlabs.io/v1"
        
    async def synthesize_audio_flash(self, text: str, voice_id: Optional[str] = None) -> str:
        """Generate audio using ElevenLabs Flash TTS (75ms latency)"""
        try:
            if not text.strip():
                return ""
                
            synthesis_start = time.time()
            logger.info(f"Starting ElevenLabs Flash TTS for {len(text)} characters")
            
            # Use provided voice_id or default
            voice_id = voice_id or self.default_voice_id
            
            # ElevenLabs Flash API endpoint
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_flash_v2_5",  # Flash model for 75ms latency
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=30.0)
                
            api_time = time.time()
            logger.info(f"ElevenLabs API call completed in {(api_time - synthesis_start)*1000:.2f}ms")
            
            if response.status_code == 200:
                audio_data = response.content
                audio_b64 = base64.b64encode(audio_data).decode()
                
                encode_time = time.time()
                total_time = (encode_time - synthesis_start) * 1000
                logger.info(f"Total ElevenLabs Flash synthesis: {total_time:.2f}ms (audio size: {len(audio_b64)} chars)")
                
                return audio_b64
            else:
                logger.error(f"ElevenLabs API error {response.status_code}: {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
            return ""

    async def synthesize_audio_standard(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        model_id: str = "eleven_monolingual_v1",
        stability: float = 0.5,
        similarity_boost: float = 0.8
    ) -> str:
        """Generate audio using standard ElevenLabs TTS with customizable settings"""
        try:
            if not text.strip():
                return ""
                
            synthesis_start = time.time()
            logger.info(f"Starting ElevenLabs standard TTS for {len(text)} characters")
            
            # Use provided voice_id or default
            voice_id = voice_id or self.default_voice_id
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=60.0)
                
            api_time = time.time()
            logger.info(f"ElevenLabs standard API call completed in {(api_time - synthesis_start)*1000:.2f}ms")
            
            if response.status_code == 200:
                audio_data = response.content
                audio_b64 = base64.b64encode(audio_data).decode()
                
                encode_time = time.time()
                total_time = (encode_time - synthesis_start) * 1000
                logger.info(f"Total ElevenLabs standard synthesis: {total_time:.2f}ms")
                
                return audio_b64
            else:
                logger.error(f"ElevenLabs API error {response.status_code}: {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"ElevenLabs standard synthesis error: {e}")
            return ""

    async def get_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs"""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                voices_data = response.json()
                return voices_data.get("voices", [])
            else:
                logger.error(f"Failed to get voices: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []

    async def get_voice_settings(self, voice_id: Optional[str] = None) -> dict:
        """Get current voice settings"""
        try:
            voice_id = voice_id or self.default_voice_id
            url = f"{self.base_url}/voices/{voice_id}/settings"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get voice settings: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting voice settings: {e}")
            return {}

    def set_default_voice(self, voice_id: str):
        """Set the default voice ID for this service instance"""
        self.default_voice_id = voice_id
        logger.info(f"Default voice set to: {voice_id}")

    async def check_api_key(self) -> bool:
        """Check if the API key is valid"""
        try:
            voices = await self.get_available_voices()
            return len(voices) > 0
        except Exception:
            return False