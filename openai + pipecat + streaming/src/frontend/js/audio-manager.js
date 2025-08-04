/**
 * Audio Manager for handling audio playback
 */

class AudioManager {
    constructor() {
        this.currentAudio = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.volume = 1.0;
    }
    
    /**
     * Play audio from base64 encoded data
     * @param {string} audioB64 - Base64 encoded audio data
     * @param {string} mimeType - MIME type of audio (default: audio/mp3)
     * @returns {Promise<boolean>} - Success status
     */
    async playAudio(audioB64, mimeType = 'audio/mp3') {
        try {
            if (!audioB64) {
                console.warn('⚠️  No audio data provided');
                return false;
            }
            
            // Convert base64 to blob
            const audioBlob = this.base64ToBlob(audioB64, mimeType);
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Stop current audio if playing
            this.stopCurrentAudio();
            
            // Create and play new audio
            this.currentAudio = new Audio(audioUrl);
            this.currentAudio.volume = this.volume;
            this.isPlaying = true;
            
            // Set up event handlers
            this.currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                this.isPlaying = false;
                console.log('🔊 Audio playback completed');
                
                // Play next in queue if available
                this.playNextInQueue();
            };
            
            this.currentAudio.onerror = (error) => {
                console.error('❌ Audio playback error:', error);
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                this.isPlaying = false;
            };
            
            this.currentAudio.onloadstart = () => {
                console.log('🔊 Audio loading started');
            };
            
            this.currentAudio.oncanplay = () => {
                console.log('🔊 Audio ready to play');
            };
            
            // Start playback
            await this.currentAudio.play();
            console.log('🔊 Audio playback started');
            
            return true;
            
        } catch (error) {
            console.error('❌ Audio playback error:', error);
            this.isPlaying = false;
            return false;
        }
    }
    
    /**
     * Queue audio for sequential playback
     * @param {string} audioB64 - Base64 encoded audio data
     * @param {string} mimeType - MIME type of audio
     */
    queueAudio(audioB64, mimeType = 'audio/mp3') {
        this.audioQueue.push({ audioB64, mimeType });
        
        // If not currently playing, start playing the queue
        if (!this.isPlaying) {
            this.playNextInQueue();
        }
    }
    
    /**
     * Play next audio in queue
     */
    async playNextInQueue() {
        if (this.audioQueue.length === 0 || this.isPlaying) {
            return;
        }
        
        const nextAudio = this.audioQueue.shift();
        await this.playAudio(nextAudio.audioB64, nextAudio.mimeType);
    }
    
    /**
     * Stop current audio playback
     */
    stopCurrentAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
        this.isPlaying = false;
    }
    
    /**
     * Clear audio queue
     */
    clearQueue() {
        this.audioQueue = [];
    }
    
    /**
     * Stop all audio and clear queue
     */
    stopAll() {
        this.stopCurrentAudio();
        this.clearQueue();
    }
    
    /**
     * Set audio volume
     * @param {number} volume - Volume level (0.0 to 1.0)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.currentAudio) {
            this.currentAudio.volume = this.volume;
        }
    }
    
    /**
     * Get current volume
     * @returns {number} - Current volume level
     */
    getVolume() {
        return this.volume;
    }
    
    /**
     * Check if audio is currently playing
     * @returns {boolean} - Playing status
     */
    isAudioPlaying() {
        return this.isPlaying;
    }
    
    /**
     * Get queue length
     * @returns {number} - Number of items in queue
     */
    getQueueLength() {
        return this.audioQueue.length;
    }
    
    /**
     * Convert base64 string to Blob
     * @param {string} base64 - Base64 encoded data
     * @param {string} mimeType - MIME type of the data
     * @returns {Blob} - Blob object
     */
    base64ToBlob(base64, mimeType) {
        try {
            const byteCharacters = atob(base64);
            const byteNumbers = new Array(byteCharacters.length);
            
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            return new Blob([byteArray], { type: mimeType });
            
        } catch (error) {
            console.error('❌ Error converting base64 to blob:', error);
            throw error;
        }
    }
    
    /**
     * Test audio playback with a short beep
     * @returns {Promise<boolean>} - Success status
     */
    async testAudio() {
        try {
            // Create a short beep sound using Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800; // 800 Hz
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
            
            console.log('🔊 Audio test completed');
            return true;
            
        } catch (error) {
            console.error('❌ Audio test failed:', error);
            return false;
        }
    }
}

// Export for use in other modules
window.AudioManager = AudioManager;