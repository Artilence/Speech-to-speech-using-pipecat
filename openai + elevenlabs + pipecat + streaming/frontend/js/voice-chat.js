/**
 * Voice Chat Streaming - Client-side JavaScript
 * Handles WebSocket communication, speech recognition, and audio playback
 */

class VoiceCall {
    constructor() {
        this.ws = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.isOnCall = false;
        this.isConnected = false;
        this.conversationHistory = [];
        this.currentAudio = null;
        this.currentAiMessage = null; // For streaming responses
        this.liveTranscriptionElement = null; // For live speech display
        
        this.initializeElements();
        this.connectWebSocket();
        this.setupEventListeners();
    }

    initializeElements() {
        this.chatArea = document.getElementById('chatArea');
        this.callButton = document.getElementById('callButton');
        this.callStatus = document.getElementById('callStatus');
        this.status = document.getElementById('status');
        this.connectionIndicator = document.getElementById('connectionIndicator');
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/stream-chat`;
        
        console.log('🔗 Connecting to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.isConnected = true;
            console.log('✅ WebSocket connected successfully');
            this.updateStatus('Connected - Ready to chat!', 'connected');
            this.addSystemMessage('Connected to streaming voice chat');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('📨 Received message:', message.type, message);
                this.handleWebSocketMessage(message);
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error, event.data);
            }
        };
        
        this.ws.onclose = (event) => {
            this.isConnected = false;
            console.log('📞 WebSocket closed:', event.code, event.reason);
            this.updateStatus('Disconnected', 'disconnected');
            this.addSystemMessage('Disconnected from server');
            
            // Auto-reconnect after 3 seconds if it wasn't a clean close
            if (event.code !== 1000) {
                setTimeout(() => {
                    console.log('🔄 Attempting to reconnect...');
                    this.connectWebSocket();
                }, 3000);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateStatus('Connection error', 'disconnected');
        };
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'ai_typing':
                this.callStatus.textContent = '🤖 AI is thinking...';
                break;
                
            case 'ai_response_start':
                // Create a new AI message container for streaming
                this.currentAiMessage = document.createElement('div');
                this.currentAiMessage.className = 'message ai current-response';
                this.currentAiMessage.textContent = '';
                this.chatArea.appendChild(this.currentAiMessage);
                this.scrollToBottom();
                break;
                
            case 'ai_chunk':
                // Add chunk to current AI message
                if (this.currentAiMessage) {
                    this.currentAiMessage.textContent = message.full_text;
                    this.scrollToBottom();
                }
                this.callStatus.textContent = '🔴 On Call - AI is responding...';
                break;
                
            case 'ai_response_complete':
                // Finalize the AI response
                if (this.currentAiMessage) {
                    this.currentAiMessage.className = 'message ai'; // Remove current-response class
                    this.currentAiMessage.textContent = `AI: ${message.content}`;
                    this.currentAiMessage = null;
                } else {
                    // Fallback if no streaming message was created
                    this.addCallMessage(`AI: ${message.content}`, 'ai');
                }
                this.callStatus.textContent = '🔴 On Call - Speak naturally';
                break;
                
            case 'audio_chunk':
                this.playAudio(message.content);
                console.log('Playing audio for:', message.text || 'audio chunk');
                break;
                
            case 'ai_response':
                // Legacy support for non-streaming responses
                this.addCallMessage(`AI: ${message.content}`, 'ai');
                this.callStatus.textContent = '🔴 On Call - Speak naturally';
                break;
                
            case 'audio_response':
                // Legacy support for audio responses
                this.playAudio(message.content);
                break;
                
            case 'system':
                this.addCallMessage(message.content, 'system');
                break;
                
            case 'error':
                this.addCallMessage(`❌ Error: ${message.content}`, 'error');
                console.error('WebSocket error:', message.content);
                break;
                
            default:
                console.log('Unknown message type:', message.type, message);
        }
    }

    setupEventListeners() {
        // Call button - toggle call
        this.callButton.addEventListener('click', () => this.toggleCall());
    }
    
    toggleCall() {
        if (this.isOnCall) {
            this.endCall();
        } else {
            this.startCall();
        }
    }

    async startCall() {
        if (!this.isConnected || this.isOnCall) return;
        
        try {
            // Check if browser supports speech recognition
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                this.callStatus.textContent = 'Speech recognition not supported in this browser';
                return;
            }
            
            // Initialize speech recognition
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            
            this.isOnCall = true;
            let finalTranscript = '';
            
            // Update UI
            this.callButton.className = 'call-button active';
            this.callButton.innerHTML = '📞 End Call';
            this.callStatus.textContent = '🔴 On Call - Speak naturally';
            
            // Clear welcome message and show call started
            this.clearChatArea();
            this.addCallMessage('📞 Call started with AI', 'system');
            
            this.recognition.onresult = (event) => {
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                        // Remove any interim transcription display before showing final
                        this.removeLiveTranscription();
                        this.sendTranscription(transcript.trim());
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                // Show live transcription as user speaks
                if (interimTranscript.trim()) {
                    this.showLiveTranscription(interimTranscript.trim());
                    this.callStatus.textContent = `🎤 Speaking: "${interimTranscript.trim()}"`;
                } else {
                    this.removeLiveTranscription();
                    this.callStatus.textContent = '🔴 On Call - Speak naturally';
                }
            };
            
            this.recognition.onend = () => {
                if (this.isOnCall) {
                    // Restart recognition if call is still active
                    setTimeout(() => {
                        if (this.isOnCall) {
                            this.recognition.start();
                        }
                    }, 100);
                }
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                if (this.isOnCall) {
                    this.callStatus.textContent = '🔴 On Call - Speak naturally';
                }
            };
            
            this.recognition.start();
            
        } catch (error) {
            console.error('Error starting call:', error);
            this.callStatus.textContent = 'Failed to start speech recognition';
        }
    }

    endCall() {
        if (!this.isOnCall) return;
        
        this.isOnCall = false;
        
        if (this.recognition) {
            this.recognition.stop();
        }
        
        // Clean up live transcription
        this.removeLiveTranscription();
        
        // Update UI
        this.callButton.className = 'call-button inactive';
        this.callButton.innerHTML = '📞 Start Call';
        this.callStatus.textContent = 'Call ended';
        
        // Add call ended message
        this.addCallMessage('📞 Call ended', 'system');
        
        setTimeout(() => {
            this.callStatus.textContent = 'Ready to call';
        }, 2000);
    }

    showLiveTranscription(text) {
        // Remove any existing live transcription
        this.removeLiveTranscription();
        
        // Create new live transcription element
        this.liveTranscriptionElement = document.createElement('div');
        this.liveTranscriptionElement.className = 'message live-transcription';
        this.liveTranscriptionElement.textContent = `🎤 "${text}"`;
        this.liveTranscriptionElement.id = 'live-transcription';
        
        this.chatArea.appendChild(this.liveTranscriptionElement);
        this.scrollToBottom();
    }
    
    removeLiveTranscription() {
        if (this.liveTranscriptionElement) {
            this.liveTranscriptionElement.remove();
            this.liveTranscriptionElement = null;
        }
        
        // Also remove by ID in case reference is lost
        const existingLive = document.getElementById('live-transcription');
        if (existingLive) {
            existingLive.remove();
        }
    }

    sendTranscription(text) {
        if (!this.isConnected || !text.trim()) {
            console.log('Cannot send transcription:', { connected: this.isConnected, text: text.trim() });
            return;
        }
        
        try {
            console.log('📤 Sending transcription:', text.trim());
            
            this.sendWebSocketMessage({
                type: 'user_speech',
                content: text.trim()
            });
            
            // Show user speech in chat immediately
            this.addCallMessage(`You: ${text.trim()}`, 'user');
            
            // Update status to show we're waiting for AI
            this.callStatus.textContent = '🤖 Waiting for AI response...';
            
        } catch (error) {
            console.error('❌ Error sending transcription:', error);
            this.addCallMessage(`❌ Failed to send message: ${error.message}`, 'error');
        }
    }

    sendWebSocketMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                console.log('📤 Sending WebSocket message:', message.type, message);
                this.ws.send(JSON.stringify(message));
            } catch (error) {
                console.error('❌ Error sending WebSocket message:', error);
                this.addCallMessage(`❌ Failed to send message: ${error.message}`, 'error');
            }
        } else {
            console.error('❌ WebSocket not connected. Ready state:', this.ws?.readyState);
            this.addCallMessage('❌ Not connected to server', 'error');
        }
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = content;
        this.chatArea.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addCallMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = content;
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString();
        messageDiv.setAttribute('title', timestamp);
        
        this.chatArea.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Store in conversation history
        this.conversationHistory.push({
            content: content,
            sender: sender,
            timestamp: timestamp
        });
    }
    
    clearChatArea() {
        this.chatArea.innerHTML = '';
        this.conversationHistory = [];
    }
    
    playAudio(audioB64) {
        try {
            const audioBlob = this.base64ToBlob(audioB64, 'audio/mp3');
            const audioUrl = URL.createObjectURL(audioBlob);
            
            this.currentAudio = new Audio(audioUrl);
            this.currentAudio.play();
            
            this.currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
            };
        } catch (error) {
            console.error('Audio playback error:', error);
        }
    }

    addSystemMessage(content, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.textContent = content;
        this.chatArea.appendChild(messageDiv);
        this.scrollToBottom();
    }

    playAudioResponse(base64Audio) {
        try {
            const audioBlob = this.base64ToBlob(base64Audio, 'audio/mp3');
            const audioUrl = URL.createObjectURL(audioBlob);
            
            this.currentAudio = new Audio(audioUrl);
            this.currentAudio.play();
            
            this.currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
            };
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

    base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], { type: mimeType });
    }

    updateStatus(message, type) {
        this.status.textContent = message;
        this.connectionIndicator.className = `connection-indicator ${type === 'connected' ? '' : 'disconnected'}`;
    }

    scrollToBottom() {
        this.chatArea.scrollTop = this.chatArea.scrollHeight;
    }
}

// Initialize the app when the page loads
window.addEventListener('DOMContentLoaded', () => {
    new VoiceCall();
});