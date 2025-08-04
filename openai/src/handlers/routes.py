"""
HTTP Routes module
Defines HTTP endpoints for the OpenAI Voice Assistant
"""
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from loguru import logger

from ..services import WebSocketService

# Create router
router = APIRouter()

# WebSocket service instance for status endpoints
websocket_service = WebSocketService()

@router.get("/", response_class=HTMLResponse)
async def get_root():
    """Serve the main HTML page"""
    try:
        # Look for index.html in the openai directory
        file_path = os.path.join(os.path.dirname(__file__), "..", "..", "index.html")
        file_path = os.path.abspath(file_path)
        
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            logger.error(f"index.html not found at {file_path}")
            return HTMLResponse(
                content="<h1>Voice Assistant</h1><p>Frontend not found. Please check your installation.</p>",
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error serving root page: {e}")
        return HTMLResponse(
            content="<h1>Error</h1><p>Failed to load the application.</p>",
            status_code=500
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "OpenAI Voice Assistant",
        "version": "1.0.0"
    })

@router.get("/status")
async def get_status():
    """Get application status and metrics"""
    return JSONResponse({
        "status": "running",
        "connected_clients": websocket_service.get_connection_count(),
        "service_info": {
            "name": "OpenAI Voice Assistant",
            "version": "1.0.0",
            "description": "Modular voice assistant with OpenAI integration"
        }
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
        "features": [
            "Voice recognition",
            "Text-to-speech",
            "OpenAI integration",
            "Real-time conversation"
        ]
    })