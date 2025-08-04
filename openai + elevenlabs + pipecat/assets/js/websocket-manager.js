/**
 * WebSocket Manager
 * Handles WebSocket connection and message communication
 */
export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.clientId = Math.random().toString(36).substr(2, 9);
        this.messageHandlers = new Map();
        this.connectionStateCallbacks = [];
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.notifyConnectionState('connected');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            this.notifyConnectionState('disconnected');
            setTimeout(() => this.connect(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.notifyConnectionState('error');
        };
    }

    handleMessage(message) {
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
            handler(message);
        } else {
            console.warn('Unhandled message type:', message.type);
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
        return false;
    }

    sendUserSpeech(text) {
        return this.sendMessage({
            type: 'user_speech',
            text: text
        });
    }

    sendPing() {
        return this.sendMessage({
            type: 'ping'
        });
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    getClientId() {
        return this.clientId;
    }
}