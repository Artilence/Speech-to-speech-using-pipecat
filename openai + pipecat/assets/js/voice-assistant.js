/**
 * Voice Assistant Main Module
 * Orchestrates all components for the voice assistant functionality
 */
import { WebSocketClient } from './websocket-client.js';
import { SpeechManager } from './speech-manager.js';
import { UIController } from './ui-controller.js';

export class VoiceAssistant {
    constructor() {
        this.websocketClient = new WebSocketClient();
        this.speechManager = new SpeechManager();
        this.uiController = new UIController();
        this.keepaliveInterval = null;
        
        this.initialize();
    }

    initialize() {
        this.setupWebSocketHandlers();
        this.setupSpeechHandlers();
        this.setupUIEventHandlers();
        this.startKeepalive();
        
        // Validate environment and connect
        if (this.uiController.validateSecureConnection()) {
            if (this.speechManager.isSupported()) {
                this.websocketClient.connect();
            }
        }
    }

    setupWebSocketHandlers() {
        // Connection state changes
        this.websocketClient.onConnectionStateChange((state) => {
            this.uiController.setConnectionState(state);
        });

        // Message handlers
        this.websocketClient.onMessage('message', (data) => {
            this.uiController.addMessage("🤖 " + data.content, "bot-message");
        });

        this.websocketClient.onMessage('voice_chunk', (data) => {
            this.uiController.addVoiceChunk(data.content);
        });

        this.websocketClient.onMessage('audio', (data) => {
            this.uiController.playAudio(data.content);
        });

        this.websocketClient.onMessage('error', (data) => {
            this.uiController.showError(`Server error: ${data.content}`);
        });

        this.websocketClient.onMessage('info', (data) => {
            this.uiController.addMessage("ℹ️ " + data.content, "info-message");
        });

        this.websocketClient.onMessage('keepalive', () => {
            // Just acknowledge the keepalive
        });

        this.websocketClient.onMessage('pong', () => {
            // Response to our ping
        });
    }

    setupSpeechHandlers() {
        this.speechManager.onStart(() => {
            this.uiController.setRecordingState(true);
            this.uiController.clearVoiceChunks();
            this.uiController.showStatus("Recording started. Speak now!");
            
            // Notify server
            this.websocketClient.sendStartRecording();
        });

        this.speechManager.onResult((result) => {
            this.uiController.updateTranscript(`Transcribing: ${result.current}`);
            
            // Send voice chunk to server for real-time display
            if (result.current) {
                this.websocketClient.sendVoiceChunk(result.current);
            }
        });

        this.speechManager.onEnd((finalTranscript) => {
            this.uiController.setRecordingState(false);
            this.uiController.clearTranscript();
            
            // Send final transcript to server
            if (finalTranscript) {
                this.websocketClient.sendStopRecording(finalTranscript);
                this.uiController.addMessage("👤 " + finalTranscript, "user-message");
            } else {
                this.uiController.showError("No speech detected. Please try again.");
            }
        });

        this.speechManager.onError((error) => {
            this.uiController.showError(error);
            this.uiController.setRecordingState(false);
        });
    }

    setupUIEventHandlers() {
        this.uiController.setupEventListeners({
            onStartClick: () => this.startRecording(),
            onStopClick: () => this.stopRecording(),
            onSendClick: () => this.sendTextMessage(),
            onInputKeyPress: () => this.sendTextMessage()
        });

        // Handle page visibility for connection management
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && !this.websocketClient.isConnected()) {
                this.websocketClient.connect();
            }
        });

        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.destroy();
        });
    }

    startRecording() {
        if (!this.speechManager.isSupported()) {
            this.uiController.showError("Speech recognition not available");
            return;
        }

        if (!this.websocketClient.isConnected()) {
            this.uiController.showError("Not connected to server");
            return;
        }

        this.speechManager.start();
    }

    stopRecording() {
        this.speechManager.stop();
    }

    sendTextMessage() {
        const text = this.uiController.getInputValue();
        
        if (!text) {
            return;
        }

        if (!this.websocketClient.isConnected()) {
            this.uiController.showError("Cannot send message: Not connected to server");
            return;
        }

        this.websocketClient.sendTextMessage(text);
        this.uiController.addMessage("👤 " + text, "user-message");
        this.uiController.clearInput();
    }

    startKeepalive() {
        this.keepaliveInterval = setInterval(() => {
            if (this.websocketClient.isConnected()) {
                this.websocketClient.sendPing();
            }
        }, 30000); // 30 seconds
    }

    destroy() {
        if (this.keepaliveInterval) {
            clearInterval(this.keepaliveInterval);
        }
        this.websocketClient.disconnect();
        this.speechManager.reset();
    }
}