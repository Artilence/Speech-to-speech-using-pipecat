/**
 * UI Controller Module
 * Handles user interface updates and interactions
 */
export class UIController {
    constructor() {
        this.elements = {};
        this.initializeElements();
        this.createConnectionStatusIndicator();
    }

    initializeElements() {
        this.elements = {
            messages: document.getElementById("messages"),
            voiceChunks: document.getElementById("voiceChunks"),
            transcript: document.getElementById("transcript"),
            errorDiv: document.getElementById("error"),
            statusDiv: document.getElementById("status"),
            input: document.getElementById("input"),
            audioPlayer: document.getElementById("audioPlayer"),
            startBtn: document.getElementById("startBtn"),
            stopBtn: document.getElementById("stopBtn"),
            sendBtn: document.getElementById("sendBtn"),
            recordingIndicator: document.getElementById("recordingIndicator")
        };
    }

    createConnectionStatusIndicator() {
        // Create connection status indicator
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'connectionStatus';
        statusIndicator.className = 'connection-status disconnected';
        statusIndicator.textContent = 'Disconnected';
        document.body.appendChild(statusIndicator);
        this.elements.connectionStatus = statusIndicator;
    }

    showError(message) {
        this.elements.errorDiv.textContent = message;
        this.elements.errorDiv.style.display = "block";
        this.elements.statusDiv.style.display = "none";
    }

    showStatus(message) {
        this.elements.statusDiv.textContent = message;
        this.elements.statusDiv.style.display = "block";
        this.elements.errorDiv.style.display = "none";
    }

    hideError() {
        this.elements.errorDiv.style.display = "none";
    }

    hideStatus() {
        this.elements.statusDiv.style.display = "none";
    }

    updateTranscript(text) {
        this.elements.transcript.textContent = text;
    }

    clearTranscript() {
        this.elements.transcript.textContent = "";
    }

    addMessage(content, className = "") {
        const div = document.createElement("div");
        div.className = `message ${className}`;
        div.textContent = content;
        this.elements.messages.appendChild(div);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    addVoiceChunk(content) {
        const div = document.createElement("div");
        div.className = "message voice-chunk";
        div.textContent = `[${new Date().toLocaleTimeString()}] ${content}`;
        this.elements.voiceChunks.appendChild(div);
        this.elements.voiceChunks.scrollTop = this.elements.voiceChunks.scrollHeight;
    }

    clearVoiceChunks() {
        this.elements.voiceChunks.innerHTML = "";
    }

    playAudio(audioBase64) {
        try {
            this.elements.audioPlayer.src = `data:audio/mp3;base64,${audioBase64}`;
            this.elements.audioPlayer.play().catch(e => console.error("Audio play failed:", e));
        } catch (error) {
            console.error("Error playing audio:", error);
        }
    }

    setRecordingState(isRecording) {
        this.elements.startBtn.disabled = isRecording;
        this.elements.stopBtn.disabled = !isRecording;
        
        if (isRecording) {
            this.elements.recordingIndicator.classList.add('active');
        } else {
            this.elements.recordingIndicator.classList.remove('active');
        }
    }

    setConnectionState(state) {
        const { connectionStatus, startBtn, sendBtn } = this.elements;
        
        // Update connection status indicator
        connectionStatus.className = `connection-status ${state}`;
        
        const statusText = {
            'connected': 'Connected',
            'disconnected': 'Disconnected',
            'reconnecting': 'Reconnecting...',
            'error': 'Connection Error',
            'failed': 'Connection Failed'
        };
        
        connectionStatus.textContent = statusText[state] || state;
        
        // Update button states
        const isConnected = state === 'connected';
        startBtn.disabled = !isConnected;
        sendBtn.disabled = !isConnected;
        
        // Show appropriate status message
        if (state === 'connected') {
            this.showStatus("Connected to voice assistant!");
        } else if (state === 'disconnected') {
            this.showError("Disconnected from server");
        } else if (state === 'reconnecting') {
            this.showStatus("Reconnecting...");
        } else if (state === 'failed') {
            this.showError("Connection failed. Please refresh the page.");
        } else if (state === 'error') {
            this.showError("Connection error. Attempting to reconnect...");
        }
    }

    getInputValue() {
        return this.elements.input.value.trim();
    }

    clearInput() {
        this.elements.input.value = "";
    }

    setLoadingState(isLoading) {
        const container = document.querySelector('.container');
        if (isLoading) {
            container.classList.add('loading');
        } else {
            container.classList.remove('loading');
        }
    }

    setupEventListeners(callbacks) {
        if (callbacks.onStartClick) {
            this.elements.startBtn.addEventListener('click', callbacks.onStartClick);
        }

        if (callbacks.onStopClick) {
            this.elements.stopBtn.addEventListener('click', callbacks.onStopClick);
        }

        if (callbacks.onSendClick) {
            this.elements.sendBtn.addEventListener('click', callbacks.onSendClick);
        }

        if (callbacks.onInputKeyPress) {
            this.elements.input.addEventListener("keypress", (e) => {
                if (e.key === "Enter") {
                    callbacks.onInputKeyPress();
                }
            });
        }
    }

    validateSecureConnection() {
        if (window.location.protocol !== "https:" && 
            window.location.hostname !== "localhost" && 
            window.location.hostname !== "127.0.0.1") {
            this.showError("Speech recognition requires HTTPS. Please use a secure connection or localhost.");
            return false;
        }
        return true;
    }
}