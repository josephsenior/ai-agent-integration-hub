// Type definitions matching backend models

export type MessageChannel = 'slack' | 'discord' | 'email' | 'webhook' | 'websocket' | 'api';

export type MessageStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'delivered';

export interface AgentRequest {
  message: string;
  channel: MessageChannel;
  user_id?: string;
  channel_id?: string;
  context?: Record<string, any>;
  integration_id?: string;
  metadata?: Record<string, any>;
}

export interface AgentResponse {
  message_id: string;
  response: string;
  status: string;
  channel: MessageChannel;
  metadata?: Record<string, any>;
  timestamp?: string;
}

export interface Message {
  id: string;
  channel: MessageChannel;
  status: MessageStatus;
  content: string;
  user_id?: string;
  channel_id?: string;
  metadata?: Record<string, any>;
  integration_id?: string;
  created_at: string;
  updated_at?: string;
  processed_at?: string;
  response?: string;
  response_metadata?: Record<string, any>;
}

export interface WebSocketMessage {
  type: 'message' | 'agent_response' | 'event' | 'error' | 'ping' | 'pong';
  message?: string;
  response?: string;
  data?: any;
  error?: string;
  timestamp?: number;
}

export interface Integration {
  name: string;
  type: MessageChannel;
  status: 'available' | 'connected' | 'disconnected' | 'error';
  configured: boolean;
}

export interface HealthStatus {
  status: string;
  redis: string;
  timestamp: string;
}
