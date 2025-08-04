"""
Voice Chat Streaming - Main FastAPI Application
Modular voice chat application using OpenAI, ElevenLabs, and Pipecat
"""

import os
import sys
import argparse
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from loguru import logger

# Import our modular services
from services.openai_service import OpenAIService
from services.elevenlabs_service import ElevenLabsService
from services.pipecat_service import PipecatService, check_pipecat_dependencies
from handlers.websocket_handler import WebSocketHandler

# Load environment variables
load_dotenv(override=True)

# Setup logging
logger.add(sys.stderr, level="INFO")

# FastAPI instance
app = FastAPI(
    title="Voice Chat Streaming",
    description="Modular voice chat application with OpenAI, ElevenLabs, and Pipecat",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
openai_service: OpenAIService = None
elevenlabs_service: ElevenLabsService = None
pipecat_service: PipecatService = None
websocket_handler: WebSocketHandler = None


def initialize_services():
    """Initialize all services with proper error handling"""
    global openai_service, elevenlabs_service, pipecat_service, websocket_handler
    
    try:
        # Initialize OpenAI service
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required in .env")
        
        openai_service = OpenAIService(openai_api_key)
        logger.info("✅ OpenAI service initialized")
        
        # Initialize ElevenLabs service
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY is required in .env")
        
        elevenlabs_service = ElevenLabsService(elevenlabs_api_key)
        logger.info("✅ ElevenLabs service initialized")
        
        # Initialize Pipecat service (optional)
        try:
            pipecat_service = PipecatService(openai_api_key)
            if pipecat_service.check_availability():
                logger.info("✅ Pipecat service initialized")
            else:
                logger.warning("⚠️  Pipecat service initialized but not fully available")
        except Exception as e:
            logger.warning(f"⚠️  Pipecat service initialization failed: {e}")
            pipecat_service = None
        
        # Initialize WebSocket handler
        websocket_handler = WebSocketHandler(
            openai_service=openai_service,
            elevenlabs_service=elevenlabs_service,
            pipecat_service=pipecat_service
        )
        logger.info("✅ WebSocket handler initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Voice Chat Streaming application...")
    
    if not initialize_services():
        logger.error("❌ Failed to initialize services")
        sys.exit(1)
    
    logger.info("✅ All services initialized successfully")


# Mount static files (frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"✅ Frontend mounted from: {frontend_path}")


@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Serve the main voice chat interface"""
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    else:
        return HTMLResponse("""
        <html>
            <head><title>Voice Chat Streaming</title></head>
            <body>
                <h1>Voice Chat Streaming</h1>
                <p>Frontend files not found. Please check the frontend directory.</p>
                <p>Expected path: {}</p>
            </body>
        </html>
        """.format(frontend_file))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services_status = {
        "openai": openai_service is not None,
        "elevenlabs": elevenlabs_service is not None,
        "pipecat": pipecat_service is not None and pipecat_service.check_availability(),
        "websocket_handler": websocket_handler is not None
    }
    
    return {
        "status": "healthy",
        "service": "voice_chat_streaming",
        "services": services_status,
        "active_sessions": websocket_handler.get_session_count() if websocket_handler else 0
    }


@app.get("/status")
async def get_status():
    """Get detailed status of all services"""
    pipecat_deps = check_pipecat_dependencies()
    
    return {
        "status": "running",
        "services": {
            "openai": {
                "available": openai_service is not None,
                "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
            },
            "elevenlabs": {
                "available": elevenlabs_service is not None,
                "api_key_configured": bool(os.getenv("ELEVENLABS_API_KEY"))
            },
            "pipecat": {
                "available": pipecat_service is not None,
                "functional": pipecat_service.check_availability() if pipecat_service else False,
                "dependencies": pipecat_deps
            }
        },
        "active_sessions": websocket_handler.get_active_sessions() if websocket_handler else [],
        "session_count": websocket_handler.get_session_count() if websocket_handler else 0
    }


@app.websocket("/stream-chat")
async def websocket_stream_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming voice chat"""
    if not websocket_handler:
        await websocket.close(code=1011, reason="Service not initialized")
        return
    
    await websocket_handler.handle_connection(websocket)


@app.get("/api/voices")
async def get_available_voices():
    """Get available ElevenLabs voices"""
    if not elevenlabs_service:
        return {"error": "ElevenLabs service not available"}
    
    try:
        voices = await elevenlabs_service.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return {"error": str(e)}


@app.post("/api/test-services")
async def test_services():
    """Test all services connectivity"""
    results = {}
    
    # Test OpenAI
    if openai_service:
        try:
            test_response = await openai_service.get_simple_completion(
                "Say 'OpenAI service is working'",
                "You are a test assistant. Respond exactly as requested."
            )
            results["openai"] = {"status": "success", "response": test_response}
        except Exception as e:
            results["openai"] = {"status": "error", "error": str(e)}
    else:
        results["openai"] = {"status": "not_initialized"}
    
    # Test ElevenLabs
    if elevenlabs_service:
        try:
            api_key_valid = await elevenlabs_service.check_api_key()
            results["elevenlabs"] = {"status": "success" if api_key_valid else "invalid_api_key"}
        except Exception as e:
            results["elevenlabs"] = {"status": "error", "error": str(e)}
    else:
        results["elevenlabs"] = {"status": "not_initialized"}
    
    # Test Pipecat
    if pipecat_service:
        results["pipecat"] = {
            "status": "available" if pipecat_service.check_availability() else "not_functional",
            "dependencies": check_pipecat_dependencies()
        }
    else:
        results["pipecat"] = {"status": "not_initialized"}
    
    return {"test_results": results}


def check_environment():
    """Check if environment is properly configured"""
    required_vars = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please create a .env file with:")
        for var in missing_vars:
            logger.info(f"  {var}=your_api_key_here")
        return False
    
    logger.info("✅ Environment configuration verified")
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run modular voice chat streaming server')
    parser.add_argument("--host", type=str, default="0.0.0.0", help='Host to bind to')
    parser.add_argument("--port", type=int, default=8001, help='Port to bind to')
    parser.add_argument("--reload", action="store_true", help='Enable auto-reload for development')
    parser.add_argument("--check-only", action="store_true", help='Only check environment and dependencies')
    args = parser.parse_args()
    
    # Startup banner
    print("🎙️ Voice Chat Streaming - Modular Architecture")
    print("=" * 60)
    print("🧩 OpenAI + ElevenLabs + Pipecat + FastAPI")
    print("🚀 Optimized for Ultra-Low Latency")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    deps = check_pipecat_dependencies()
    logger.info(f"Dependency check: {deps}")
    
    if args.check_only:
        logger.info("✅ All checks completed!")
        return
    
    # Start server
    logger.info(f"🚀 Starting modular voice chat server...")
    logger.info(f"📱 Frontend: http://{args.host}:{args.port}/")
    logger.info(f"🔍 Health check: http://{args.host}:{args.port}/health")
    logger.info(f"📊 Status: http://{args.host}:{args.port}/status")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("-" * 60)
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()