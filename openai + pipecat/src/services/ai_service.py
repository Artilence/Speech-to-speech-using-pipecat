"""
AI Service module for OpenAI + Pipecat integration
Handles conversation with OpenAI's language models using Pipecat
"""
from typing import List, Dict
from loguru import logger
from openai import AsyncOpenAI

from pipecat.services.openai import OpenAILLMService
from ..config import config

class AIService:
    """Service for handling AI conversations with OpenAI via Pipecat"""
    
    def __init__(self):
        self.config = config
        self.llm_service = None
        self.openai_client = None
        self._initialize_services()
        logger.info("AI Service initialized with OpenAI and Pipecat")
    
    def _initialize_services(self):
        """Initialize OpenAI and Pipecat services"""
        try:
            # Create Pipecat OpenAI LLM service
            self.llm_service = OpenAILLMService(
                api_key=self.config.openai_api_key,
                model=self.config.ai_model
            )
            
            # Create direct OpenAI client for chat completions
            self.openai_client = AsyncOpenAI(api_key=self.config.openai_api_key)
            
            logger.info(f"Initialized AI services with model: {self.config.ai_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}")
            raise
    
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
            
            # Use direct OpenAI client for more control
            # The pipecat service can be used for more complex pipeline scenarios
            client = self.openai_client
            
            # If pipecat service has internal client access, use it
            if hasattr(self.llm_service, '_client') and self.llm_service._client:
                client = self.llm_service._client
            
            # Make the chat completion call
            chat_completion = await client.chat.completions.create(
                model=self.config.ai_model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            response_text = chat_completion.choices[0].message.content
            
            if not response_text:
                response_text = "I'm sorry, I couldn't generate a response. Please try again."
            
            logger.debug(f"Received response from OpenAI: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "I'm having trouble processing your request right now. Please try again."
    
    async def process_with_conversation_history(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Process user message with conversation history
        
        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            AI response text
        """
        try:
            logger.info(f"Processing message with pipecat: {user_message}")
            
            # Create complete message list including history
            all_messages = list(conversation_history)  # Copy existing history
            all_messages.append({"role": "user", "content": user_message})
            
            # Get response using the AI service
            response_text = await self.get_response(all_messages)
            
            logger.info(f"LLM Response: {response_text}")
            return response_text
            
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return "I'm having trouble processing your request right now. Please try again."
    
    async def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key by making a test request
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=test_messages,
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def get_llm_service(self) -> OpenAILLMService:
        """Get the Pipecat LLM service for advanced use cases"""
        return self.llm_service