"""
OpenAI Service Module
Handles all interactions with OpenAI API including chat completions and transcriptions
"""

import os
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
from io import BytesIO
from openai import AsyncOpenAI
from loguru import logger


class OpenAIService:
    """Service for handling OpenAI API operations"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def transcribe_audio_chunk(self, audio_data: bytes) -> str:
        """Transcribe audio chunk using OpenAI Whisper API - OPTIMIZED FOR SPEED"""
        try:
            transcription_start_time = time.time()
            
            # Skip very small audio chunks
            if len(audio_data) < 1500:  # Reduced threshold for faster processing
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
                audio_file.name = "audio.ogg"
                logger.info("Unknown format, trying as OGG")
            
            logger.info(f"Starting Whisper transcription of {len(audio_data)} bytes")
            
            # OPTIMIZED Whisper API call
            try:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en",  # Specify English for better speed
                )
                
                transcription_end_time = time.time()
                transcription_duration = (transcription_end_time - transcription_start_time) * 1000
                
                result = response.strip() if response else ""
                logger.info(f"Whisper transcription completed in {transcription_duration:.2f}ms: '{result}'")
                return result
                
            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}")
                return ""
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    async def get_chat_completion_stream(
        self, 
        user_text: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "You are a helpful AI assistant. Keep responses concise and conversational since this is a voice chat.",
        model: str = "gpt-4o-mini",
        max_tokens: int = 150,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Get streaming chat completion from OpenAI"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages
            
            # Add current user message
            messages.append({"role": "user", "content": user_text})
            
            # Create streaming chat completion
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            # Process streaming response
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"

    async def get_fast_response(
        self, 
        user_text: str,
        use_conversation_history: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """Get ultra-fast AI response optimized for low latency"""
        try:
            ai_start_time = time.time()
            logger.info(f"Getting AI response for: '{user_text}'")
            
            # ULTRA FAST CONFIGURATION - NO HISTORY, MINIMAL TOKENS, FASTEST MODEL
            messages = [
                {"role": "system", "content": "Be brief. One short sentence only."},
                {"role": "user", "content": user_text}
            ]
            
            # Only add history if specifically requested
            if use_conversation_history and conversation_history:
                messages = [{"role": "system", "content": "Be brief. One short sentence only."}] + conversation_history[-5:] + [{"role": "user", "content": user_text}]
            
            stream_start_time = time.time()
            stream = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Actually faster for simple responses than gpt-4o-mini
                messages=messages,
                max_tokens=25,  # VERY short responses for speed
                temperature=0.1,  # Very low for fastest generation
                stream=True,
                presence_penalty=0,
                frequency_penalty=0,
            )
            
            stream_create_time = time.time()
            logger.info(f"OpenAI stream created in {(stream_create_time - stream_start_time)*1000:.2f}ms")
            
            response_text = ""
            first_chunk_time = None
            chunk_count = 0
            
            # Process streaming response
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    chunk_time = time.time()
                    if first_chunk_time is None:
                        first_chunk_time = chunk_time
                        logger.info(f"First AI chunk received in {(first_chunk_time - stream_create_time)*1000:.2f}ms")
                    
                    content = chunk.choices[0].delta.content
                    response_text += content
                    chunk_count += 1
                    
                    yield content
            
            # Log timing summary
            total_ai_time = (time.time() - ai_start_time) * 1000
            logger.info(f"ULTRA-FAST AI RESPONSE TIMING: {total_ai_time:.2f}ms total, {chunk_count} chunks, {len(response_text)} chars")
            
        except Exception as e:
            logger.error(f"AI fast response error: {e}")
            yield f"Error: {str(e)}"

    async def get_simple_completion(self, user_text: str, system_prompt: str = None) -> str:
        """Get a simple, non-streaming completion"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_text})
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Simple completion error: {e}")
            return f"Error: {str(e)}"