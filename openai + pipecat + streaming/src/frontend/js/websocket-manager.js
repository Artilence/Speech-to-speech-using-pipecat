/**
 * WebSocket Manager for handling real-time communication
 */

class WebSocketManager {
    constructor(eventCallbacks = {}) {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        
        // Event callbacks
        this.callbacks = {
            onOpen: eventCallbacks.onOpen || (() => {}),
            onMessage: eventCallbacks.onMessage || (() => {}),
            onClose: eventCallbacks.onClose || (() => {}),
            onError: eventCallbacks.onError || (() => {})
        };
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/stream-chat`;
        
        console.log('🔗 Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            console.log('✅ WebSocket connected successfully');
            this.callbacks.onOpen();
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('📨 Received message:', message.type, message);
                this.callbacks.onMessage(message);
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error, event.data);
            }
        };
        
        this.ws.onclose = (event) => {
            this.isConnected = false;
            console.log('📞 WebSocket closed:', event.code, event.reason);
            this.callbacks.onClose(event);
            
            // Auto-reconnect if it wasn't a clean close and we haven't exceeded max attempts
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                setTimeout(() => {
                    this.connect();
                }, this.reconnectDelay);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.callbacks.onError(error);
        };
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
        this.isConnected = false;
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                console.log('📤 Sending WebSocket message:', message.type, message);
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('❌ Error sending WebSocket message:', error);
                return false;
            }
        } else {
            console.error('❌ WebSocket not connected. Ready state:', this.ws?.readyState);
            return false;
        }
    }
    
    sendUserSpeech(text) {
        return this.sendMessage({
            type: 'user_speech',
            content: text.trim()
        });
    }
    
    ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // Send a ping frame (if supported) or a custom ping message
            try {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            } catch (error) {
                console.error('❌ Ping failed:', error);
            }
        }
    }
}

// Export for use in other modules
window.WebSocketManager = WebSocketManager;