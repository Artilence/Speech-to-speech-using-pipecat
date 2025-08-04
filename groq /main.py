"""
Real-time Voice Agent using Groq LLM with Browser TTS
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from services.voice_service import VoiceService
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
app = FastAPI(title="Voice Agent API", version="1.0.0")
config_service = ConfigService()
websocket_manager = WebSocketManager()
voice_service = VoiceService(config_service)
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
            "tts": "browser",
            "voice_service": voice_service.is_ready()
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
        "total_interactions": 0
    }
    
    logger.info(f"🎯 New voice session started: {session_id}")
    
    try:
        await handle_voice_session(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"📞 Session ended: {session_id}")
    except Exception as e:
        logger.error(f"❌ Session error {session_id}: {e}")
    finally:
        await cleanup_session(session_id)


async def handle_voice_session(websocket: WebSocket, session_id: str):
    """Handle the voice interaction session"""
    session = active_sessions[session_id]
    
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
            elif message_type == "tts_test":
                await handle_tts_test(websocket, session_id, message)
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
    """Process user speech and generate AI response"""
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
        # Generate AI response using voice service
        response_data = await voice_service.generate_response(
            user_text, 
            session["conversation_history"],
            session_id
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
        
        # Audio is handled by browser TTS - no server-side audio streaming needed
        
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


async def handle_tts_test(websocket: WebSocket, session_id: str, message: dict):
    """Handle TTS test requests (text-only, no LLM processing)"""
    request_start = time.time()
    text_content = message.get("content", "").strip()
    
    if not text_content:
        logger.warning(f"Empty TTS test content from {session_id}")
        await websocket_manager.send_to_session(session_id, {
            "type": "error",
            "message": "Empty text provided for TTS test"
        })
        return
    
    logger.info(f"🗣️ TTS Test ({session_id}): {text_content}")
    
    try:
        # Send processing acknowledgment
        await websocket_manager.send_to_session(session_id, {
            "type": "processing",
            "message": "Generating speech...",
            "request_id": str(uuid.uuid4())
        })
        
        # Audio is handled by browser TTS - no server-side audio streaming needed
        
        # Send completion message
        await websocket_manager.send_to_session(session_id, {
            "type": "tts_complete",
            "message": "TTS generation completed"
        })
        
        # Log latency
        total_latency = (time.time() - request_start) * 1000
        latency_logger.log_latency(session_id, "tts_test", total_latency)
        
        logger.info(f"✅ TTS test completed for {session_id} in {total_latency:.2f}ms")
        
    except Exception as e:
        logger.error(f"❌ Error in TTS test for {session_id}: {e}")
        await websocket_manager.send_to_session(session_id, {
            "type": "error",
            "message": f"TTS test failed: {str(e)}"
        })



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
        logger.info(f"🧹 Session cleaned up: {session_id} - Total interactions: {session.get('total_interactions', 0)}")
    
    # Clean up voice service resources
    await voice_service.cleanup_session(session_id)
    
    # Log final session stats
    latency_logger.log_session_end(session_id)


if __name__ == "__main__":
    logger.info("🚀 Starting Voice Agent Server...")
    logger.info(f"🔑 Groq API configured: {bool(config_service.groq_api_key)}")
    logger.info(f"🗣️ TTS: Browser Web Speech API")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )