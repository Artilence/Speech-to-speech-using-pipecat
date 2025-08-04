/**
 * Main VoiceCall class - orchestrates all components
 */

class VoiceCall {
    constructor() {
        // Initialize managers
        this.ui = new UIManager();
        this.audio = new AudioManager();
        
        // Initialize WebSocket with callbacks
        this.websocket = new WebSocketManager({
            onOpen: () => this.handleWebSocketOpen(),
            onMessage: (message) => this.handleWebSocketMessage(message),
            onClose: (event) => this.handleWebSocketClose(event),
            onError: (error) => this.handleWebSocketError(error)
        });
        
        // Initialize speech recognition with callbacks
        this.speechRecognition = new SpeechRecognitionManager({
            onResult: (text) => this.handleSpeechResult(text),
            onInterimResult: (text) => this.handleInterimSpeechResult(text),
            onStart: () => this.handleSpeechStart(),
            onEnd: () => this.handleSpeechEnd(),
            onError: (error) => this.handleSpeechError(error)
        });
        
        // State
        this.isOnCall = false;
        this.isConnected = false;
        
        this.initialize();
    }
    
    initialize() {
        // Set up UI event handlers
        this.ui.setCallButtonHandler(() => this.toggleCall());
        
        // Connect to WebSocket
        this.websocket.connect();
        
        // Show welcome message
        this.ui.showWelcomeMessage();
        
        // Update initial status
        this.ui.updateConnectionStatus('Connecting...', false);
        this.ui.updateCallStatus('Ready to call');
        
        // Handle responsive layout
        this.ui.updateResponsiveLayout();
        window.addEventListener('resize', () => this.ui.updateResponsiveLayout());
        
        console.log('🎙️ VoiceCall initialized');
    }
    
    // WebSocket Event Handlers
    handleWebSocketOpen() {
        this.isConnected = true;
        this.ui.updateConnectionStatus('Connected - Ready to chat!', true);
        this.ui.addSystemMessage('Connected to streaming voice chat');
    }
    
    handleWebSocketClose(event) {
        this.isConnected = false;
        this.ui.updateConnectionStatus('Disconnected', false);
        this.ui.addSystemMessage('Disconnected from server');
        
        // If we were on a call, end it
        if (this.isOnCall) {
            this.endCall();
        }
    }
    
    handleWebSocketError(error) {
        this.ui.updateConnectionStatus('Connection error', false);
        this.ui.addErrorMessage('Connection error occurred');
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'ai_typing':
                this.ui.updateCallStatus('🤖 AI is thinking...');
                break;
                
            case 'ai_response_start':
                this.ui.startAiResponse();
                break;
                
            case 'ai_chunk':
                this.ui.updateAiResponse(message.full_text || message.content);
                this.ui.updateCallStatus('🔴 On Call - AI is responding...');
                break;
                
            case 'ai_response_complete':
                this.ui.finishAiResponse(message.content);
                this.ui.updateCallStatus('🔴 On Call - Speak naturally');
                break;
                
            case 'audio_chunk':
                this.handleAudioChunk(message);
                break;
                
            case 'ai_response':
                // Legacy support for non-streaming responses
                this.ui.addMessage(`AI: ${message.content}`, 'ai');
                this.ui.updateCallStatus('🔴 On Call - Speak naturally');
                break;
                
            case 'audio_response':
                // Legacy support for audio responses
                this.audio.playAudio(message.content);
                break;
                
            case 'system':
                this.ui.addSystemMessage(message.content);
                break;
                
            case 'error':
                this.ui.addErrorMessage(message.content);
                console.error('WebSocket error:', message.content);
                break;
                
            default:
                console.log('Unknown message type:', message.type, message);
        }
    }
    
    // Speech Recognition Event Handlers
    handleSpeechResult(text) {
        // Remove live transcription and send final result
        this.ui.removeLiveTranscription();
        this.sendTranscription(text);
    }
    
    handleInterimSpeechResult(text) {
        // Show live transcription
        this.ui.showLiveTranscription(text);
        this.ui.updateCallStatus(`🎤 Speaking: "${text}"`);
    }
    
    handleSpeechStart() {
        console.log('🎤 Speech recognition started');
    }
    
    handleSpeechEnd() {
        console.log('🎤 Speech recognition ended');
        this.ui.removeLiveTranscription();
        
        // Restart if call is still active
        if (this.isOnCall) {
            this.ui.updateCallStatus('🔴 On Call - Speak naturally');
            // Restart recognition after a short delay
            setTimeout(() => {
                if (this.isOnCall) {
                    this.speechRecognition.start();
                }
            }, 100);
        }
    }
    
    handleSpeechError(error) {
        console.error('Speech recognition error:', error);
        if (this.isOnCall) {
            this.ui.updateCallStatus('🔴 On Call - Speak naturally');
        }
    }
    
    // Audio Handling
    handleAudioChunk(message) {
        const audioData = message.content;
        const text = message.text || 'audio chunk';
        
        console.log('🔊 Playing audio for:', text);
        this.audio.playAudio(audioData);
    }
    
    // Call Management
    toggleCall() {
        if (this.isOnCall) {
            this.endCall();
        } else {
            this.startCall();
        }
    }
    
    async startCall() {
        if (!this.isConnected || this.isOnCall) {
            console.warn('Cannot start call - not connected or already on call');
            return;
        }
        
        // Check speech recognition support
        if (!this.speechRecognition.isSupported) {
            this.ui.updateCallStatus('Speech recognition not supported in this browser');
            this.ui.showNotification('Speech recognition not supported in this browser', 'error');
            return;
        }
        
        try {
            this.isOnCall = true;
            
            // Update UI
            this.ui.updateCallButton(true);
            this.ui.updateCallStatus('🔴 On Call - Speak naturally');
            
            // Clear chat and show call started
            this.ui.clearChatArea();
            this.ui.addSystemMessage('📞 Call started with AI');
            
            // Start speech recognition
            if (!this.speechRecognition.startContinuous()) {
                throw new Error('Failed to start speech recognition');
            }
            
            console.log('📞 Call started successfully');
            
        } catch (error) {
            console.error('❌ Error starting call:', error);
            this.ui.updateCallStatus('Failed to start call');
            this.ui.addErrorMessage(`Failed to start call: ${error.message}`);
            this.isOnCall = false;
            this.ui.updateCallButton(false);
        }
    }
    
    endCall() {
        if (!this.isOnCall) return;
        
        console.log('📞 Ending call');
        
        this.isOnCall = false;
        
        // Stop speech recognition
        this.speechRecognition.stopContinuous();
        
        // Stop any playing audio
        this.audio.stopAll();
        
        // Clean up UI
        this.ui.removeLiveTranscription();
        this.ui.updateCallButton(false);
        this.ui.updateCallStatus('Call ended');
        
        // Add call ended message
        this.ui.addSystemMessage('📞 Call ended');
        
        // Reset status after delay
        setTimeout(() => {
            this.ui.updateCallStatus('Ready to call');
        }, 2000);
    }
    
    // Message Sending
    sendTranscription(text) {
        if (!this.isConnected || !text.trim()) {
            console.log('Cannot send transcription:', { 
                connected: this.isConnected, 
                text: text.trim() 
            });
            return;
        }
        
        try {
            console.log('📤 Sending transcription:', text.trim());
            
            // Send to WebSocket
            const success = this.websocket.sendUserSpeech(text.trim());
            
            if (success) {
                // Show user speech in chat immediately
                this.ui.addUserMessage(text.trim());
                
                // Update status to show we're waiting for AI
                this.ui.updateCallStatus('🤖 Waiting for AI response...');
            } else {
                throw new Error('Failed to send message via WebSocket');
            }
            
        } catch (error) {
            console.error('❌ Error sending transcription:', error);
            this.ui.addErrorMessage(`Failed to send message: ${error.message}`);
        }
    }
    
    // Utility Methods
    getStatus() {
        return {
            isConnected: this.isConnected,
            isOnCall: this.isOnCall,
            speechSupported: this.speechRecognition.isSupported,
            audioPlaying: this.audio.isAudioPlaying(),
            audioQueueLength: this.audio.getQueueLength()
        };
    }
    
    // Test Methods (for debugging)
    async testAudio() {
        const success = await this.audio.testAudio();
        this.ui.showNotification(
            success ? 'Audio test successful' : 'Audio test failed',
            success ? 'success' : 'error'
        );
        return success;
    }
    
    testSpeechRecognition() {
        const support = this.speechRecognition.getSupport();
        console.log('Speech recognition support:', support);
        this.ui.showNotification(
            support.isSupported ? 'Speech recognition supported' : 'Speech recognition not supported',
            support.isSupported ? 'success' : 'error'
        );
        return support;
    }
    
    // Cleanup
    destroy() {
        this.endCall();
        this.websocket.disconnect();
        this.audio.stopAll();
        console.log('🎙️ VoiceCall destroyed');
    }
}

// Export for use
window.VoiceCall = VoiceCall;

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.voiceCallApp = new VoiceCall();
    console.log('🎙️ VoiceCall application started');
});