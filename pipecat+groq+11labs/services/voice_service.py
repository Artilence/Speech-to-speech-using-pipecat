"""
Voice service integrating Pipecat + Groq LLM + Browser TTS/STT
"""

import asyncio
import json
import logging
import time
import base64
from typing import Dict, List, Optional, Any

from groq import AsyncGroq
from elevenlabs import ElevenLabs

from .config_service import ConfigService
from .websocket_service import WebSocketManager

logger = logging.getLogger(__name__)


class VoicePipelineService:
    """Core voice service managing Pipecat-inspired pipeline with Groq + Browser services"""
    
    def __init__(self, config_service: ConfigService):
        self.config = config_service
        self.groq_client = None
        self.elevenlabs_client = None
        self.session_contexts: Dict[str, dict] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients"""
        try:
            # Initialize Groq client
            groq_config = self.config.get_groq_config()
            self.groq_client = AsyncGroq(api_key=groq_config["api_key"])
            
            # Initialize ElevenLabs client
            if self.config.elevenlabs_api_key:
                self.elevenlabs_client = ElevenLabs(api_key=self.config.elevenlabs_api_key)
                logger.info("✅ ElevenLabs TTS client initialized")
            else:
                logger.warning("⚠️ ElevenLabs API key not found, using browser TTS")
            
            logger.info("✅ Voice pipeline service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize voice service: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if the voice service is ready"""
        return bool(self.groq_client and self.config.is_ready())
    
    async def create_session_pipeline(self, session_id: str, websocket_manager: WebSocketManager) -> dict:
        """Create a session context for browser-based processing"""
        try:
            # Initialize session context
            self.session_contexts[session_id] = {
                "conversation_history": [],
                "websocket_manager": websocket_manager,
                "created_at": time.time(),
                "active": True
            }
            
            logger.info(f"✅ Browser pipeline session created: {session_id}")
            return {"session_id": session_id, "type": "browser_pipeline"}
            
        except Exception as e:
            logger.error(f"❌ Failed to create session for {session_id}: {e}")
            raise
    
    async def process_user_input(
        self, 
        session_id: str, 
        user_text: str, 
        conversation_history: List[dict]
    ) -> dict:
        """Process user input through Groq LLM (browser handles TTS/STT)"""
        start_time = time.time()
        
        try:
            if session_id not in self.session_contexts:
                raise ValueError(f"No session found for: {session_id}")
            
            # Update conversation context
            self.session_contexts[session_id]["conversation_history"] = conversation_history
            
            # Process through Groq LLM
            response_data = await self._process_with_groq(user_text, conversation_history)
            
            llm_latency = (time.time() - start_time) * 1000
            
            # Generate TTS audio if ElevenLabs is available
            audio_data = None
            if self.elevenlabs_client:
                try:
                    audio_data = await self._generate_elevenlabs_tts(response_data["text"])
                except Exception as e:
                    logger.warning(f"⚠️ ElevenLabs TTS failed, fallback to browser: {e}")

            result = {
                "text": response_data["text"],
                "llm_latency": llm_latency,
                "model_used": self.config.groq_model,
                "tokens_used": response_data.get("tokens_used", 0),
                "tts_method": "elevenlabs" if audio_data else "browser",
                "audio_data": audio_data
            }
            
            logger.info(f"🤖 LLM response ({llm_latency:.2f}ms): {response_data['text'][:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing user input: {e}")
            raise Exception(f"Failed to process input: {str(e)}")
    
    async def _process_with_groq(self, user_input: str, conversation_history: List[dict]) -> dict:
        """Process input with Groq LLM"""
        try:
            # Prepare conversation context
            messages = self._prepare_conversation_context(user_input, conversation_history)
            
            # Get Groq configuration
            groq_config = self.config.get_groq_config()
            
            # Generate response
            response = await self.groq_client.chat.completions.create(
                model=groq_config["model"],
                messages=messages,
                max_tokens=groq_config["max_tokens"],
                temperature=groq_config["temperature"],
                stream=False
            )
            
            ai_text = response.choices[0].message.content
            
            return {
                "text": ai_text,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error with Groq LLM: {e}")
            raise
    
    def _prepare_conversation_context(
        self, 
        user_input: str, 
        conversation_history: List[dict]
    ) -> List[dict]:
        """Prepare conversation context for the LLM"""
        
        # System prompt for voice assistant
        system_prompt = """You are a helpful AI voice assistant powered by Pipecat framework, Groq AI, and browser speech services. Provide clear, concise, and natural-sounding responses that are suitable for text-to-speech conversion.

Guidelines:
- Keep responses conversational and engaging
- Avoid overly technical language unless specifically asked
- Use natural speech patterns
- Keep responses reasonably brief (1-3 sentences typically)
- Show personality while being helpful
- If you don't know something, admit it honestly

You are designed for real-time voice conversations using advanced pipeline processing with browser speech APIs, so make your responses flow naturally when spoken aloud."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (limit to last 10 exchanges)
        recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
        
        for msg in recent_history:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    async def process_audio_chunk(self, session_id: str, audio_data: str):
        """Process incoming audio chunk (browser handles STT)"""
        try:
            if session_id not in self.session_contexts:
                logger.warning(f"No session for: {session_id}")
                return
            
            # In browser-based implementation, audio is processed by browser STT
            # This would typically be transcription results sent from browser
            logger.debug(f"Audio chunk received for {session_id} (browser STT)")
            
        except Exception as e:
            logger.error(f"❌ Error processing audio chunk: {e}")
    
    async def start_recording(self, session_id: str):
        """Start recording for a session (browser-based)"""
        try:
            if session_id in self.session_contexts:
                logger.info(f"🎤 Started browser recording for session: {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Error starting recording: {e}")
    
    async def stop_recording(self, session_id: str):
        """Stop recording for a session (browser-based)"""
        try:
            if session_id in self.session_contexts:
                logger.info(f"🛑 Stopped browser recording for session: {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Error stopping recording: {e}")
    
    async def handle_interruption(self, session_id: str):
        """Handle user interruption of AI processing"""
        try:
            if session_id in self.session_contexts:
                context = self.session_contexts[session_id]
                
                # Mark session as interrupted
                context["interrupted"] = True
                context["interrupted_at"] = time.time()
                
                logger.info(f"🛑 Session {session_id} marked as interrupted")
                
                # Note: Since we're using browser TTS and direct API calls,
                # the actual audio stopping is handled on the frontend.
                # This method serves as a record of the interruption event.
                
        except Exception as e:
            logger.error(f"❌ Error handling interruption for session {session_id}: {e}")

    async def cleanup_session(self, session_id: str):
        """Clean up session-specific resources"""
        try:
            if session_id in self.session_contexts:
                self.session_contexts[session_id]["active"] = False
                del self.session_contexts[session_id]
                logger.debug(f"🧹 Cleaned up session: {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up session {session_id}: {e}")
    
    def get_session_info(self, session_id: str) -> dict:
        """Get information about a session"""
        context_info = self.session_contexts.get(session_id, {})
        
        return {
            "has_context": bool(context_info),
            "is_active": context_info.get("active", False),
            "created_at": context_info.get("created_at"),
            "conversation_length": len(context_info.get("conversation_history", []))
        }
    
    async def _generate_elevenlabs_tts(self, text: str) -> str:
        """Generate TTS audio using ElevenLabs API"""
        try:
            tts_start = time.time()
            
            # Generate audio using ElevenLabs (optimized for speed)
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id="JBFqnCBsd6RMkjVDRZzb",  # Rachel voice ID
                text=text,
                model_id="eleven_flash_v2_5",  # Ultra-fast model (~75ms latency)
                optimize_streaming_latency=3  # Max latency optimizations
            )
            
            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            
            # Convert to base64 for transmission
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            tts_latency = (time.time() - tts_start) * 1000
            logger.info(f"🔊 ElevenLabs TTS generated ({tts_latency:.2f}ms): {len(audio_bytes)} bytes")
            
            return audio_base64
            
        except Exception as e:
            logger.error(f"❌ ElevenLabs TTS generation failed: {e}")
            raise
    
    def get_service_stats(self) -> dict:
        """Get service statistics"""
        tts_service = "ElevenLabs TTS" if self.elevenlabs_client else "Browser Web Speech API"
        framework = "pipecat + elevenlabs" if self.elevenlabs_client else "pipecat + browser"
        
        return {
            "active_sessions": len([s for s in self.session_contexts.values() if s.get("active", False)]),
            "groq_ready": bool(self.groq_client),
            "elevenlabs_ready": bool(self.elevenlabs_client),
            "browser_ready": True,  # Browser services are always available
            "framework": framework,
            "model_config": {
                "groq_model": self.config.groq_model,
                "tts_service": tts_service,
                "stt_service": "Browser Web Speech API",
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "enable_interruptions": self.config.enable_interruptions,
                "vad_enabled": self.config.vad_enabled
            }
        }