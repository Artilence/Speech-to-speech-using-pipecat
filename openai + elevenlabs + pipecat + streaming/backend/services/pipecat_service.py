"""
Pipecat Service Module
Handles streaming pipeline functionality using Pipecat
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any
from loguru import logger

# Try to import Pipecat components
try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.services.openai.llm import OpenAILLMService
    from pipecat.frames.frames import (
        Frame, AudioRawFrame, TextFrame, LLMMessagesFrame, 
        TranscriptionFrame, TTSAudioRawFrame, StartInterruptionFrame,
        StopInterruptionFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
    )
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pipecat not available for streaming: {e}")
    PIPECAT_AVAILABLE = False
    
    # Define dummy classes to prevent errors
    class FrameProcessor:
        def __init__(self): pass
        async def process_frame(self, frame, direction): pass
        async def push_frame(self, frame, direction): pass
    class Frame: pass
    class Pipeline: pass
    FrameDirection = None


class PipecatService:
    """Service for handling Pipecat streaming operations"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.is_available = PIPECAT_AVAILABLE
        self.active_pipelines: Dict[str, Any] = {}
        
        if not self.is_available:
            logger.warning("Pipecat is not available. Advanced streaming features will be disabled.")
    
    def check_availability(self) -> bool:
        """Check if Pipecat is available and properly configured"""
        return self.is_available and bool(self.openai_api_key)
    
    async def create_streaming_pipeline(self, session_id: str, websocket) -> Optional[Pipeline]:
        """Create a streaming pipeline for voice conversations"""
        
        if not self.check_availability():
            logger.warning("Pipecat not available, cannot create pipeline")
            return None
        
        try:
            # For now, let's skip the complex pipeline and use direct OpenAI calls
            # This avoids the API compatibility issues with newer Pipecat versions
            logger.info("Skipping complex pipeline creation due to API changes")
            return None
            
            # TODO: Implement when Pipecat API is stable
            # This would include:
            # - WebSocket transport integration
            # - Audio processing pipeline
            # - Speech recognition integration
            # - TTS integration
            # - Real-time streaming
            
        except Exception as e:
            logger.error(f"Failed to create pipeline for {session_id}: {e}")
            return None
    
    async def cleanup_pipeline(self, session_id: str):
        """Clean up a streaming pipeline"""
        if session_id in self.active_pipelines:
            try:
                pipeline = self.active_pipelines[session_id]
                # Add cleanup logic here when implemented
                del self.active_pipelines[session_id]
                logger.info(f"Cleaned up pipeline for session: {session_id}")
            except Exception as e:
                logger.error(f"Error cleaning up pipeline {session_id}: {e}")
    
    def get_active_sessions(self) -> list:
        """Get list of active pipeline sessions"""
        return list(self.active_pipelines.keys())
    
    async def get_pipeline_status(self, session_id: str) -> dict:
        """Get status of a specific pipeline"""
        if session_id not in self.active_pipelines:
            return {"status": "not_found", "session_id": session_id}
        
        return {
            "status": "active",
            "session_id": session_id,
            "available": self.is_available,
            "openai_configured": bool(self.openai_api_key)
        }


class WebSocketTransport(FrameProcessor):
    """Custom transport for WebSocket communication"""
    
    def __init__(self, websocket):
        super().__init__()
        self._websocket = websocket
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Handle different frame types for WebSocket communication"""
        if not PIPECAT_AVAILABLE:
            return
            
        try:
            if isinstance(frame, TextFrame):
                # Send text response to client
                await self._websocket.send_json({
                    "type": "llm_response", 
                    "content": frame.text
                })
                
            elif isinstance(frame, TTSAudioRawFrame):
                # Handle audio frame (would need ElevenLabs integration)
                logger.info("Audio frame received - would convert to base64 and send")
                
            elif isinstance(frame, TranscriptionFrame):
                # Send transcription to client for real-time display
                await self._websocket.send_json({
                    "type": "transcription",
                    "content": frame.text
                })
                
            # Always pass frame downstream
            await self.push_frame(frame, direction)
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")


class StreamingVoiceProcessor(FrameProcessor):
    """Processor for handling streaming voice interactions"""
    
    def __init__(self):
        super().__init__()
        self._current_speech = ""
        self._is_speaking = False
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process voice-related frames"""
        if not PIPECAT_AVAILABLE:
            return
            
        try:
            if isinstance(frame, UserStartedSpeakingFrame):
                self._is_speaking = True
                self._current_speech = ""
                logger.info("User started speaking")
                
            elif isinstance(frame, UserStoppedSpeakingFrame):
                self._is_speaking = False
                logger.info("User stopped speaking")
                
            elif isinstance(frame, TranscriptionFrame):
                if self._is_speaking:
                    self._current_speech += f" {frame.text}"
                
            await self.push_frame(frame, direction)
            
        except Exception as e:
            logger.error(f"Error in voice processor: {e}")


class AudioStreamProcessor(FrameProcessor):
    """Process incoming audio streams"""
    
    def __init__(self):
        super().__init__()
        self._audio_buffer = []
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process audio frames"""
        if not PIPECAT_AVAILABLE:
            return
            
        try:
            if isinstance(frame, AudioRawFrame):
                # Process incoming audio data
                self._audio_buffer.append(frame.audio)
                
            await self.push_frame(frame, direction)
            
        except Exception as e:
            logger.error(f"Error in audio processor: {e}")


def check_pipecat_dependencies() -> dict:
    """Check if Pipecat dependencies are properly installed"""
    dependencies = {
        "pipecat": False,
        "torch": False,
        "whisper": False,
        "pyaudio": False
    }
    
    try:
        import pipecat
        dependencies["pipecat"] = True
        logger.info("✅ Pipecat found")
    except ImportError:
        logger.warning("❌ Pipecat not found")
    
    try:
        import torch
        dependencies["torch"] = True
        logger.info("✅ Torch found")
    except ImportError:
        logger.warning("⚠️  Torch not found (optional)")
    
    try:
        import whisper
        dependencies["whisper"] = True
        logger.info("✅ Whisper found")
    except ImportError:
        logger.warning("⚠️  Whisper not found (optional)")
    
    try:
        import pyaudio
        dependencies["pyaudio"] = True
        logger.info("✅ PyAudio found")
    except ImportError:
        logger.warning("⚠️  PyAudio not found (optional)")
    
    return dependencies