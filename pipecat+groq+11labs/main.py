"""
Real-time Voice Agent using Pipecat + Groq LLM + Google TTS/STT
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from pipecat.frames.frames import (
    AudioRawFrame,
    TextFrame,
    LLMMessagesFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    TranscriptionFrame
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask

from services.voice_service import VoicePipelineService
from services.websocket_service import WebSocketManager
from services.config_service import ConfigService
from utils.latency_logger import LatencyLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
app = FastAPI(title="Pipecat Voice Agent API", version="1.0.0")
config_service = ConfigService()
websocket_manager = WebSocketManager()
voice_pipeline_service = VoicePipelineService(config_service)
latency_logger = LatencyLogger()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Session storage
active_sessions: Dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Serve the main HTML page"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend not found</h1><p>Please ensure static/index.html exists</p>",
            status_code=404
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "groq": bool(config_service.groq_api_key),
            "browser_tts": True,  # Browser TTS is always available
            "browser_stt": True,  # Browser STT is always available
            "pipecat": voice_pipeline_service.is_ready()
        }
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint for voice interactions"""
    await websocket_manager.connect(websocket, session_id)
    
    # Initialize session
    active_sessions[session_id] = {
        "connected_at": time.time(),
        "conversation_history": [],
        "total_interactions": 0,
        "session_info": None
    }
    
    logger.info(f"🎯 New pipecat voice session started: {session_id}")
    
    try:
        await handle_voice_session(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"📞 Session ended: {session_id}")
    except Exception as e:
        logger.error(f"❌ Session error {session_id}: {e}")
    finally:
        await cleanup_session(session_id)


async def handle_voice_session(websocket: WebSocket, session_id: str):
    """Handle the voice interaction session with pipecat pipeline"""
    session = active_sessions[session_id]
    
    # Initialize pipecat session for this session
    try:
        session_info = await voice_pipeline_service.create_session_pipeline(
            session_id, 
            websocket_manager
        )
        session["session_info"] = session_info
        
        logger.info(f"✅ Pipecat session initialized for session: {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize session for {session_id}: {e}")
        await websocket_manager.send_to_session(session_id, {
            "type": "error",
            "message": f"Failed to initialize voice session: {str(e)}"
        })
        return
    
    while True:
        try:
            # Track message receive latency
            msg_start = time.time()
            data = await websocket.receive_text()
            msg_received = time.time()
            
            message = json.loads(data)
            message_type = message.get("type")
            
            latency_logger.log_latency(
                session_id, 
                "websocket_receive", 
                (msg_received - msg_start) * 1000
            )
            
            logger.info(f"📨 Received {message_type} from {session_id}")
            
            if message_type == "user_speech":
                await handle_user_speech(websocket, session_id, message)
            elif message_type == "audio_chunk":
                await handle_audio_chunk(websocket, session_id, message)
            elif message_type == "start_recording":
                await handle_start_recording(websocket, session_id)
            elif message_type == "stop_recording":
                await handle_stop_recording(websocket, session_id)
            elif message_type == "ping":
                await handle_ping(websocket, session_id)
            elif message_type == "get_stats":
                await handle_stats_request(websocket, session_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except asyncio.TimeoutError:
            await websocket.ping()
            logger.debug(f"Ping sent to {session_id}")


async def handle_user_speech(websocket: WebSocket, session_id: str, message: dict):
    """Process user speech through pipecat pipeline"""
    request_start = time.time()
    user_text = message.get("content", "").strip()
    
    if not user_text:
        logger.warning(f"Empty speech content from {session_id}")
        return
    
    session = active_sessions[session_id]
    session["total_interactions"] += 1
    
    # Add to conversation history
    session["conversation_history"].append({
        "role": "user",
        "content": user_text,
        "timestamp": request_start
    })
    
    logger.info(f"🎤 User ({session_id}): {user_text}")
    
    # Send processing acknowledgment
    await websocket_manager.send_to_session(session_id, {
        "type": "processing",
        "message": "Processing your request...",
        "request_id": str(uuid.uuid4())
    })
    
    try:
        # Process through pipecat pipeline
        response_data = await voice_pipeline_service.process_user_input(
            session_id,
            user_text,
            session["conversation_history"]
        )
        
        # Add AI response to conversation history
        session["conversation_history"].append({
            "role": "assistant", 
            "content": response_data["text"],
            "timestamp": time.time()
        })
        
        # Send text response
        await websocket_manager.send_to_session(session_id, {
            "type": "ai_response",
            "text": response_data["text"],
            "latency": response_data.get("llm_latency", 0)
        })
        
        # Send audio data if available
        if "audio_data" in response_data:
            await websocket_manager.send_to_session(session_id, {
                "type": "audio_response",
                "audio_data": response_data["audio_data"],
                "audio_format": response_data.get("audio_format", "wav")
            })
        
        # Log end-to-end latency
        total_latency = (time.time() - request_start) * 1000
        latency_logger.log_latency(session_id, "total_request", total_latency)
        
        logger.info(f"✅ Response completed for {session_id} in {total_latency:.2f}ms")
        
    except Exception as e:
        logger.error(f"❌ Error processing speech for {session_id}: {e}")
        await websocket_manager.send_to_session(session_id, {
            "type": "error",
            "message": f"Error processing request: {str(e)}"
        })


async def handle_audio_chunk(websocket: WebSocket, session_id: str, message: dict):
    """Handle incoming audio chunk from client"""
    try:
        audio_data = message.get("audio_data")
        if not audio_data:
            return
            
        # Process audio through pipecat pipeline
        await voice_pipeline_service.process_audio_chunk(session_id, audio_data)
        
    except Exception as e:
        logger.error(f"❌ Error processing audio chunk for {session_id}: {e}")


async def handle_start_recording(websocket: WebSocket, session_id: str):
    """Handle start recording request"""
    try:
        await voice_pipeline_service.start_recording(session_id)
        await websocket_manager.send_to_session(session_id, {
            "type": "recording_started",
            "message": "Recording started"
        })
        
    except Exception as e:
        logger.error(f"❌ Error starting recording for {session_id}: {e}")


async def handle_stop_recording(websocket: WebSocket, session_id: str):
    """Handle stop recording request"""
    try:
        await voice_pipeline_service.stop_recording(session_id)
        await websocket_manager.send_to_session(session_id, {
            "type": "recording_stopped",
            "message": "Recording stopped"
        })
        
    except Exception as e:
        logger.error(f"❌ Error stopping recording for {session_id}: {e}")


async def handle_ping(websocket: WebSocket, session_id: str):
    """Handle ping requests"""
    await websocket_manager.send_to_session(session_id, {
        "type": "pong",
        "timestamp": time.time()
    })


async def handle_stats_request(websocket: WebSocket, session_id: str):
    """Send session statistics"""
    session = active_sessions.get(session_id, {})
    stats = latency_logger.get_session_stats(session_id)
    
    await websocket_manager.send_to_session(session_id, {
        "type": "stats",
        "session_duration": time.time() - session.get("connected_at", time.time()),
        "total_interactions": session.get("total_interactions", 0),
        "latency_stats": stats
    })


async def cleanup_session(session_id: str):
    """Clean up session data"""
    websocket_manager.disconnect(session_id)
    
    if session_id in active_sessions:
        session = active_sessions.pop(session_id)
        
        # Clean up pipecat session
        if session.get("session_info"):
            try:
                await voice_pipeline_service.cleanup_session(session_id)
            except Exception as e:
                logger.error(f"❌ Error cleaning up session for {session_id}: {e}")
        
        logger.info(f"🧹 Session cleaned up: {session_id} - Total interactions: {session.get('total_interactions', 0)}")
    
    # Log final session stats
    latency_logger.log_session_end(session_id)


if __name__ == "__main__":
    logger.info("🚀 Starting Pipecat Voice Agent Server...")
    logger.info(f"🔑 Groq API configured: {bool(config_service.groq_api_key)}")
    logger.info(f"🗣️ TTS: Browser Web Speech API (FREE)")
    logger.info(f"🎤 STT: Browser Web Speech API (FREE)")
    logger.info(f"🎛️ Framework: Pipecat + Browser")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )