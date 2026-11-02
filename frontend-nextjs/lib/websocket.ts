import ReconnectingWebSocket from 'reconnecting-websocket';
import type { WebSocketMessage } from '@/types';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export class WebSocketClient {
  private ws: ReconnectingWebSocket | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect(): void {
    if (this.ws) {
      return;
    }

    this.ws = new ReconnectingWebSocket(`${WS_BASE_URL}/ws`, [], {
      connectionTimeout: 4000,
      maxRetries: 10,
      maxReconnectionDelay: 10000,
      minReconnectionDelay: 1000,
    });

    this.ws.addEventListener('message', (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    });

    this.ws.addEventListener('open', () => {
      console.log('WebSocket connected');
      this.emit('connected', {});
    });

    this.ws.addEventListener('close', () => {
      console.log('WebSocket disconnected');
      this.emit('disconnected', {});
    });

    this.ws.addEventListener('error', (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', { error });
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }

  send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === 1) { // WebSocket.OPEN = 1
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  on(event: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Emit based on message type
    this.emit(message.type, message);

    // Also emit generic 'message' event
    if (message.type !== 'message') {
      this.emit('message', message);
    }
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in WebSocket listener for ${event}:`, error);
      }
    });
  }

  isConnected(): boolean {
    return this.ws?.readyState === 1; // WebSocket.OPEN = 1
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();
