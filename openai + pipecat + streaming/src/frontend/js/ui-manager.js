/**
 * UI Manager for handling user interface updates and interactions
 */

class UIManager {
    constructor() {
        this.elements = {};
        this.conversationHistory = [];
        this.currentAiMessage = null;
        this.liveTranscriptionElement = null;
        
        this.initializeElements();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.elements = {
            chatArea: document.getElementById('chatArea'),
            callButton: document.getElementById('callButton'),
            callStatus: document.getElementById('callStatus'),
            status: document.getElementById('status'),
            connectionIndicator: document.getElementById('connectionIndicator')
        };
        
        // Validate required elements
        const missingElements = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);
            
        if (missingElements.length > 0) {
            console.warn('⚠️  Missing UI elements:', missingElements);
        }
    }
    
    setupEventListeners() {
        // Call button event listener will be set by VoiceCall class
        // This allows for better separation of concerns
    }
    
    /**
     * Update connection status
     */
    updateConnectionStatus(message, isConnected = true) {
        if (this.elements.status) {
            this.elements.status.textContent = message;
        }
        
        if (this.elements.connectionIndicator) {
            this.elements.connectionIndicator.className = 
                `connection-indicator ${isConnected ? '' : 'disconnected'}`;
        }
    }
    
    /**
     * Update call status
     */
    updateCallStatus(message) {
        if (this.elements.callStatus) {
            this.elements.callStatus.textContent = message;
        }
    }
    
    /**
     * Update call button state
     */
    updateCallButton(isOnCall = false) {
        if (!this.elements.callButton) return;
        
        if (isOnCall) {
            this.elements.callButton.className = 'call-button active';
            this.elements.callButton.innerHTML = '📞 End Call';
        } else {
            this.elements.callButton.className = 'call-button inactive';
            this.elements.callButton.innerHTML = '📞 Start Call';
        }
    }
    
    /**
     * Add message to chat area
     */
    addMessage(content, sender, options = {}) {
        if (!this.elements.chatArea) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = content;
        
        // Add timestamp
        if (options.includeTimestamp !== false) {
            const timestamp = new Date().toLocaleTimeString();
            messageDiv.setAttribute('title', timestamp);
        }
        
        // Add custom classes if provided
        if (options.additionalClasses) {
            messageDiv.className += ` ${options.additionalClasses}`;
        }
        
        // Add custom ID if provided
        if (options.id) {
            messageDiv.id = options.id;
        }
        
        this.elements.chatArea.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Store in conversation history
        this.conversationHistory.push({
            content: content,
            sender: sender,
            timestamp: new Date().toLocaleTimeString(),
            options: options
        });
        
        return messageDiv;
    }
    
    /**
     * Add system message
     */
    addSystemMessage(content) {
        return this.addMessage(content, 'system');
    }
    
    /**
     * Add error message
     */
    addErrorMessage(content) {
        return this.addMessage(`❌ ${content}`, 'error');
    }
    
    /**
     * Add user message
     */
    addUserMessage(content) {
        return this.addMessage(`You: ${content}`, 'user');
    }
    
    /**
     * Start AI response (for streaming)
     */
    startAiResponse() {
        if (!this.elements.chatArea) return null;
        
        this.currentAiMessage = document.createElement('div');
        this.currentAiMessage.className = 'message ai current-response';
        this.currentAiMessage.textContent = '';
        this.currentAiMessage.id = 'current-ai-response';
        
        this.elements.chatArea.appendChild(this.currentAiMessage);
        this.scrollToBottom();
        
        return this.currentAiMessage;
    }
    
    /**
     * Update current AI response
     */
    updateAiResponse(fullText) {
        if (this.currentAiMessage) {
            this.currentAiMessage.textContent = fullText;
            this.scrollToBottom();
        }
    }
    
    /**
     * Finish AI response
     */
    finishAiResponse(finalText) {
        if (this.currentAiMessage) {
            this.currentAiMessage.className = 'message ai'; // Remove current-response class
            this.currentAiMessage.textContent = `AI: ${finalText}`;
            this.currentAiMessage.removeAttribute('id');
            this.currentAiMessage = null;
        }
    }
    
    /**
     * Show live transcription
     */
    showLiveTranscription(text) {
        // Remove any existing live transcription
        this.removeLiveTranscription();
        
        if (!this.elements.chatArea) return;
        
        // Create new live transcription element
        this.liveTranscriptionElement = document.createElement('div');
        this.liveTranscriptionElement.className = 'message live-transcription';
        this.liveTranscriptionElement.textContent = `🎤 "${text}"`;
        this.liveTranscriptionElement.id = 'live-transcription';
        
        this.elements.chatArea.appendChild(this.liveTranscriptionElement);
        this.scrollToBottom();
    }
    
    /**
     * Remove live transcription
     */
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
    
    /**
     * Clear chat area
     */
    clearChatArea() {
        if (this.elements.chatArea) {
            this.elements.chatArea.innerHTML = '';
        }
        this.conversationHistory = [];
        this.currentAiMessage = null;
        this.liveTranscriptionElement = null;
    }
    
    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        if (!this.elements.chatArea) return;
        
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.innerHTML = `
            <h3>📞 Voice Call with AI</h3>
            <p>Click the button below to start a real-time voice conversation with AI.</p>
            <p>Your conversation history will appear here.</p>
        `;
        
        this.elements.chatArea.appendChild(welcomeDiv);
    }
    
    /**
     * Scroll chat area to bottom
     */
    scrollToBottom() {
        if (this.elements.chatArea) {
            this.elements.chatArea.scrollTop = this.elements.chatArea.scrollHeight;
        }
    }
    
    /**
     * Show loading indicator
     */
    showLoading(message = 'Loading...') {
        this.updateCallStatus(message);
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        // This will be handled by specific status updates
    }
    
    /**
     * Set call button click handler
     */
    setCallButtonHandler(handler) {
        if (this.elements.callButton) {
            this.elements.callButton.addEventListener('click', handler);
        }
    }
    
    /**
     * Get conversation history
     */
    getConversationHistory() {
        return this.conversationHistory;
    }
    
    /**
     * Update UI theme (if needed for customization)
     */
    setTheme(theme = 'default') {
        document.body.className = `theme-${theme}`;
    }
    
    /**
     * Show notification (for important messages)
     */
    showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
    }
    
    /**
     * Handle responsive design updates
     */
    updateResponsiveLayout() {
        // Add responsive classes based on screen size
        const isMobile = window.innerWidth <= 600;
        document.body.classList.toggle('mobile-layout', isMobile);
    }
}

// Export for use in other modules
window.UIManager = UIManager;