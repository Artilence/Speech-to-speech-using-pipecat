"""
Main FastAPI application for voice chat server
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from .utils.logging_config import setup_logging, get_logger
from .utils.env_config import load_environment, validate_environment, check_dependencies
from .services.websocket_service import WebSocketService
from .services.llm_service import LLMService
from .services.audio_service import AudioService
from .handlers.voice_handler import VoiceCallHandler

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load environment configuration
config = load_environment()

# Validate environment
if not validate_environment(config):
    sys.exit(1)

# FastAPI instance
app = FastAPI(
    title="Voice Chat with AI",
    description="Real-time voice chat application with AI using OpenAI and Pipecat",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
websocket_service = WebSocketService()
llm_service = LLMService(
    api_key=config['OPENAI_API_KEY'],
    model=config['MODEL'],
    max_tokens=config['MAX_TOKENS'],
    temperature=config['TEMPERATURE']
)
audio_service = AudioService()
voice_handler = VoiceCallHandler(websocket_service, llm_service, audio_service)


@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Serve the main voice chat interface at root"""
    file_path = Path(__file__).parent.parent.parent / "static" / "index.html"
    if file_path.exists():
        return FileResponse(file_path)
    else:
        # Fallback to embedded HTML for development
        return HTMLResponse(get_embedded_html())


@app.get("/stream", response_class=HTMLResponse)
async def get_stream_page():
    """Serve the streaming voice chat interface"""
    return await get_root()


@app.websocket("/stream-chat")
async def websocket_stream_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming voice chat"""
    session_id = None
    
    try:
        # Connect to WebSocket service
        session_id = await websocket_service.connect(websocket)
        
        # Handle voice session
        await voice_handler.handle_voice_session(session_id)
        
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        # Clean up session
        if session_id:
            await websocket_service.disconnect(session_id)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice_chat_api",
        "version": "1.0.0"
    }


@app.get("/status")
async def get_status():
    """Get service status and statistics"""
    return {
        "status": "running",
        "session_stats": websocket_service.get_session_stats(),
        "config": {
            "model": config['MODEL'],
            "max_tokens": config['MAX_TOKENS'],
            "temperature": config['TEMPERATURE']
        }
    }


def get_embedded_html() -> str:
    """Embedded HTML for development/fallback"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Chat with AI</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            .button { padding: 20px 40px; font-size: 18px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎙️ Voice Chat with AI</h1>
            <p>The modular voice chat application is running!</p>
            <p>Please ensure the frontend files are properly placed in the static directory.</p>
            <button class="button" onclick="window.location.reload()">Refresh</button>
        </div>
    </body>
    </html>
    """


def main():
    """Main entry point"""
    # Startup banner
    print("🎙️ Voice Chat with AI (Modular Version)")
    print("=" * 50)
    
    parser = argparse.ArgumentParser(description='Run modular voice chat server')
    parser.add_argument("--host", type=str, default=config['HOST'], 
                       help=f'Host to bind to (default: {config["HOST"]})')
    parser.add_argument("--port", type=int, default=config['PORT'], 
                       help=f'Port to bind to (default: {config["PORT"]})')
    parser.add_argument("--reload", action="store_true", 
                       help='Enable auto-reload for development')
    parser.add_argument("--check-only", action="store_true", 
                       help='Only check dependencies and exit')
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        logger.warning("⚠️  Some dependencies missing, but continuing with basic features")
    
    if args.check_only:
        print("✅ All checks passed!")
        sys.exit(0)
    
    print(f"🚀 Starting modular voice chat server...")
    print(f"📱 Open in browser: http://{args.host}:{args.port}/")
    print(f"🎤 Voice chat at: http://localhost:{args.port}/")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start server
    uvicorn.run(
        "src.backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()