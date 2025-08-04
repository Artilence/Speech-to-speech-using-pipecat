"""
WebSocket Handler module
Handles WebSocket message processing and conversation flow
"""
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from ..models import MessageType, ConversationHistory, WebSocketMessage
from ..services import AIService, TTSService, WebSocketService
from ..config import config

class WebSocketHandler:
    """Handles WebSocket connections and message processing"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.tts_service = TTSService()
        self.websocket_service = WebSocketService()
        logger.info("WebSocket Handler initialized")
    
    async def handle_connection(self, websocket: WebSocket):
        """
        Handle a new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
        """
        # Create conversation history with system message
        conversation_history = ConversationHistory(config.get_system_message())
        
        # Connect client and get session
        session = await self.websocket_service.connect_client(websocket, conversation_history)
        
        try:
            # Send initial greeting
            await self.websocket_service.send_message(
                websocket, 
                MessageType.INFO, 
                "Connected! Click Start to begin voice conversation."
            )
            
            # Start message processing loop
            await self._message_processing_loop(websocket, session)
            
        except WebSocketDisconnect:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket handler: {e}")
            try:
                await self.websocket_service.send_message(
                    websocket, 
                    MessageType.ERROR, 
                    "Server error occurred"
                )
            except:
                pass
        finally:
            self.websocket_service.disconnect_client(websocket)
    
    async def _message_processing_loop(self, websocket: WebSocket, session):
        """
        Main message processing loop for a WebSocket session
        
        Args:
            websocket: The WebSocket connection
            session: The client session
        """
        while True:
            try:
                # Wait for message with timeout for keepalive
                data = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=config.websocket_timeout
                )
            except asyncio.TimeoutError:
                logger.debug("WebSocket timeout - sending keepalive")
                await self.websocket_service.send_message(websocket, MessageType.KEEPALIVE)
                continue
            
            try:
                # Parse message
                message_data = json.loads(data)
                message = WebSocketMessage(**message_data)
                
                # Process message based on type
                await self._process_message(websocket, session, message)
                
            except json.JSONDecodeError:
                await self.websocket_service.send_message(
                    websocket, 
                    MessageType.ERROR, 
                    "Invalid JSON received"
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self.websocket_service.send_message(
                    websocket, 
                    MessageType.ERROR, 
                    "Failed to process message"
                )
    
    async def _process_message(self, websocket: WebSocket, session, message: WebSocketMessage):
        """
        Process a specific message based on its type
        
        Args:
            websocket: The WebSocket connection
            session: The client session
            message: The parsed message
        """
        if message.type == MessageType.START_RECORDING:
            await self._handle_start_recording(websocket, session)
            
        elif message.type == MessageType.VOICE_CHUNK:
            await self._handle_voice_chunk(websocket, message.content)
            
        elif message.type == MessageType.STOP_RECORDING:
            await self._handle_stop_recording(websocket, session, message.content)
            
        elif message.type == MessageType.TEXT:
            await self._handle_text_message(websocket, session, message.content)
            
        elif message.type == MessageType.PING:
            await self._handle_ping(websocket)
            
        else:
            logger.warning(f"Unknown message type: {message.type}")
            await self.websocket_service.send_message(
                websocket, 
                MessageType.ERROR, 
                f"Unknown message type: {message.type}"
            )
    
    async def _handle_start_recording(self, websocket: WebSocket, session):
        """Handle start recording message"""
        logger.info("Voice recording started")
        session.is_recording = True
        await self.websocket_service.send_message(
            websocket, 
            MessageType.INFO, 
            "Listening... Speak now!"
        )
    
    async def _handle_voice_chunk(self, websocket: WebSocket, content: str):
        """Handle voice chunk message"""
        if content:
            await self.websocket_service.send_message(
                websocket, 
                MessageType.VOICE_CHUNK, 
                content
            )
    
    async def _handle_stop_recording(self, websocket: WebSocket, session, content: str):
        """Handle stop recording message"""
        session.is_recording = False
        transcribed_text = content.strip() if content else ""
        
        logger.info(f"Processing transcribed text: {transcribed_text}")
        
        if not transcribed_text:
            await self.websocket_service.send_message(
                websocket, 
                MessageType.ERROR, 
                "No speech detected. Please try again."
            )
            return
        
        await self._process_user_input(websocket, session, transcribed_text)
    
    async def _handle_text_message(self, websocket: WebSocket, session, content: str):
        """Handle text message"""
        if not content:
            return
        
        logger.debug(f"User text message: {content}")
        await self._process_user_input(websocket, session, content)
    
    async def _handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await self.websocket_service.send_message(websocket, MessageType.PONG)
    
    async def _process_user_input(self, websocket: WebSocket, session, user_input: str):
        """
        Process user input (from voice or text) and generate AI response
        
        Args:
            websocket: The WebSocket connection
            session: The client session
            user_input: The user's input text
        """
        try:
            await self.websocket_service.send_message(
                websocket, 
                MessageType.INFO, 
                "Processing your message..."
            )
            
            # Add user message to conversation
            session.conversation_history.add_user_message(user_input)
            
            # Get AI response
            messages = session.conversation_history.get_messages()
            response_text = await self.ai_service.get_response(messages)
            
            # Add AI response to conversation
            session.conversation_history.add_assistant_message(response_text)
            
            # Send text response
            await self.websocket_service.send_message(
                websocket, 
                MessageType.MESSAGE, 
                response_text
            )
            
            # Generate and send audio
            audio_data = await self.tts_service.synthesize_audio(response_text)
            if audio_data:
                await self.websocket_service.send_message(
                    websocket, 
                    MessageType.AUDIO, 
                    audio_data
                )
            else:
                await self.websocket_service.send_message(
                    websocket, 
                    MessageType.ERROR, 
                    "Audio synthesis failed"
                )
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            await self.websocket_service.send_message(
                websocket, 
                MessageType.ERROR, 
                "Failed to process your message. Please try again."
            )