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
            await websocket.send_json({
                "type": "info", 
                "content": "Connected! Click Start Recording to begin voice conversation or type a message."
            })
            
            # Start keepalive task
            keepalive_task = asyncio.create_task(self._keepalive_loop(websocket))
            
            # Start message processing loop
            await self._message_processing_loop(websocket, session)
            
        except WebSocketDisconnect:
            logger.info(f"Client disconnected: {session}")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket handler: {e}")
            try:
                await websocket.send_json({
                    "type": "error", 
                    "content": "Server error occurred"
                })
            except:
                pass
        finally:
            self.websocket_service.disconnect_client(websocket)
            keepalive_task.cancel()
    
    async def _keepalive_loop(self, websocket: WebSocket):
        """
        Send keepalive pings to maintain connection
        
        Args:
            websocket: The WebSocket connection
        """
        try:
            while True:
                await asyncio.sleep(config.keepalive_interval)
                if self.websocket_service.is_connected(websocket):
                    await websocket.ping()
        except asyncio.CancelledError:
            logger.debug("Keepalive task cancelled")
        except Exception as e:
            logger.warning(f"Keepalive error: {e}")
    
    async def _message_processing_loop(self, websocket: WebSocket, session):
        """
        Main message processing loop for a WebSocket session
        
        Args:
            websocket: The WebSocket connection
            session: The client session
        """
        while True:
            try:
                # Wait for message
                data = await websocket.receive_text()
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {e}")
                break
            
            try:
                # Parse message
                message_data = json.loads(data)
                message = WebSocketMessage(**message_data)
                
                # Process message based on type
                await self._process_message(websocket, session, message)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error", 
                    "content": "Invalid JSON received"
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error", 
                    "content": "Failed to process message"
                })
    
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
    
    async def _handle_start_recording(self, websocket: WebSocket, session):
        """Handle start recording message"""
        logger.info(f"Voice recording started for session: {session}")
        session.is_recording = True
        # No response needed - handled by frontend
    
    async def _handle_voice_chunk(self, websocket: WebSocket, content: str):
        """Handle voice chunk message - echo back for real-time display"""
        if content:
            await websocket.send_json({
                "type": "voice_chunk", 
                "content": content
            })
    
    async def _handle_stop_recording(self, websocket: WebSocket, session, content: str):
        """Handle stop recording message and process transcribed text"""
        session.is_recording = False
        transcribed_text = content.strip() if content else ""
        
        logger.info(f"Processing transcribed text for session {session}: {transcribed_text}")
        
        if not transcribed_text:
            await websocket.send_json({
                "type": "error", 
                "content": "No speech detected. Please try again."
            })
            return
        
        await self._process_user_input(websocket, session, transcribed_text)
    
    async def _handle_text_message(self, websocket: WebSocket, session, content: str):
        """Handle text message input"""
        if not content or not content.strip():
            return
        
        user_text = content.strip()
        logger.debug(f"User text message for session {session}: {user_text}")
        await self._process_user_input(websocket, session, user_text)
    
    async def _handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await websocket.send_json({"type": "pong"})
    
    async def _process_user_input(self, websocket: WebSocket, session, user_input: str):
        """
        Process user input (from voice or text) and generate AI response
        
        Args:
            websocket: The WebSocket connection
            session: The client session
            user_input: The user's input text
        """
        try:
            # Get AI response using conversation history
            conversation_messages = session.conversation_history.get_messages_dict()
            response_text = await self.ai_service.process_with_conversation_history(
                user_input, 
                conversation_messages
            )
            
            # Add messages to conversation history
            session.conversation_history.add_user_message(user_input)
            session.conversation_history.add_assistant_message(response_text)
            
            # Send text response
            await websocket.send_json({
                "type": "message", 
                "content": response_text
            })
            
            # Generate and send audio
            audio_data = await self.tts_service.synthesize_audio(response_text)
            if audio_data:
                await websocket.send_json({
                    "type": "audio", 
                    "content": audio_data
                })
            else:
                await websocket.send_json({
                    "type": "error", 
                    "content": "Audio synthesis failed"
                })
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            await websocket.send_json({
                "type": "error", 
                "content": "Failed to process your message. Please try again."
            })
    
    def get_websocket_service(self) -> WebSocketService:
        """Get the WebSocket service for external access"""
        return self.websocket_service