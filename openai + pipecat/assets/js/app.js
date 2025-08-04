/**
 * Application Entry Point
 * Initializes the OpenAI + Pipecat Voice Assistant application
 */
import { VoiceAssistant } from './voice-assistant.js';

// Global application instance
let voiceAssistant = null;

// Initialize app when page loads
window.addEventListener('load', () => {
    try {
        console.log('🎤 Initializing OpenAI + Pipecat Voice Assistant...');
        voiceAssistant = new VoiceAssistant();
        console.log('✅ Voice Assistant initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize Voice Assistant:', error);
        
        // Show error to user
        const errorMessage = document.createElement('div');
        errorMessage.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ffebee;
            color: #d32f2f;
            padding: 15px 20px;
            border-radius: 5px;
            border: 1px solid #ffcdd2;
            z-index: 1000;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 90%;
            text-align: center;
        `;
        errorMessage.textContent = 'Failed to initialize voice assistant. Please refresh the page.';
        document.body.appendChild(errorMessage);
        
        // Auto-remove error message after 10 seconds
        setTimeout(() => {
            if (errorMessage.parentNode) {
                errorMessage.parentNode.removeChild(errorMessage);
            }
        }, 10000);
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (voiceAssistant) {
        voiceAssistant.destroy();
    }
});

// Make voice assistant available globally for debugging
window.voiceAssistant = voiceAssistant;