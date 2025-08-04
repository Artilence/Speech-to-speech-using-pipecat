"""
Environment configuration utilities
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .logging_config import get_logger

logger = get_logger(__name__)


def load_environment(env_file: Optional[str] = None) -> Dict[str, Any]:
    """Load environment variables from .env file"""
    
    if env_file is None:
        env_file = Path('.env')
    else:
        env_file = Path(env_file)
    
    if env_file.exists():
        load_dotenv(env_file, override=True)
        logger.info(f"✅ Loaded environment from {env_file}")
    else:
        logger.warning(f"⚠️  Environment file {env_file} not found")
    
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'HOST': os.getenv('HOST', '0.0.0.0'),
        'PORT': int(os.getenv('PORT', '8001')),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
        'MAX_TOKENS': int(os.getenv('MAX_TOKENS', '150')),
        'TEMPERATURE': float(os.getenv('TEMPERATURE', '0.7')),
        'MODEL': os.getenv('MODEL', 'gpt-3.5-turbo'),
    }


def validate_environment(config: Dict[str, Any]) -> bool:
    """Validate required environment variables"""
    
    required_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not config.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please create a .env file with:")
        for var in missing_vars:
            logger.info(f"  {var}=your_value_here")
        return False
    
    logger.info("✅ Environment validation passed")
    return True


def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    try:
        import pipecat
        logger.info("✅ Pipecat found")
        
        try:
            import whisper
            logger.info("✅ Whisper found")
        except ImportError:
            logger.warning("⚠️  Whisper not found (optional for advanced features)")
        
        try:
            import torch
            logger.info("✅ Torch found")
        except ImportError:
            logger.warning("⚠️  Torch not found (optional for advanced features)")
        
        logger.info("✅ Core dependencies found")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing core dependency: {e}")
        logger.info("Note: The server will work with basic features even without all dependencies")
        return True  # Allow running even without all deps