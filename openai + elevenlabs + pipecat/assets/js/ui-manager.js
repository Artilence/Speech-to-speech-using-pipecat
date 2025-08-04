/**
 * UI Manager
 * Handles user interface updates and state management
 */
export class UIManager {
    constructor() {
        this.elements = {};
        this.initializeElements();
    }

    initializeElements() {
        this.elements = {
            status: document.getElementById('status'),
            micButton: document.getElementById('micButton'),
            transcript: document.getElementById('transcript'),
            conversation: document.getElementById('conversation'),
            clearBtn: document.getElementById('clearBtn'),
            muteBtn: document.getElementById('muteBtn'),
            visualizer: document.getElementById('audioVisualizer')
        };
    }

    updateMicButton(state) {
        const { micButton } = this.elements;
        
        switch (state) {
            case 'listening':
                micButton.className = 'mic-button listening';
                micButton.innerHTML = '🔴';
                break;
            case 'processing':
                micButton.className = 'mic-button processing';
                micButton.innerHTML = '⏳';
                break;
            case 'idle':
            default:
                micButton.className = 'mic-button';
                micButton.innerHTML = '🎤';
                break;
        }
    }

    updateStatus(message, className) {
        const { status } = this.elements;
        status.textContent = message;
        status.className = `status ${className}`;
    }

    updateTranscript(text) {
        this.elements.transcript.textContent = text;
    }

    addMessage(text, sender) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}-message`;
        messageEl.textContent = sender === 'user' ? `You: ${text}` : `Assistant: ${text}`;
        this.elements.conversation.appendChild(messageEl);
        this.elements.conversation.scrollTop = this.elements.conversation.scrollHeight;
    }

    showError(message) {
        const errorEl = document.createElement('div');
        errorEl.className = 'error';
        errorEl.textContent = message;
        this.elements.conversation.appendChild(errorEl);
        this.elements.conversation.scrollTop = this.elements.conversation.scrollHeight;
        
        setTimeout(() => {
            if (errorEl.parentNode) {
                errorEl.parentNode.removeChild(errorEl);
            }
        }, 5000);
    }

    clearConversation() {
        this.elements.conversation.innerHTML = `
            <div class="message ai-message">
                👋 Hi! I'm your voice assistant. Click the microphone button and start speaking!
            </div>
        `;
    }

    updateMuteButton(isMuted) {
        const { muteBtn } = this.elements;
        muteBtn.textContent = isMuted ? 'Unmute Audio' : 'Mute Audio';
        muteBtn.style.background = isMuted ? 
            'linear-gradient(135deg, #f56565, #e53e3e)' : 
            'linear-gradient(135deg, #667eea, #764ba2)';
    }

    showVisualizer() {
        this.elements.visualizer.style.display = 'flex';
    }

    hideVisualizer() {
        this.elements.visualizer.style.display = 'none';
    }

    enableMicButton() {
        this.elements.micButton.disabled = false;
    }

    disableMicButton() {
        this.elements.micButton.disabled = true;
    }

    setupEventListeners(callbacks) {
        const { micButton, clearBtn, muteBtn } = this.elements;
        
        if (callbacks.onMicClick) {
            micButton.addEventListener('click', callbacks.onMicClick);
        }
        
        if (callbacks.onClearClick) {
            clearBtn.addEventListener('click', callbacks.onClearClick);
        }
        
        if (callbacks.onMuteClick) {
            muteBtn.addEventListener('click', callbacks.onMuteClick);
        }
        
        // Keyboard shortcuts
        if (callbacks.onKeyboardShortcut) {
            document.addEventListener('keydown', (event) => {
                if (event.code === 'Space' && event.ctrlKey) {
                    event.preventDefault();
                    callbacks.onKeyboardShortcut();
                }
            });
        }
    }
}