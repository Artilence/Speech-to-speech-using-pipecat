"""
AI Service module for OpenAI integration
Handles conversation with OpenAI's language models
"""
import openai
from typing import List, Dict
from loguru import logger

from ..config import config

class AIService:
    """Service for handling AI conversations with OpenAI"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        logger.info("AI Service initialized with OpenAI client")
    
    async def get_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get response from OpenAI language model
        
        Args:
            messages: List of conversation messages in OpenAI format
            
        Returns:
            AI response text
            
        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            logger.debug(f"Sending {len(messages)} messages to OpenAI API")
            
            response = await self.client.chat.completions.create(
                model=config.ai_model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            
            ai_response = response.choices[0].message.content
            logger.debug(f"Received response from OpenAI: {ai_response[:100]}...")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")
    
    async def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key by making a test request
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False