/**
 * Speech Recognition Manager
 * Handles speech recognition functionality
 */
export class SpeechRecognitionManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.callbacks = {
            onStart: [],
            onResult: [],
            onEnd: [],
            onError: []
        };
        
        this.initializeSpeechRecognition();
    }

    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.notifyCallbacks('onStart');
            };
            
            this.recognition.onresult = (event) => {
                let interim = '';
                let final = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        final += transcript;
                    } else {
                        interim += transcript;
                    }
                }
                
                this.notifyCallbacks('onResult', { interim, final });
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.notifyCallbacks('onError', event.error);
                this.stop();
            };
            
            this.recognition.onend = () => {
                this.stop();
            };
        } else {
            this.notifyCallbacks('onError', 'Speech recognition not supported in this browser');
        }
    }

    start() {
        if (this.recognition && !this.isListening) {
            this.recognition.start();
            return true;
        }
        return false;
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            this.notifyCallbacks('onEnd');
        }
    }

    isSupported() {
        return this.recognition !== null;
    }

    getListeningState() {
        return this.isListening;
    }

    onStart(callback) {
        this.callbacks.onStart.push(callback);
    }

    onResult(callback) {
        this.callbacks.onResult.push(callback);
    }

    onEnd(callback) {
        this.callbacks.onEnd.push(callback);
    }

    onError(callback) {
        this.callbacks.onError.push(callback);
    }

    notifyCallbacks(type, data = null) {
        this.callbacks[type].forEach(callback => callback(data));
    }
}