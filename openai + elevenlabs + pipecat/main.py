"""
Main application module for Voice Conversation Agent
Orchestrates all services and handles FastAPI routes and WebSocket endpoints
"""
import json
import time
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

try:
    from .config import config
    from .ai_service import AIService
    from .conversation_manager import ConversationManager
    from .websocket_manager import WebSocketManager
    from .audio_streaming import AudioStreamingService
except ImportError:
    from config import config
    from ai_service import AIService
    from conversation_manager import ConversationManager
    from websocket_manager import WebSocketManager
    from audio_streaming import AudioStreamingService

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Voice Conversation Agent")

# Initialize services
websocket_manager = WebSocketManager()
conversation_manager = ConversationManager()
ai_service = AIService()
audio_service = AudioStreamingService(websocket_manager)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time voice conversation"""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "user_speech":
                await handle_user_speech(message, client_id)
            elif message["type"] == "ping":
                await handle_ping(client_id)
                
    except WebSocketDisconnect:
        await handle_disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await handle_disconnect(client_id)

async def handle_user_speech(message: dict, client_id: str) -> None:
    """Handle user speech input and generate AI response with audio"""
    request_start_time = time.time()
    user_text = message["text"]
    logger.info(f"Received from {client_id}: {user_text}")
    
    # Send acknowledgment
    await websocket_manager.send_message({
        "type": "processing",
        "message": "Processing your request...",
        "request_start_time": request_start_time * 1000  # Convert to milliseconds for frontend
    }, client_id)
    
    # Add user message to conversation
    conversation_manager.add_user_message(client_id, user_text)
    
    # Get conversation history and AI response
    conversation_history = conversation_manager.get_conversation_history(client_id)
    ai_response, openai_latency = await ai_service.get_response(user_text, conversation_history)
    
    # Add AI response to conversation
    conversation_manager.add_ai_message(client_id, ai_response)
    
    # Send text response
    await websocket_manager.send_message({
        "type": "ai_response",
        "text": ai_response
    }, client_id)
    
    # Generate and stream audio using WebSocket streaming for ultra-low latency
    await audio_service.stream_text_to_speech(
        ai_response, 
        client_id, 
        openai_latency, 
        request_start_time
    )

async def handle_ping(client_id: str) -> None:
    """Handle ping message from client"""
    await websocket_manager.send_message({
        "type": "pong"
    }, client_id)

async def handle_disconnect(client_id: str) -> None:
    """Handle client disconnection and cleanup"""
    websocket_manager.disconnect(client_id)
    conversation_manager.cleanup_conversation(client_id)

@app.get("/")
async def get_voice_agent():
    """Serve the voice agent HTML page"""
    try:
        with open("11/index.html", "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Voice agent HTML file not found")

@app.get("/health")
async def health_check():
    """Health check endpoint with service status"""
    return {
        "status": "healthy",
        "elevenlabs_configured": bool(config.elevenlabs_api_key),
        "openai_configured": bool(config.openai_api_key),
        "active_connections": websocket_manager.get_connection_count(),
        "active_conversations": len(conversation_manager.get_active_clients())
    }

@app.get("/stats")
async def get_stats():
    """Get current application statistics"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "connected_clients": websocket_manager.get_connected_clients(),
        "active_conversations": len(conversation_manager.get_active_clients()),
        "config": {
            "ai_model": config.ai_model,
            "voice_id": config.voice_id,
            "model_id": config.model_id
        }
    }

def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting Voice Conversation Agent...")
        logger.info(f"OpenAI configured: {bool(config.openai_api_key)}")
        logger.info(f"ElevenLabs configured: {bool(config.elevenlabs_api_key)}")
        
        uvicorn.run(
            "11.main:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
            log_level=config.log_level
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()