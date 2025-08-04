"""
Audio processing service for speech synthesis and transcription
"""

import base64
from io import BytesIO
from typing import Optional
from gtts import gTTS

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class AudioService:
    """Service for audio processing and synthesis"""
    
    def __init__(self, language: str = 'en'):
        self.language = language
        
    async def synthesize_speech(self, text: str) -> Optional[str]:
        """
        Generate audio from text using gTTS
        
        Args:
            text: Text to synthesize
            
        Returns:
            Base64 encoded audio data or None if failed
        """
        try:
            if not text.strip():
                logger.warning("Empty text provided for synthesis")
                return None
                
            logger.info(f"🔊 Synthesizing audio for: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            tts = gTTS(text=text, lang=self.language)
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_b64 = base64.b64encode(audio_buffer.read()).decode()
            logger.info(f"✅ Audio synthesis successful ({len(audio_b64)} bytes)")
            
            return audio_b64
            
        except Exception as e:
            logger.error(f"❌ Audio synthesis error: {e}")
            return None
    
    async def transcribe_audio_chunk(self, audio_data: bytes, api_key: str) -> str:
        """
        Transcribe audio chunk using OpenAI Whisper API
        
        Args:
            audio_data: Raw audio bytes
            api_key: OpenAI API key
            
        Returns:
            Transcribed text or empty string if failed
        """
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            
            # Skip very small audio chunks
            if len(audio_data) < 2000:  # Less than 2KB probably not useful for speech
                logger.info(f"Skipping small audio chunk: {len(audio_data)} bytes")
                return ""
            
            # Create a temporary file-like object with appropriate extension
            audio_file = BytesIO(audio_data)
            
            # Detect audio format and set appropriate filename
            if audio_data[:4] == b'RIFF':
                audio_file.name = "audio.wav"
                logger.info("Detected WAV format")
            elif audio_data[:4] == b'OggS':
                audio_file.name = "audio.ogg" 
                logger.info("Detected OGG format")
            elif audio_data[:4] == b'\x1aE\xdf\xa3':
                audio_file.name = "audio.webm"
                logger.info("Detected WebM/Matroska format")
            elif b'ftyp' in audio_data[:20]:
                audio_file.name = "audio.mp4"
                logger.info("Detected MP4 format")
            else:
                # Try different extensions for better compatibility
                # Many browsers send WebM with Opus codec
                audio_file.name = "audio.ogg"  # Try OGG first as it often works better
                logger.info(f"Unknown format (first 10 bytes: {audio_data[:10]}), trying as OGG")
            
            logger.info(f"🎙️ Transcribing audio chunk of {len(audio_data)} bytes")
            
            # Frontend now sends WAV format, so this should work directly
            try:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en"  # Specify English for better accuracy
                )
                
                result = response.strip() if response else ""
                logger.info(f"✅ Transcription successful: '{result}'")
                return result
                
            except Exception as e:
                logger.error(f"❌ Transcription failed: {e}")
                return ""
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            return ""
    
    def detect_audio_format(self, audio_data: bytes) -> str:
        """
        Detect audio format from binary data
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            File extension for the detected format
        """
        if audio_data[:4] == b'RIFF':
            return "wav"
        elif audio_data[:4] == b'OggS':
            return "ogg"
        elif audio_data[:4] == b'\x1aE\xdf\xa3':
            return "webm"
        elif b'ftyp' in audio_data[:20]:
            return "mp4"
        else:
            return "ogg"  # Default fallback