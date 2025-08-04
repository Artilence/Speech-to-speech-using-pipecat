/**
 * Speech Recognition Manager for handling browser speech recognition
 */

class SpeechRecognitionManager {
    constructor(eventCallbacks = {}) {
        this.recognition = null;
        this.isListening = false;
        this.isSupported = this.checkSupport();
        
        // Event callbacks
        this.callbacks = {
            onResult: eventCallbacks.onResult || (() => {}),
            onInterimResult: eventCallbacks.onInterimResult || (() => {}),
            onStart: eventCallbacks.onStart || (() => {}),
            onEnd: eventCallbacks.onEnd || (() => {}),
            onError: eventCallbacks.onError || (() => {})
        };
        
        this.init();
    }
    
    checkSupport() {
        return ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
    }
    
    init() {
        if (!this.isSupported) {
            console.warn('⚠️  Speech recognition not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        if (!this.recognition) return;
        
        this.recognition.onstart = () => {
            this.isListening = true;
            console.log('🎤 Speech recognition started');
            this.callbacks.onStart();
        };
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Handle interim results (live transcription)
            if (interimTranscript.trim()) {
                this.callbacks.onInterimResult(interimTranscript.trim());
            }
            
            // Handle final results
            if (finalTranscript.trim()) {
                this.callbacks.onResult(finalTranscript.trim());
            }
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            console.log('🎤 Speech recognition ended');
            this.callbacks.onEnd();
        };
        
        this.recognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            this.isListening = false;
            this.callbacks.onError(event.error);
        };
    }
    
    start() {
        if (!this.isSupported) {
            this.callbacks.onError('Speech recognition not supported');
            return false;
        }
        
        if (!this.isListening && this.recognition) {
            try {
                this.recognition.start();
                return true;
            } catch (error) {
                console.error('❌ Failed to start speech recognition:', error);
                this.callbacks.onError(error.message);
                return false;
            }
        }
        
        return false;
    }
    
    stop() {
        if (this.isListening && this.recognition) {
            this.recognition.stop();
        }
    }
    
    restart() {
        if (this.isListening) {
            this.stop();
            // Small delay to ensure clean restart
            setTimeout(() => {
                this.start();
            }, 100);
        }
    }
    
    // Continuous listening mode - restarts automatically when recognition ends
    startContinuous() {
        if (!this.start()) {
            return false;
        }
        
        // Override onend to restart automatically
        const originalOnEnd = this.callbacks.onEnd;
        this.callbacks.onEnd = () => {
            originalOnEnd();
            // Restart if we should still be listening
            if (this.shouldContinueListening) {
                setTimeout(() => {
                    if (this.shouldContinueListening) {
                        this.start();
                    }
                }, 100);
            }
        };
        
        this.shouldContinueListening = true;
        return true;
    }
    
    stopContinuous() {
        this.shouldContinueListening = false;
        this.stop();
    }
    
    getSupport() {
        return {
            isSupported: this.isSupported,
            hasWebkitSpeechRecognition: 'webkitSpeechRecognition' in window,
            hasSpeechRecognition: 'SpeechRecognition' in window
        };
    }
}

// Export for use in other modules
window.SpeechRecognitionManager = SpeechRecognitionManager;