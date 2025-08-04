# Pipecat Voice Agent with Groq + Browser Speech

A real-time voice agent powered by **Pipecat framework**, **Groq AI**, and **Browser Speech APIs** for free, high-quality voice conversations.

## 🚀 Features

- **Advanced Pipeline Processing**: Built on Pipecat framework for robust real-time audio processing
- **Groq LLM Integration**: Lightning-fast AI responses using Groq's optimized language models
- **Browser TTS**: High-quality text-to-speech using Web Speech API (FREE)
- **Browser STT**: Accurate speech-to-text using Web Speech API (FREE)
- **Voice Activity Detection**: Optional VAD for better conversation flow
- **Interruption Handling**: Advanced pipeline interruption capabilities
- **Real-time WebSocket Communication**: Low-latency bidirectional communication
- **Professional Audio Quality**: Browser-native audio processing
- **Comprehensive Monitoring**: Detailed latency tracking and performance metrics
- **No API Costs**: Only requires Groq API key - TTS/STT are free!

## 🛠️ Technology Stack

- **Framework**: Pipecat (Real-time AI pipeline framework)
- **LLM**: Groq (llama-3.3-70b-versatile)
- **TTS**: Browser Web Speech API (FREE)
- **STT**: Browser Web Speech API (FREE)
- **Backend**: FastAPI + WebSockets
- **Frontend**: Modern HTML5 + JavaScript
- **Audio**: WebRTC + MediaRecorder API

## 📋 Prerequisites

1. **Python 3.8+**
2. **Groq API Key** - Get from [Groq Console](https://console.groq.com)
3. **Modern Browser** with Web Speech API support (Chrome, Edge, Safari)

## 🔧 Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd pipecat-groq
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your Groq API key:

```env
# Groq API Configuration (REQUIRED)
GROQ_API_KEY=your_groq_api_key_here
```

**That's it!** No other API keys or services needed.

### 3. Run the Application

```bash
python main.py
```

The application will start on `http://localhost:8000`

## 🎯 Usage

### Web Interface

1. Open your browser to `http://localhost:8000`
2. Grant microphone permissions when prompted
3. **Hold the microphone button** to speak (push-to-talk mode)
4. **Type messages** in the chat input for text-based conversations
5. AI responses will be automatically converted to speech using browser TTS

### API Endpoints

- `GET /` - Web interface
- `GET /health` - Health check with service status
- `WebSocket /ws/{session_id}` - Real-time voice communication

### Configuration Options

- **Voice Activity Detection**: Optional VAD for automatic speech detection
- **Interruption Handling**: Allows interrupting the AI while it's speaking
- **Auto-play Responses**: Automatically plays AI responses as audio
- **Voice Visualization**: Visual feedback during voice interactions

## 🎛️ Pipecat Pipeline Architecture

The application uses Pipecat's pipeline processing concepts:

```
Audio Input → Browser STT → User Processing → Groq LLM → Browser TTS → Audio Output
     ↑                                                                      ↓
Optional VAD                                              Pipeline Response Handler
```

### Pipeline Components

1. **Voice Activity Detection (Optional)**: For automatic speech detection
2. **Speech-to-Text**: Browser Web Speech API for transcription
3. **User Processing**: Pipecat-inspired input handling
4. **Groq LLM Service**: Fast AI response generation
5. **Text-to-Speech**: Browser Web Speech API for natural voice synthesis
6. **Response Handler**: Manages AI response delivery

## 📊 Performance Monitoring

The application includes comprehensive performance tracking:

- **Pipeline Stage Latencies**: Individual stage timing
- **Service Performance**: Groq LLM timing
- **End-to-End Response Time**: Complete request processing time
- **WebSocket Communication**: Real-time message latency

View performance metrics in the browser console and server logs.

## 🔧 Advanced Configuration

### Audio Settings

```env
AUDIO_SAMPLE_RATE=24000    # High-quality audio
AUDIO_CHUNK_SIZE=1024      # Optimized for real-time processing
AUDIO_CHANNELS=1           # Mono audio for efficiency
```

### Pipecat Settings

```env
ENABLE_INTERRUPTIONS=true  # Allow interrupting AI responses
VAD_ENABLED=false         # Voice activity detection (optional)
```

### Browser Speech Settings

The application automatically uses the best available voices in your browser:
- **Chrome**: Google voices
- **Edge**: Microsoft voices
- **Safari**: Apple voices
- **Firefox**: Basic synthesis voices

## 🚨 Troubleshooting

### Common Issues

1. **"Groq API error"**
   - Check your `GROQ_API_KEY` is valid
   - Verify you have sufficient API credits

2. **"Speech not working"**
   - Ensure you're using a supported browser (Chrome, Edge, Safari)
   - Grant microphone permissions
   - Check browser speech synthesis support

3. **"WebSocket connection failed"**
   - Ensure port 8000 is available
   - Check firewall settings

4. **"Audio not recording"**
   - Grant microphone permissions in your browser
   - Check audio settings in the web interface

### Debug Mode

Run with verbose logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 🎯 Use Cases

- **Virtual Assistants**: Build sophisticated voice-enabled applications
- **Customer Support**: Real-time voice interaction systems
- **Education**: Interactive learning and tutoring systems
- **Accessibility**: Voice-controlled interfaces for accessibility
- **Prototyping**: Rapid development of voice AI applications

## 💰 Cost Efficiency

- **Groq API**: Pay only for LLM tokens used
- **Browser TTS**: Completely free, runs locally
- **Browser STT**: Completely free, runs locally
- **No Additional Services**: No Google Cloud, Azure, or AWS costs

## 📈 Browser Compatibility

| Browser | TTS Support | STT Support | Quality |
|---------|-------------|-------------|---------|
| Chrome  | ✅ Excellent | ✅ Excellent | High |
| Edge    | ✅ Excellent | ✅ Excellent | High |
| Safari  | ✅ Good     | ✅ Good     | Medium |
| Firefox | ✅ Basic    | ✅ Basic    | Basic |

## 🤝 Contributing

This implementation demonstrates:
- Real-time AI pipeline architecture using Pipecat concepts
- Browser-based speech services integration
- Production-ready voice AI systems
- Comprehensive error handling and monitoring
- Cost-effective voice AI solutions

## 📄 License

This project demonstrates advanced voice AI implementation patterns and is intended for educational and development purposes.

---

**Built with ❤️ using Pipecat, Groq AI, and Browser Speech APIs**