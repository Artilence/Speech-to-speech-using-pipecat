"""
AI Service module for OpenAI integration
Handles conversation management and AI response generation
"""
import asyncio
import time
import logging
from typing import Tuple
try:
    from .config import config
except ImportError:
    from config import config

logger = logging.getLogger(__name__)

class AIService:
    """Service for handling AI conversations with OpenAI"""
    
    def __init__(self):
        self.client = config.get_openai_client()
    
    async def get_response(self, user_input: str, conversation_history: list) -> Tuple[str, float]:
        """
        Get AI response from OpenAI and return response with timing
        
        Args:
            user_input: The user's input text
            conversation_history: Current conversation history
            
        Returns:
            Tuple of (ai_response, latency_ms)
        """
        try:
            openai_start_time = time.time()
            
            # Add user message to conversation
            messages = conversation_history + [{"role": "user", "content": user_input}]
            
            # Get AI response
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=config.ai_model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            openai_end_time = time.time()
            openai_latency = (openai_end_time - openai_start_time) * 1000  # Convert to milliseconds
            
            ai_response = response.choices[0].message.content.strip()
            
            logger.info(f"OpenAI API latency: {openai_latency:.2f}ms")
            return ai_response, openai_latency
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "I'm sorry, I'm having trouble processing your request right now.", 0.0