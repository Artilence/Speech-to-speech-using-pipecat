/**
 * Application Initialization
 * Main entry point for the Voice Conversation Agent
 */
import { VoiceAgent } from './voice-agent.js';

// Initialize the voice agent when the page loads
document.addEventListener('DOMContentLoaded', () => {
    try {
        new VoiceAgent();
        console.log('Voice Conversation Agent initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Voice Conversation Agent:', error);
        
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = 'Failed to initialize the voice agent. Please refresh the page.';
        document.body.appendChild(errorDiv);
    }
});