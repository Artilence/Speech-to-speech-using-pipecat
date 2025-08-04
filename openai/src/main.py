"""
Main application module for OpenAI Voice Assistant
Orchestrates all services and handles FastAPI app configuration
"""
import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from loguru import logger

from .config import config
from .handlers import WebSocketHandler, router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 OpenAI Voice Assistant starting...")
    logger.info(f"Host: {config.host}:{config.port}")
    logger.info(f"Debug mode: {config.debug}")
    yield
    logger.info("🔄 OpenAI Voice Assistant shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title="OpenAI Voice Assistant",
        description="Modular voice assistant with OpenAI integration and TTS capabilities",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files for frontend assets
    try:
        app.mount("/assets", StaticFiles(directory="openai/assets"), name="assets")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    # Include HTTP routes
    app.include_router(router)
    
    # Initialize WebSocket handler
    websocket_handler = WebSocketHandler()
    
    @app.websocket("/chat")
    async def websocket_chat(websocket: WebSocket):
        """WebSocket endpoint for voice chat"""
        await websocket_handler.handle_connection(websocket)
    
    return app


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="OpenAI Voice Assistant")
    parser.add_argument(
        "--host", 
        type=str, 
        default=config.host,
        help="Host to bind to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=config.port,
        help="Port to bind to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level"
    )
    
    args = parser.parse_args()
    
    # Create the app
    app = create_app()
    
    # Run the server
    try:
        uvicorn.run(
            "openai.src.main:app" if not args.reload else app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


# Create app instance for uvicorn
app = create_app()

if __name__ == "__main__":
    main()