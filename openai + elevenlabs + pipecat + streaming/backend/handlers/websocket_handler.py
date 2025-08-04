"""
WebSocket Handler
Handles WebSocket connections and message processing for voice chat
"""

import json
import time
import asyncio
from typing import Optional, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from ..services.openai_service import OpenAIService
from ..services.elevenlabs_service import ElevenLabsService
from ..services.pipecat_service import PipecatService
from ..utils.speech_buffer import ConversationHistory


class WebSocketHandler:
    """Handles WebSocket connections for voice chat streaming"""
    
    def __init__(
        self, 
        openai_service: OpenAIService,
        elevenlabs_service: ElevenLabsService,
        pipecat_service: Optional[PipecatService] = None
    ):
        self.openai_service = openai_service
        self.elevenlabs_service = elevenlabs_service
        self.pipecat_service = pipecat_service
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle a new WebSocket connection"""
        await websocket.accept()
        session_id = f"session_{id(websocket)}"
        
        # Initialize session data
        self.active_sessions[session_id] = {
            "websocket": websocket,
            "conversation_history": ConversationHistory(),
            "created_at": time.time()
        }
        
        try:
            logger.info(f"Starting streaming session: {session_id}")
            
            # Try to create pipeline if Pipecat is available
            pipeline = None
            if self.pipecat_service and self.pipecat_service.check_availability():
                pipeline = await self.pipecat_service.create_streaming_pipeline(session_id, websocket)
            
            if pipeline is None:
                # Use simple implementation 
                await websocket.send_json({
                    "type": "system", 
                    "content": "📞 Ready for voice call - click the call button to start!"
                })
                await self._simple_voice_call_handler(websocket, session_id)
            else:
                # Use advanced pipeline (currently not implemented)
                logger.info("Advanced pipeline mode would be used here")
                await self._simple_voice_call_handler(websocket, session_id)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error in session {session_id}: {e}")
        finally:
            await self._cleanup_session(session_id)
    
    async def _simple_voice_call_handler(self, websocket: WebSocket, session_id: str):
        """Simple voice call handler - process text from browser speech recognition"""
        
        logger.info(f"🎯 Voice call handler started for session: {session_id}")
        conversation_history = self.active_sessions[session_id]["conversation_history"]
        
        try:
            while True:
                try:
                    # Track message reception latency
                    msg_start_time = time.time()
                    data = await websocket.receive_text()
                    msg_receive_time = time.time()
                    logger.info(f"WebSocket message received in {(msg_receive_time - msg_start_time)*1000:.2f}ms")
                    
                    message = json.loads(data)
                    
                    if message["type"] == "user_speech":
                        await self._process_user_speech(
                            websocket, 
                            message["content"], 
                            conversation_history,
                            session_id
                        )
                    
                except asyncio.TimeoutError:
                    await websocket.ping()
                    logger.debug("WebSocket ping sent")
                    
        except WebSocketDisconnect:
            logger.info(f"📞 Call ended - WebSocket disconnected: {session_id}")
        except Exception as e:
            logger.error(f"❌ Call handler error for {session_id}: {e}")
        finally:
            logger.info(f"🎯 Voice call handler ended for session: {session_id}")
    
    async def _process_user_speech(
        self, 
        websocket: WebSocket, 
        user_text: str, 
        conversation_history: ConversationHistory,
        session_id: str
    ):
        """Process user speech and generate AI response"""
        try:
            process_start_time = time.time()
            user_text = user_text.strip()
            
            if not user_text:
                logger.info("🔇 Empty speech received")
                return
            
            logger.info(f"✅ User said: '{user_text}'")
            logger.info(f"Processing user speech: '{user_text[:50]}...' (len: {len(user_text)})")
            
            # Get AI response using the fast method
            await self._get_ai_response_fast(
                user_text, 
                websocket, 
                conversation_history,
                session_id
            )
            
            process_end_time = time.time()
            total_process_time = (process_end_time - process_start_time) * 1000
            logger.info(f"TOTAL processing time for user input: {total_process_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Speech processing error for {session_id}: {e}")
            await websocket.send_json({
                "type": "error",
                "content": f"Speech processing failed: {str(e)}"
            })
    
    async def _get_ai_response_fast(
        self, 
        user_text: str, 
        websocket: WebSocket, 
        conversation_history: ConversationHistory,
        session_id: str
    ):
        """Get AI response optimized for ULTRA LOW LATENCY"""
        try:
            ai_start_time = time.time()
            logger.info(f"🤖 Getting AI response for: '{user_text}' in session {session_id}")
            
            # Send typing indicator
            typing_time = time.time()
            await websocket.send_json({
                "type": "ai_typing",
                "content": "AI is thinking..."
            })
            logger.info(f"Typing indicator sent in {(typing_time - ai_start_time)*1000:.2f}ms")
            
            response_text = ""
            first_chunk_time = None
            
            # Send initial message container
            await websocket.send_json({
                "type": "ai_response_start",
                "content": ""
            })
            
            # Process streaming response
            chunk_count = 0
            async for chunk in self.openai_service.get_fast_response(user_text, use_conversation_history=False):
                chunk_time = time.time()
                if first_chunk_time is None:
                    first_chunk_time = chunk_time
                    logger.info(f"First AI chunk received in {(first_chunk_time - typing_time)*1000:.2f}ms")
                
                response_text += chunk
                chunk_count += 1
                
                # Send chunk for real-time display
                await websocket.send_json({
                    "type": "ai_chunk",
                    "content": chunk,
                    "full_text": response_text
                })
            
            # Generate audio for complete response
            if response_text.strip():
                audio_start_time = time.time()
                logger.info(f"Starting ElevenLabs Flash synthesis for complete response: '{response_text.strip()[:30]}...'")
                
                audio_b64 = await self.elevenlabs_service.synthesize_audio_flash(response_text.strip())
                audio_end_time = time.time()
                audio_duration = (audio_end_time - audio_start_time) * 1000
                logger.info(f"ElevenLabs synthesis completed in {audio_duration:.2f}ms")
                
                if audio_b64:
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "content": audio_b64,
                        "text": response_text.strip()
                    })
                    logger.info("Audio chunk sent to client")
            
            # Send final response
            final_time = time.time()
            await websocket.send_json({
                "type": "ai_response_complete",
                "content": response_text
            })
            
            # Add to conversation history (optional for speed optimization)
            # conversation_history.add_message("user", user_text)
            # conversation_history.add_message("assistant", response_text)
            
            # Print comprehensive timing summary
            total_ai_time = (final_time - ai_start_time) * 1000
            logger.info(f"=== ULTRA-FAST AI RESPONSE TIMING ===")
            logger.info(f"Total AI processing time: {total_ai_time:.2f}ms")
            logger.info(f"Total chunks processed: {chunk_count}")
            logger.info(f"Response length: {len(response_text)} chars")
            logger.info(f"=== END TIMING SUMMARY ===")
            
            logger.info(f"✅ AI response complete: '{response_text}'")
            logger.info("🎯 Ready for next user input")
            
        except Exception as e:
            logger.error(f"❌ AI response error for {session_id}: {e}")
            await websocket.send_json({
                "type": "error",
                "content": f"Failed to get AI response: {str(e)}"
            })
    
    async def _cleanup_session(self, session_id: str):
        """Clean up session resources"""
        try:
            if session_id in self.active_sessions:
                # Clean up Pipecat pipeline if it exists
                if self.pipecat_service:
                    await self.pipecat_service.cleanup_pipeline(session_id)
                
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up session: {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    def get_active_sessions(self) -> list:
        """Get list of active session IDs"""
        return list(self.active_sessions.keys())
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_sessions)
    
    async def broadcast_message(self, message: dict):
        """Broadcast a message to all active sessions"""
        disconnected_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            try:
                websocket = session_data["websocket"]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send broadcast to {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            await self._cleanup_session(session_id)