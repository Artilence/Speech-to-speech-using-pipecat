"""
Voice service integrating Groq LLM (Browser TTS used for speech)
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any

from groq import AsyncGroq

from .config_service import ConfigService

logger = logging.getLogger(__name__)


class VoiceService:
    """Core voice service managing LLM and TTS interactions"""
    
    def __init__(self, config_service: ConfigService):
        self.config = config_service
        self.groq_client = None
        self.session_contexts: Dict[str, dict] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients"""
        try:
            # Initialize Groq client
            groq_config = self.config.get_groq_config()
            self.groq_client = AsyncGroq(api_key=groq_config["api_key"])
            
            logger.info("✅ Voice service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize voice service: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if the voice service is ready"""
        return bool(self.groq_client and self.config.is_ready())
    
    async def generate_response(
        self, 
        user_input: str, 
        conversation_history: List[dict],
        session_id: str
    ) -> dict:
        """Generate AI response using Groq LLM"""
        start_time = time.time()
        
        try:
            # Prepare conversation context
            messages = self._prepare_conversation_context(user_input, conversation_history)
            
            logger.debug(f"🤖 Generating response for: {user_input[:50]}...")
            
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
            llm_latency = (time.time() - start_time) * 1000
            
            logger.info(f"🤖 LLM response ({llm_latency:.2f}ms): {ai_text[:100]}...")
            
            return {
                "text": ai_text,
                "llm_latency": llm_latency,
                "model_used": groq_config["model"],
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating LLM response: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _prepare_conversation_context(
        self, 
        user_input: str, 
        conversation_history: List[dict]
    ) -> List[dict]:
        """Prepare conversation context for the LLM"""
        
        # System prompt for voice assistant
        system_prompt = """You are a helpful AI voice assistant. Provide clear, concise, and natural-sounding responses that are suitable for text-to-speech conversion. 

Guidelines:
- Keep responses conversational and engaging
- Avoid overly technical language unless specifically asked
- Use natural speech patterns
- Keep responses reasonably brief (1-3 sentences typically)
- Show personality while being helpful
- If you don't know something, admit it honestly

You are designed for real-time voice conversations, so make your responses flow naturally when spoken aloud."""

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
    

    async def cleanup_session(self, session_id: str):
        """Clean up session-specific resources"""
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
            logger.debug(f"🧹 Cleaned up voice service session: {session_id}")
    
    def get_session_info(self, session_id: str) -> dict:
        """Get information about a session"""
        return self.session_contexts.get(session_id, {})
    
    def get_service_stats(self) -> dict:
        """Get service statistics"""
        return {
            "active_sessions": len(self.session_contexts),
            "groq_ready": bool(self.groq_client),
            "tts_type": "browser",
            "model_config": {
                "groq_model": self.config.groq_model,
                "tts": "Browser Web Speech API",
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
        }