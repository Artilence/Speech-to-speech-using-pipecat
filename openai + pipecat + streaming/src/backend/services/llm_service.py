"""
Large Language Model service for AI responses
"""

from typing import List, Dict, Any, AsyncIterator, Optional
from openai import AsyncOpenAI

from ..models.message_models import ConversationMessage
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", 
                 max_tokens: int = 150, temperature: float = 0.7):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # System prompt for voice conversations
        self.system_prompt = (
            "You are a helpful AI assistant in a voice call. "
            "Keep responses conversational and concise (1-2 sentences max). "
            "Speak naturally as if you're having a real conversation."
        )
        
    async def get_streaming_response(
        self, 
        user_message: str, 
        conversation_history: List[ConversationMessage]
    ) -> AsyncIterator[str]:
        """
        Get streaming response from LLM
        
        Args:
            user_message: User's input message
            conversation_history: Previous conversation messages
            
        Yields:
            Chunks of AI response text
        """
        try:
            logger.info(f"🤖 Getting AI response for: '{user_message}'")
            
            # Prepare messages for OpenAI API
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history (limit to last 10 messages)
            recent_messages = conversation_history[-10:]
            for msg in recent_messages:
                messages.append(msg.to_openai_format())
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Create streaming chat completion
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            # Process streaming response
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
                    
        except Exception as e:
            logger.error(f"❌ LLM streaming error: {e}")
            yield f"I apologize, but I encountered an error: {str(e)}"
    
    async def get_complete_response(
        self, 
        user_message: str, 
        conversation_history: List[ConversationMessage]
    ) -> str:
        """
        Get complete response from LLM (non-streaming)
        
        Args:
            user_message: User's input message
            conversation_history: Previous conversation messages
            
        Returns:
            Complete AI response text
        """
        try:
            logger.info(f"🤖 Getting complete AI response for: '{user_message}'")
            
            # Prepare messages for OpenAI API
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history (limit to last 10 messages)
            recent_messages = conversation_history[-10:]
            for msg in recent_messages:
                messages.append(msg.to_openai_format())
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Create chat completion
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            result = response.choices[0].message.content
            logger.info(f"✅ AI response complete: '{result}'")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM error: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def update_system_prompt(self, new_prompt: str):
        """Update the system prompt for the AI assistant"""
        self.system_prompt = new_prompt
        logger.info(f"Updated system prompt: {new_prompt[:100]}...")
    
    def update_model_params(self, model: Optional[str] = None, 
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None):
        """Update model parameters"""
        if model:
            self.model = model
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
            
        logger.info(f"Updated model params: {self.model}, tokens={self.max_tokens}, temp={self.temperature}")