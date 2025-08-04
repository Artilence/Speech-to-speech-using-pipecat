"""
Text-to-Speech Service module
Handles conversion of text to audio using gTTS
"""
import base64
from io import BytesIO
from gtts import gTTS
from loguru import logger

from ..config import config

class TTSService:
    """Service for text-to-speech conversion"""
    
    def __init__(self):
        self.language = config.tts_language
        logger.info(f"TTS Service initialized with language: {self.language}")
    
    async def synthesize_audio(self, text: str) -> str:
        """
        Convert text to base64-encoded audio (mp3)
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Base64-encoded audio data, empty string if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS synthesis")
            return ""
        
        try:
            logger.debug(f"Synthesizing audio for text: {text[:50]}...")
            
            # Create TTS object
            tts = gTTS(text=text.strip(), lang=self.language)
            
            # Write to BytesIO buffer
            buffer = BytesIO()
            tts.write_to_fp(buffer)
            
            # Encode to base64
            audio_data = base64.b64encode(buffer.getvalue()).decode()
            
            logger.debug(f"Audio synthesis completed, data length: {len(audio_data)}")
            return audio_data
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return ""
    
    def validate_language(self, lang_code: str) -> bool:
        """
        Validate if language code is supported by gTTS
        
        Args:
            lang_code: Language code to validate
            
        Returns:
            True if language is supported, False otherwise
        """
        try:
            from gtts.lang import tts_langs
            supported_langs = tts_langs()
            return lang_code in supported_langs
        except Exception as e:
            logger.error(f"Language validation error: {e}")
            return False
    
    def get_supported_languages(self) -> dict:
        """
        Get dictionary of supported languages
        
        Returns:
            Dictionary mapping language codes to language names
        """
        try:
            from gtts.lang import tts_langs
            return tts_langs()
        except Exception as e:
            logger.error(f"Error getting supported languages: {e}")
            return {}
    
    def set_language(self, lang_code: str) -> bool:
        """
        Set the language for TTS synthesis
        
        Args:
            lang_code: Language code to set
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if self.validate_language(lang_code):
            self.language = lang_code
            logger.info(f"TTS language set to: {lang_code}")
            return True
        else:
            logger.warning(f"Invalid language code: {lang_code}")
            return False