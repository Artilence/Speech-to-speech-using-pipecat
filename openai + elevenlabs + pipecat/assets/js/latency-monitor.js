/**
 * Latency Monitor
 * Handles latency measurement display and management
 */
export class LatencyMonitor {
    constructor() {
        this.elements = {
            openaiLatency: document.getElementById('openaiLatency'),
            websocketLatency: document.getElementById('websocketLatency'),
            firstChunkLatency: document.getElementById('firstChunkLatency'),
            totalLatency: document.getElementById('totalLatency')
        };
    }

    updateLatencyDisplay(latencyData) {
        // Update latency measurements with color coding
        this.updateLatencyValue(this.elements.openaiLatency, latencyData.openai_latency, 'OpenAI API');
        this.updateLatencyValue(this.elements.websocketLatency, latencyData.websocket_connection_latency, 'WebSocket');
        this.updateLatencyValue(this.elements.firstChunkLatency, latencyData.time_to_first_chunk, 'First Chunk');
        this.updateLatencyValue(this.elements.totalLatency, latencyData.total_round_trip, 'Total', true);
        
        console.log('📊 Latency Measurements:', {
            'OpenAI API': `${latencyData.openai_latency.toFixed(2)}ms`,
            'WebSocket Connection': `${latencyData.websocket_connection_latency.toFixed(2)}ms`,
            'Time to First Chunk': `${latencyData.time_to_first_chunk.toFixed(2)}ms`,
            'Total Round-trip': `${latencyData.total_round_trip.toFixed(2)}ms`
        });
    }

    updateLatencyValue(element, value, label, isTotal = false) {
        if (!element) return;
        
        const formattedValue = `${value.toFixed(1)}ms`;
        element.textContent = formattedValue;
        
        // Remove existing classes
        element.classList.remove('fast', 'medium', 'slow');
        
        // Add appropriate class based on latency thresholds
        if (isTotal) {
            // Total latency thresholds
            if (value < 500) {
                element.classList.add('fast');
            } else if (value < 1000) {
                element.classList.add('medium');
            } else {
                element.classList.add('slow');
            }
        } else {
            // Individual component thresholds
            if (label === 'OpenAI API') {
                if (value < 300) element.classList.add('fast');
                else if (value < 800) element.classList.add('medium');
                else element.classList.add('slow');
            } else if (label === 'WebSocket') {
                if (value < 100) element.classList.add('fast');
                else if (value < 200) element.classList.add('medium');
                else element.classList.add('slow');
            } else if (label === 'First Chunk') {
                if (value < 200) element.classList.add('fast');
                else if (value < 500) element.classList.add('medium');
                else element.classList.add('slow');
            }
        }
    }

    resetLatencyDisplay() {
        // Reset all latency displays
        const elements = [
            this.elements.openaiLatency, 
            this.elements.websocketLatency, 
            this.elements.firstChunkLatency, 
            this.elements.totalLatency
        ];
        
        elements.forEach(el => {
            if (el) {
                el.textContent = '-';
                el.classList.remove('fast', 'medium', 'slow');
            }
        });
    }
}