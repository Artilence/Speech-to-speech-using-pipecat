/**
 * WebSocket Client Module
 * Handles WebSocket connection and message communication
 */
export class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.messageHandlers = new Map();
        this.connectionStateCallbacks = [];
        this.reconnectTimeout = null;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/chat`;
        
        console.log(`Connecting to WebSocket: ${url}`);
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.notifyConnectionState('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.notifyConnectionState('error');
        };

        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
            this.notifyConnectionState('disconnected');
            this.attemptReconnect();
        };
    }

    handleMessage(data) {
        const handler = this.messageHandlers.get(data.type);
        if (handler) {
            handler(data);
        } else {
            console.warn('Unhandled message type:', data.type);
        }
    }

    onMessage(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    onConnectionStateChange(callback) {
        this.connectionStateCallbacks.push(callback);
    }

    notifyConnectionState(state) {
        this.connectionStateCallbacks.forEach(callback => callback(state));
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        }
        console.warn('WebSocket not connected, cannot send message:', message);
        return false;
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = 2000 * this.reconnectAttempts;
            
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.notifyConnectionState('reconnecting');
            
            this.reconnectTimeout = setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.notifyConnectionState('failed');
        }
    }

    disconnect() {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    // Message sending helpers
    sendStartRecording() {
        return this.sendMessage({ type: "start_recording" });
    }

    sendStopRecording(transcriptText) {
        return this.sendMessage({ 
            type: "stop_recording", 
            content: transcriptText 
        });
    }

    sendVoiceChunk(chunkText) {
        return this.sendMessage({ 
            type: "voice_chunk", 
            content: chunkText 
        });
    }

    sendTextMessage(text) {
        return this.sendMessage({ 
            type: "text", 
            content: text 
        });
    }

    sendPing() {
        return this.sendMessage({ type: "ping" });
    }
}