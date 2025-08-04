"""
Audio Streaming module
Handles ElevenLabs WebSocket streaming and audio chunk management
"""
import asyncio
import json
import base64
import time
import logging
import websockets
from fastapi import WebSocket
try:
    from .config import config
    from .websocket_manager import WebSocketManager
except ImportError:
    from config import config
    from websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class AudioStreamingService:
    """Service for handling audio streaming with ElevenLabs"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
    
    async def stream_text_to_speech(
        self, 
        text: str, 
        client_id: str, 
        openai_latency: float, 
        request_start_time: float = None
    ) -> None:
        """
        Convert text to speech using ElevenLabs WebSocket streaming for ultra-low latency
        
        Args:
            text: Text to convert to speech
            client_id: Client ID for WebSocket communication
            openai_latency: Latency from OpenAI API call
            request_start_time: Original request start time for total latency calculation
        """
        try:
            tts_start_time = time.time()
            if request_start_time is None:
                request_start_time = tts_start_time
            
            # WebSocket URI for streaming
            uri = (f"wss://api.elevenlabs.io/v1/text-to-speech/{config.voice_id}/"
                   f"stream-input?model_id={config.model_id}&inactivity_timeout=180")
            
            async with websockets.connect(uri) as elevenlabs_ws:
                connection_time = time.time()
                websocket_connection_latency = (connection_time - tts_start_time) * 1000
                logger.info(f"ElevenLabs WebSocket connection latency: {websocket_connection_latency:.2f}ms")
                
                # Send initial configuration with optimized settings for low latency
                await elevenlabs_ws.send(json.dumps({
                    "text": " ",  # Initial space to establish connection
                    "voice_settings": config.get_voice_settings(),
                    "generation_config": config.get_generation_config(),
                    "xi_api_key": config.elevenlabs_api_key,
                }))
                
                # Create timing context for audio generation
                timing_context = {
                    "tts_start_time": tts_start_time,
                    "connection_time": connection_time,
                    "websocket_connection_latency": websocket_connection_latency,
                    "openai_latency": openai_latency,
                    "first_chunk_received": False,
                    "request_start_time": request_start_time
                }
                
                # Create tasks for sending text and receiving audio
                send_task = asyncio.create_task(self._send_text_to_elevenlabs(elevenlabs_ws, text))
                receive_task = asyncio.create_task(
                    self._receive_audio_from_elevenlabs(elevenlabs_ws, client_id, timing_context)
                )
                
                # Wait for both tasks to complete
                await asyncio.gather(send_task, receive_task)
                
        except Exception as e:
            logger.error(f"Error in WebSocket text-to-speech streaming: {e}")
            await self.websocket_manager.send_message({
                "type": "error",
                "message": "Failed to generate audio response"
            }, client_id)
    
    async def _send_text_to_elevenlabs(self, elevenlabs_ws, text: str) -> None:
        """Send text to ElevenLabs WebSocket in chunks"""
        try:
            # Send the text in chunks for streaming
            text_chunks = [text[i:i+config.chunk_size] for i in range(0, len(text), config.chunk_size)]
            
            for chunk in text_chunks:
                await elevenlabs_ws.send(json.dumps({
                    "text": chunk,
                    "flush": len(chunk) < config.chunk_size  # Flush on last chunk
                }))
                await asyncio.sleep(config.chunk_delay)  # Small delay between chunks
            
            # Send empty string to indicate end of text and close connection
            await elevenlabs_ws.send(json.dumps({"text": ""}))
            
        except Exception as e:
            logger.error(f"Error sending text to ElevenLabs: {e}")
    
    async def _receive_audio_from_elevenlabs(
        self, 
        elevenlabs_ws, 
        client_id: str, 
        timing_context: dict
    ) -> None:
        """Receive audio chunks from ElevenLabs and stream to client with timing measurements"""
        try:
            audio_chunks = []
            
            while True:
                try:
                    message = await elevenlabs_ws.recv()
                    data = json.loads(message)
                    
                    if data.get("audio"):
                        current_time = time.time()
                        
                        # Decode audio chunk
                        audio_chunk = base64.b64decode(data["audio"])
                        audio_chunks.append(audio_chunk)
                        
                        # Calculate time to first chunk if this is the first audio
                        if not timing_context["first_chunk_received"]:
                            timing_context["first_chunk_received"] = True
                            time_to_first_chunk = (current_time - timing_context["tts_start_time"]) * 1000
                            total_round_trip = (current_time - timing_context["request_start_time"]) * 1000
                            
                            logger.info(f"Time to first audio chunk: {time_to_first_chunk:.2f}ms")
                            logger.info(f"Total round-trip time: {total_round_trip:.2f}ms")
                            
                            # Send latency measurements to client
                            await self.websocket_manager.send_message({
                                "type": "latency_measurement",
                                "openai_latency": timing_context["openai_latency"],
                                "websocket_connection_latency": timing_context["websocket_connection_latency"],
                                "time_to_first_chunk": time_to_first_chunk,
                                "total_round_trip": total_round_trip
                            }, client_id)
                        
                        # Stream individual chunks to client for real-time playback
                        await self.websocket_manager.send_message({
                            "type": "audio_chunk",
                            "audio": data["audio"],  # Send base64 encoded chunk
                            "is_final": False
                        }, client_id)
                        
                    elif data.get('isFinal'):
                        # Send final message with complete audio
                        complete_audio = b''.join(audio_chunks)
                        audio_base64 = base64.b64encode(complete_audio).decode('utf-8')
                        
                        total_generation_time = (time.time() - timing_context["tts_start_time"]) * 1000
                        logger.info(f"Total audio generation time: {total_generation_time:.2f}ms")
                        
                        await self.websocket_manager.send_message({
                            "type": "audio_response",
                            "audio": audio_base64,
                            "is_final": True,
                            "total_generation_time": total_generation_time
                        }, client_id)
                        break
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info("ElevenLabs WebSocket connection closed")
                    break
                    
        except Exception as e:
            logger.error(f"Error receiving audio from ElevenLabs: {e}")