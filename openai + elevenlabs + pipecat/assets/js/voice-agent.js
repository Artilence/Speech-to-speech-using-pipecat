/**
 * Voice Agent
 * Main orchestrator class that coordinates all components
 */
import { WebSocketManager } from './websocket-manager.js';
import { SpeechRecognitionManager } from './speech-recognition.js';
import { AudioPlayer } from './audio-player.js';
import { UIManager } from './ui-manager.js';
import { LatencyMonitor } from './latency-monitor.js';

export class VoiceAgent {
    constructor() {
        // Initialize all components
        this.websocketManager = new WebSocketManager();
        this.speechRecognition = new SpeechRecognitionManager();
        this.audioPlayer = new AudioPlayer();
        this.uiManager = new UIManager();
        this.latencyMonitor = new LatencyMonitor();
        
        // State management
        this.isProcessing = false;
        
        this.initialize();
    }

    initialize() {
        this.setupWebSocketHandlers();
        this.setupSpeechRecognitionHandlers();
        this.setupUIEventHandlers();
        this.connectWebSocket();
        
        // Check if speech recognition is supported
        if (!this.speechRecognition.isSupported()) {
            this.uiManager.showError('Speech recognition not supported in this browser');
        }
    }

    setupWebSocketHandlers() {
        // Connection state changes
        this.websocketManager.onConnectionStateChange((state) => {
            switch (state) {
                case 'connected':
                    this.uiManager.updateStatus('Connected', 'connected');
                    this.uiManager.enableMicButton();
                    break;
                case 'disconnected':
                    this.uiManager.updateStatus('Disconnected', 'disconnected');
                    this.uiManager.disableMicButton();
                    break;
                case 'error':
                    this.uiManager.showError('Connection error');
                    break;
            }
        });

        // Message handlers
        this.websocketManager.onMessage('processing', (message) => {
            this.isProcessing = true;
            this.updateUI();
            this.uiManager.updateStatus('Processing...', 'processing');
            this.audioPlayer.initializeStreamingAudio();
            this.latencyMonitor.resetLatencyDisplay();
        });

        this.websocketManager.onMessage('ai_response', (message) => {
            this.uiManager.addMessage(message.text, 'ai');
        });

        this.websocketManager.onMessage('audio_chunk', (message) => {
            this.audioPlayer.playAudioChunk(message.audio);
        });

        this.websocketManager.onMessage('audio_response', (message) => {
            if (message.is_final) {
                this.audioPlayer.finalizeStreamingAudio();
                this.isProcessing = false;
                this.updateUI();
                this.uiManager.updateStatus('Connected', 'connected');
            } else {
                // Legacy support for non-streaming audio
                this.audioPlayer.playAudioResponse(message.audio);
                this.isProcessing = false;
                this.updateUI();
                this.uiManager.updateStatus('Connected', 'connected');
            }
        });

        this.websocketManager.onMessage('latency_measurement', (message) => {
            this.latencyMonitor.updateLatencyDisplay(message);
        });

        this.websocketManager.onMessage('error', (message) => {
            this.uiManager.showError(message.message);
            this.isProcessing = false;
            this.updateUI();
        });

        this.websocketManager.onMessage('pong', () => {
            // Handle pong response if needed
        });
    }

    setupSpeechRecognitionHandlers() {
        this.speechRecognition.onStart(() => {
            this.updateUI();
            this.uiManager.updateTranscript('Listening...');
            this.uiManager.showVisualizer();
        });

        this.speechRecognition.onResult(({ interim, final }) => {
            this.uiManager.updateTranscript(final || interim || 'Listening...');
            
            if (final) {
                this.sendMessage(final);
            }
        });

        this.speechRecognition.onEnd(() => {
            this.updateUI();
            this.uiManager.hideVisualizer();
        });

        this.speechRecognition.onError((error) => {
            this.uiManager.showError(`Speech recognition error: ${error}`);
            this.stopListening();
        });
    }

    setupUIEventHandlers() {
        this.uiManager.setupEventListeners({
            onMicClick: () => {
                if (this.speechRecognition.getListeningState()) {
                    this.stopListening();
                } else {
                    this.startListening();
                }
            },
            
            onClearClick: () => {
                this.clearConversation();
            },
            
            onMuteClick: () => {
                this.toggleMute();
            },
            
            onKeyboardShortcut: () => {
                if (this.speechRecognition.getListeningState()) {
                    this.stopListening();
                } else {
                    this.startListening();
                }
            }
        });
    }

    connectWebSocket() {
        this.websocketManager.connect();
    }

    startListening() {
        if (!this.speechRecognition.getListeningState() && !this.isProcessing) {
            this.speechRecognition.start();
        }
    }

    stopListening() {
        this.speechRecognition.stop();
    }

    sendMessage(text) {
        if (this.websocketManager.isConnected()) {
            this.uiManager.addMessage(text, 'user');
            this.websocketManager.sendUserSpeech(text);
            this.uiManager.updateTranscript('Processing...');
        }
    }

    updateUI() {
        if (this.speechRecognition.getListeningState()) {
            this.uiManager.updateMicButton('listening');
        } else if (this.isProcessing) {
            this.uiManager.updateMicButton('processing');
        } else {
            this.uiManager.updateMicButton('idle');
        }
    }

    clearConversation() {
        this.uiManager.clearConversation();
        this.latencyMonitor.resetLatencyDisplay();
    }

    toggleMute() {
        const isMuted = this.audioPlayer.toggleMute();
        this.uiManager.updateMuteButton(isMuted);
    }
}