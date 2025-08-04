"""
Voice call handler for processing voice interactions
"""

import asyncio
from typing import Dict, Any

from ..models.message_models import MessageType, ConversationMessage
from ..models.session_models import SessionState
from ..services.websocket_service import WebSocketService
from ..services.llm_service import LLMService
from ..services.audio_service import AudioService
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class VoiceCallHandler:
    """Handler for voice call interactions"""
    
    def __init__(self, websocket_service: WebSocketService, 
                 llm_service: LLMService, audio_service: AudioService):
        self.websocket_service = websocket_service
        self.llm_service = llm_service
        self.audio_service = audio_service
        
    async def handle_voice_session(self, session_id: str):
        """
        Main handler for voice call session
        
        Args:
            session_id: Session to handle
        """
        logger.info(f"🎯 Voice call handler started for {session_id}")
        
        try:
            while True:
                # Receive message from client
                message = await self.websocket_service.receive_message(session_id)
                if message is None:
                    break
                    
                # Process different message types
                await self.process_message(session_id, message)
                    
        except Exception as e:
            logger.error(f"❌ Voice call handler error for {session_id}: {e}")
            await self.websocket_service.broadcast_to_session(
                session_id, MessageType.ERROR, 
                f"Voice call error: {str(e)}"
            )
        finally:
            logger.info(f"🎯 Voice call handler ended for {session_id}")
    
    async def process_message(self, session_id: str, message: Dict[str, Any]):
        """
        Process incoming message from client
        
        Args:
            session_id: Source session
            message: Message data
        """
        message_type = message.get("type")
        content = message.get("content", "")
        
        if message_type == "user_speech":
            await self.handle_user_speech(session_id, content)
        else:
            logger.warning(f"⚠️  Unknown message type: {message_type}")
    
    async def handle_user_speech(self, session_id: str, user_text: str):
        """
        Handle user speech input
        
        Args:
            session_id: Source session
            user_text: Transcribed user speech
        """
        try:
            user_text = user_text.strip()
            if not user_text:
                logger.info("🔇 Empty speech received")
                return
                
            logger.info(f"✅ User said: '{user_text}'")
            
            # Get session and add user message to history
            session = self.websocket_service.get_session(session_id)
            if not session:
                logger.error(f"❌ Session not found: {session_id}")
                return
                
            session.add_message("user", user_text)
            
            # Update session state
            self.websocket_service.update_session_state(session_id, SessionState.PROCESSING)
            
            # Send typing indicator
            await self.websocket_service.broadcast_to_session(
                session_id, MessageType.AI_TYPING, "AI is thinking..."
            )
            
            # Get AI response
            await self.get_ai_response(session_id, user_text, session.conversation_history)
            
            # Update session state back to on call
            self.websocket_service.update_session_state(session_id, SessionState.ON_CALL)
            
        except Exception as e:
            logger.error(f"❌ Speech processing error: {e}")
            await self.websocket_service.broadcast_to_session(
                session_id, MessageType.ERROR,
                f"Speech processing failed: {str(e)}"
            )
    
    async def get_ai_response(self, session_id: str, user_text: str, 
                            conversation_history: list):
        """
        Get AI response and stream it back
        
        Args:
            session_id: Target session
            user_text: User's input
            conversation_history: Previous conversation
        """
        try:
            logger.info(f"🤖 Getting AI response for: '{user_text}'")
            
            # Send response start indicator
            await self.websocket_service.broadcast_to_session(
                session_id, MessageType.AI_RESPONSE_START, ""
            )
            
            response_text = ""
            current_sentence = ""
            
            # Get streaming response from LLM
            async for chunk in self.llm_service.get_streaming_response(
                user_text, conversation_history
            ):
                response_text += chunk
                current_sentence += chunk
                
                # Send chunk for real-time display
                await self.websocket_service.broadcast_to_session(
                    session_id, MessageType.AI_CHUNK, chunk,
                    full_text=response_text
                )
                
                # Check if we have a complete sentence for audio synthesis
                if any(ending in current_sentence for ending in {'.', '!', '?', '。', '！', '？'}):
                    # Generate audio for this sentence
                    await self.synthesize_and_send_audio(
                        session_id, current_sentence.strip()
                    )
                    current_sentence = ""
            
            # Handle any remaining text
            if current_sentence.strip():
                await self.synthesize_and_send_audio(
                    session_id, current_sentence.strip()
                )
            
            # Add AI response to conversation history
            session = self.websocket_service.get_session(session_id)
            if session:
                session.add_message("assistant", response_text)
            
            # Send completion signal
            await self.websocket_service.broadcast_to_session(
                session_id, MessageType.AI_RESPONSE_COMPLETE, response_text
            )
            
            logger.info(f"✅ AI response complete: '{response_text}'")
            logger.info("🎯 Ready for next user input")
            
        except Exception as e:
            logger.error(f"❌ AI response error: {e}")
            await self.websocket_service.broadcast_to_session(
                session_id, MessageType.ERROR,
                f"Failed to get AI response: {str(e)}"
            )
    
    async def synthesize_and_send_audio(self, session_id: str, text: str):
        """
        Synthesize audio and send to client
        
        Args:
            session_id: Target session
            text: Text to synthesize
        """
        try:
            audio_b64 = await self.audio_service.synthesize_speech(text)
            if audio_b64:
                await self.websocket_service.broadcast_to_session(
                    session_id, MessageType.AUDIO_CHUNK, audio_b64,
                    text=text
                )
        except Exception as e:
            logger.error(f"❌ Audio synthesis error: {e}")
    
    async def handle_ping(self, session_id: str):
        """Handle periodic ping to keep connection alive"""
        try:
            await self.websocket_service.ping_session(session_id)
        except Exception as e:
            logger.error(f"❌ Ping error for {session_id}: {e}")