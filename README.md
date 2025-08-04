# Speech-to-Speech AI Assistant - Multi-Implementation Comparison

A comprehensive collection of speech-to-speech AI implementations using various technology stacks, optimized for different latency requirements and use cases.

## 🎯 Project Overview

This repository contains **5 different implementations** of speech-to-speech AI assistants, each using different combinations of technologies to achieve varying levels of performance, latency, and functionality:

1. **OpenAI Basic** - Simple implementation with OpenAI + gTTS
2. **OpenAI + Pipecat** - Enhanced with Pipecat framework integration
3. **OpenAI + ElevenLabs + Pipecat** - Professional TTS with ultra-low latency optimization
4. **OpenAI + ElevenLabs + Pipecat + Streaming** - Full streaming architecture
5. **OpenAI + Pipecat + Streaming** - Modular streaming without ElevenLabs

## 📊 Performance Comparison

| Implementation | Latency (Total) | TTS Quality | Real-time Streaming | Complexity |
|----------------|-----------------|-------------|-------------------|------------|
| OpenAI Basic | ~2-5 seconds | Basic (gTTS) | ❌ | Low |
| OpenAI + Pipecat | ~1-3 seconds | Basic (gTTS) | ⚠️ Partial | Medium |
| OpenAI + ElevenLabs + Pipecat | **~750-1500ms** | Excellent | ✅ Full | High |
| OpenAI + ElevenLabs + Pipecat + Streaming | **~500-1000ms** | Excellent | ✅ Full | Very High |
| OpenAI + Pipecat + Streaming | ~500ms-1s | Basic (gTTS) | ✅ Full | High |

## 🏗️ Architecture Breakdown

### 1. OpenAI Basic (`openai/`)
**Technologies**: FastAPI + OpenAI + gTTS + WebSocket

- **Purpose**: Simple baseline implementation
- **TTS**: Google Text-to-Speech (gTTS)
- **Latency**: 2-5 seconds (no streaming)
- **Use Case**: Proof of concept, simple demos

```bash
# Dependencies
- openai>=1.0.0
- gTTS>=2.3.0
- fastapi>=0.100.0
- uvicorn[standard]>=0.20.0
```

### 2. OpenAI + Pipecat (`openai + pipecat/`)
**Technologies**: FastAPI + OpenAI + Pipecat + gTTS + WebSocket

- **Purpose**: Introduction to Pipecat framework
- **TTS**: Google Text-to-Speech (gTTS)
- **Latency**: 1-3 seconds
- **Features**: Real-time conversation framework, better architecture
- **Use Case**: Learning Pipecat, medium-latency applications

```bash
# Dependencies
- openai>=1.0.0
- pipecat-ai>=0.0.1
- gTTS>=2.3.0
- fastapi>=0.100.0
```

### 3. OpenAI + ElevenLabs + Pipecat (`openai + elevenlabs + pipecat/`)
**Technologies**: FastAPI + OpenAI + ElevenLabs + Pipecat + WebSocket Streaming

- **Purpose**: Ultra-low latency professional implementation
- **TTS**: ElevenLabs (eleven_flash_v2_5 model)
- **Latency**: **75-150ms** (optimized for speed)
- **Features**: 
  - WebSocket streaming to ElevenLabs
  - Aggressive chunking (50-150 char chunks)
  - Real-time latency monitoring
  - Professional voice quality
- **Use Case**: Production applications, real-time conversations

```bash
# Key optimizations
- Voice: Rachel (21m00Tcm4TlvDq8ikWAM)
- Model: eleven_flash_v2_5 (fastest)
- Chunking: [50, 90, 120, 150] characters
- Settings: stability=0.4, similarity_boost=0.75
```

### 4. OpenAI + ElevenLabs + Pipecat + Streaming (`openai + elevenlabs + pipecat + streaming/`)
**Technologies**: FastAPI + OpenAI + ElevenLabs + Pipecat + Full Streaming Architecture

- **Purpose**: Maximum performance with modular architecture
- **TTS**: ElevenLabs with advanced streaming
- **Latency**: **50-100ms** (best performance)
- **Features**:
  - Modular service architecture
  - Advanced session management
  - Comprehensive error handling
  - Production-ready scaling
- **Use Case**: Enterprise applications, high-performance requirements

### 5. OpenAI + Pipecat + Streaming (`openai + pipecat + streaming/`)
**Technologies**: FastAPI + OpenAI + Pipecat + gTTS + Streaming Architecture

- **Purpose**: Cost-effective streaming solution
- **TTS**: Google Text-to-Speech (gTTS)
- **Latency**: 500ms-1 second
- **Features**: Full streaming architecture without premium TTS costs
- **Use Case**: Budget-conscious streaming applications

## 🚀 Quick Start

### Prerequisites

```bash
# Clone the repository
git clone <repository-url>
cd Speech-to-speech-using-pipecat

# Install Python 3.8+
python --version  # Should be 3.8 or higher
```

### Environment Setup

Create a `.env` file in each implementation folder:

```bash
# Required for all implementations
OPENAI_API_KEY=your_openai_api_key_here

# Required for ElevenLabs implementations
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional configuration
AI_MODEL=gpt-3.5-turbo
MAX_TOKENS=150
TEMPERATURE=0.7
```

## 📖 Implementation Guides

### 1. OpenAI Basic

```bash
cd "openai"

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.main --host 0.0.0.0 --port 8000

# Open browser
open http://localhost:8000
```

**Features**:
- Simple WebSocket interface
- Basic conversation flow
- gTTS audio generation
- ~2-5 second latency

### 2. OpenAI + Pipecat

```bash
cd "openai + pipecat"

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.main --host 0.0.0.0 --port 8001

# Open browser
open http://localhost:8001
```

**Features**:
- Pipecat framework integration
- Improved conversation management
- Better error handling
- ~1-3 second latency

### 3. OpenAI + ElevenLabs + Pipecat (Ultra-Low Latency)

```bash
cd "openai + elevenlabs + pipecat"

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py  # or uvicorn main:app --host 0.0.0.0 --port 8002

# Open browser
open http://localhost:8002
```

**Features**:
- **~75-150ms latency**
- Professional voice quality
- Real-time streaming
- Latency monitoring dashboard
- WebSocket optimization

**Latency Breakdown**:
- OpenAI API: ~50-100ms
- WebSocket Connection: ~10-30ms
- Time to First Chunk: ~75ms
- Total Round-trip: ~75-150ms

### 4. OpenAI + ElevenLabs + Pipecat + Streaming (Best Performance)

```bash
cd "openai + elevenlabs + pipecat + streaming"

# Install dependencies
pip install -r requirements.txt

# Run the server
cd backend
python main.py --host 0.0.0.0 --port 8001

# Open browser
open http://localhost:8001
```

**Features**:
- **~50-100ms latency** (best)
- Modular architecture
- Advanced session management
- Production-ready scaling
- Comprehensive monitoring

**API Endpoints**:
- `/health` - Health check
- `/status` - Detailed service status
- `/api/voices` - Available voices
- `/api/test-services` - Service connectivity test

### 5. OpenAI + Pipecat + Streaming (Budget-Friendly)

```bash
cd "openai + pipecat + streaming"

# Install dependencies
pip install -r requirements.txt

# Run the server
cd src/backend
python main.py --host 0.0.0.0 --port 8003

# Open browser
open http://localhost:8003
```

**Features**:
- Full streaming architecture
- No premium TTS costs
- Modular design
- ~500ms-1s latency

## 🔧 Advanced Configuration

### ElevenLabs Optimization Settings

For ultra-low latency with ElevenLabs:

```python
# Voice settings for speed
voice_settings = {
    "stability": 0.4,        # Lower = faster
    "similarity_boost": 0.75,
    "style": 0.0,           # Disable for speed
    "use_speaker_boost": False  # Disable for speed
}

# Aggressive chunking
generation_config = {
    "chunk_length_schedule": [50, 90, 120, 150]
}

# Fastest model
model_id = "eleven_flash_v2_5"  # ~75ms generation time
```

### Performance Tuning

#### For Development:
```bash
# Enable auto-reload
python main.py --reload --log-level debug
```

#### For Production:
```bash
# Optimize for performance
python main.py --host 0.0.0.0 --port 8000
# Use gunicorn for better scaling
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## 📈 Latency Analysis

### Measurement Breakdown

1. **Request Processing**: User input → OpenAI
2. **AI Generation**: OpenAI response time
3. **TTS Processing**: Text → Audio conversion
4. **Network Transfer**: Audio streaming to client
5. **Client Playback**: Audio rendering

### Best Practices for Low Latency

1. **Use ElevenLabs Flash Models**: 3x faster than standard models
2. **Optimize Chunking**: Smaller chunks = faster first response
3. **WebSocket Streaming**: Eliminates HTTP overhead
4. **Connection Pooling**: Reuse connections when possible
5. **Geographic Proximity**: Host near API providers

## 🛠️ Development Tools

### Health Checks

All implementations provide health check endpoints:

```bash
# Basic health
curl http://localhost:8000/health

# Detailed status (streaming versions)
curl http://localhost:8000/status

# Test services connectivity
curl -X POST http://localhost:8000/api/test-services
```

### Monitoring

The ElevenLabs implementations include real-time latency monitoring:

- OpenAI API latency
- WebSocket connection time
- Time to first audio chunk
- Total round-trip time

## 🚨 Troubleshooting

### Common Issues

1. **Missing API Keys**:
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   echo $ELEVENLABS_API_KEY
   ```

2. **Port Conflicts**:
   ```bash
   # Use different ports for each implementation
   python main.py --port 8001
   ```

3. **Dependency Issues**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

4. **Audio Issues**:
   ```bash
   # Install system audio dependencies (macOS)
   brew install portaudio
   
   # Ubuntu
   sudo apt-get install portaudio19-dev
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python main.py --log-level debug
```

## 🎯 Use Case Recommendations

### Choose OpenAI Basic for:
- Learning and experimentation
- Simple proof-of-concepts
- Non-real-time applications

### Choose OpenAI + Pipecat for:
- Learning Pipecat framework
- Medium-latency applications
- Budget-conscious implementations

### Choose OpenAI + ElevenLabs + Pipecat for:
- Real-time conversations
- Professional voice quality
- Customer service applications
- Interactive demos

### Choose Streaming Versions for:
- Production applications
- High-traffic scenarios
- Enterprise deployments
- Scalable architectures

## 📚 Technology Stack Details

### Core Technologies

- **FastAPI**: Modern, fast web framework for APIs
- **OpenAI**: Advanced language models (GPT-3.5/4)
- **ElevenLabs**: Premium text-to-speech service
- **Pipecat**: Real-time AI application framework
- **WebSockets**: Low-latency bidirectional communication
- **gTTS**: Google Text-to-Speech (free alternative)

### Frontend Technologies

- **Vanilla JavaScript**: Maximum performance, no framework overhead
- **WebSocket Client**: Real-time communication
- **Audio API**: Browser audio playback
- **Responsive CSS**: Mobile-friendly interfaces

## 🔮 Future Enhancements

- [ ] Support for additional TTS providers (Azure, AWS Polly)
- [ ] Voice cloning integration
- [ ] Multi-language support
- [ ] Mobile application versions
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] Performance benchmarking suite
- [ ] A/B testing framework

## 📄 License

This project is provided for educational and development purposes. Please ensure you comply with the terms of service for OpenAI and ElevenLabs APIs.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your implementation
4. Update this README with performance metrics
5. Submit a pull request

---

*Built with ❤️ for the speech-to-speech AI community*