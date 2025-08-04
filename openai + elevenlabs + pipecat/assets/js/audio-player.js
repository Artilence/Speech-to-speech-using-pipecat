/**
 * Audio Player Manager
 * Handles audio playback and streaming functionality
 */
export class AudioPlayer {
    constructor() {
        this.audioEl = document.getElementById('responseAudio');
        this.isMuted = false;
        
        // Streaming audio properties for ultra-low latency
        this.audioChunks = [];
        this.audioQueue = [];
        this.isStreaming = false;
        this.currentChunkIndex = 0;
    }

    playAudioResponse(audioBase64) {
        if (!this.isMuted) {
            const audioBlob = this.base64ToBlob(audioBase64, 'audio/mpeg');
            const audioUrl = URL.createObjectURL(audioBlob);
            this.audioEl.src = audioUrl;
            this.audioEl.play().catch(console.error);
            
            this.audioEl.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
        }
    }

    initializeStreamingAudio() {
        // Initialize streaming audio for ultra-low latency playback
        if (!this.isMuted) {
            this.audioChunks = [];
            this.audioQueue = [];
            this.isStreaming = true;
            this.currentChunkIndex = 0;
        }
    }

    playAudioChunk(audioBase64) {
        // Play individual audio chunks as they arrive for real-time streaming
        if (!this.isMuted && this.isStreaming) {
            const audioBlob = this.base64ToBlob(audioBase64, 'audio/mpeg');
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create a new audio element for this chunk
            const chunkAudio = new Audio(audioUrl);
            chunkAudio.preload = 'auto';
            
            // Add to queue for sequential playback
            this.audioQueue.push({
                audio: chunkAudio,
                url: audioUrl,
                index: this.currentChunkIndex++
            });
            
            // Start playing if this is the first chunk
            if (this.audioQueue.length === 1) {
                this.playNextChunk();
            }
        }
    }

    playNextChunk() {
        if (this.audioQueue.length > 0 && !this.isMuted) {
            const chunk = this.audioQueue.shift();
            
            chunk.audio.onended = () => {
                URL.revokeObjectURL(chunk.url);
                // Play next chunk when current one ends
                if (this.audioQueue.length > 0 || this.isStreaming) {
                    setTimeout(() => this.playNextChunk(), 10); // Small delay to prevent gaps
                }
            };
            
            chunk.audio.onerror = (error) => {
                console.error('Audio chunk playback error:', error);
                URL.revokeObjectURL(chunk.url);
                // Try next chunk on error
                if (this.audioQueue.length > 0 || this.isStreaming) {
                    this.playNextChunk();
                }
            };
            
            chunk.audio.play().catch(console.error);
        }
    }

    finalizeStreamingAudio() {
        // Finalize streaming audio playback
        this.isStreaming = false;
        
        // Clean up any remaining chunks after a delay
        setTimeout(() => {
            if (this.audioQueue.length === 0) {
                this.audioChunks = [];
                this.currentChunkIndex = 0;
            }
        }, 1000);
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        return this.isMuted;
    }

    isMutedState() {
        return this.isMuted;
    }

    base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], { type: mimeType });
    }
}