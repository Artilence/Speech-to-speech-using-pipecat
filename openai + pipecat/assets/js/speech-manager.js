/**
 * Speech Manager Module
 * Handles speech recognition functionality
 */
export class SpeechManager {
    constructor() {
        this.recognition = null;
        this.isRecording = false;
        this.accumulatedTranscript = "";
        this.callbacks = {
            onStart: [],
            onResult: [],
            onEnd: [],
            onError: []
        };
        
        this.initializeSpeechRecognition();
    }

    initializeSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            this.notifyCallbacks('onError', 'Speech recognition not supported in this browser. Please use Chrome or Safari.');
            return false;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = "en-US";

        this.recognition.onresult = (event) => {
            let interimTranscript = "";
            let finalTranscript = "";
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcriptText = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcriptText;
                } else {
                    interimTranscript += transcriptText;
                }
            }

            // Notify with current transcription
            const currentText = finalTranscript || interimTranscript;
            if (currentText) {
                this.notifyCallbacks('onResult', {
                    interim: interimTranscript,
                    final: finalTranscript,
                    current: currentText
                });
            }

            // Accumulate final results
            if (finalTranscript) {
                this.accumulatedTranscript += finalTranscript;
            }
        };

        this.recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            this.notifyCallbacks('onError', `Speech recognition error: ${event.error}. Please check microphone permissions.`);
            this.stop();
        };

        this.recognition.onend = () => {
            if (this.isRecording) {
                // Restart if we're still supposed to be recording
                try {
                    this.recognition.start();
                } catch (e) {
                    console.error("Failed to restart recognition:", e);
                    this.stop();
                }
            }
        };

        return true;
    }

    start() {
        if (!this.recognition) {
            this.notifyCallbacks('onError', 'Speech recognition not available');
            return false;
        }

        try {
            this.accumulatedTranscript = "";
            this.isRecording = true;
            this.recognition.start();
            this.notifyCallbacks('onStart');
            return true;
        } catch (e) {
            console.error("Failed to start recording:", e);
            this.notifyCallbacks('onError', 'Could not start recording. Please check microphone permissions.');
            this.reset();
            return false;
        }
    }

    stop() {
        if (!this.isRecording) return "";
        
        this.isRecording = false;
        
        if (this.recognition) {
            this.recognition.stop();
        }
        
        const finalTranscript = this.accumulatedTranscript.trim();
        this.notifyCallbacks('onEnd', finalTranscript);
        return finalTranscript;
    }

    reset() {
        this.isRecording = false;
        this.accumulatedTranscript = "";
    }

    isSupported() {
        return this.recognition !== null;
    }

    getRecordingState() {
        return this.isRecording;
    }

    getAccumulatedTranscript() {
        return this.accumulatedTranscript;
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