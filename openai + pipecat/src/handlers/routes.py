"""
HTTP Routes module
Defines HTTP endpoints for the OpenAI + Pipecat Voice Assistant
"""
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Create router
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_root():
    """Serve the main HTML page"""
    try:
        # Look for index.html in the openai-pipecat directory
        file_path = os.path.join(os.path.dirname(__file__), "..", "..", "index.html")
        file_path = os.path.abspath(file_path)
        
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            logger.error(f"index.html not found at {file_path}")
            # Return a simple fallback HTML
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head><title>Voice Assistant</title></head>
                <body>
                    <h1>🎙️ OpenAI + Pipecat Voice Assistant</h1>
                    <p>Frontend files not found. Please check your installation.</p>
                </body>
                </html>
                """,
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error serving root page: {e}")
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>Failed to load the application.</p>
            </body>
            </html>
            """,
            status_code=500
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "OpenAI + Pipecat Voice Assistant",
        "version": "1.0.0"
    })

@router.get("/status")
async def get_status():
    """Get application status and metrics"""
    # Import here to avoid circular imports
    from ..handlers.websocket_handler import WebSocketHandler
    
    # This is a simple status endpoint
    # In production, you'd want to inject the websocket service properly
    return JSONResponse({
        "status": "running",
        "service_info": {
            "name": "OpenAI + Pipecat Voice Assistant",
            "version": "1.0.0",
            "description": "Modular voice assistant with OpenAI and Pipecat integration"
        },
        "features": [
            "Voice recognition",
            "Text-to-speech with gTTS",
            "OpenAI integration via Pipecat",
            "Real-time WebSocket communication",
            "Conversation history management"
        ]
    })

@router.get("/api/info")
async def get_api_info():
    """Get API information"""
    return JSONResponse({
        "api_version": "v1",
        "endpoints": {
            "websocket": "/chat",
            "health": "/health",
            "status": "/status",
            "info": "/api/info"
        },
        "websocket_message_types": [
            "start_recording",
            "stop_recording",
            "voice_chunk",
            "text",
            "ping",
            "pong",
            "message",
            "audio",
            "error",
            "info"
        ],
        "supported_features": [
            "Real-time voice conversation",
            "Text input/output",
            "Audio synthesis",
            "Conversation history",
            "WebSocket reconnection"
        ]
    })