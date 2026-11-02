import type { AgentRequest, AgentResponse, Message, HealthStatus } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function apiBaseUrl(): string {
  return typeof window === 'undefined' ? API_BASE_URL : localStorage.getItem('api_url') || API_BASE_URL;
}

function getCsrfToken(): string {
  if (typeof document === 'undefined') return '';
  const token = document.cookie.split('; ').find((item) => item.startsWith('hub_csrf='));
  return token ? decodeURIComponent(token.substring('hub_csrf='.length)) : '';
}

function getHeaders(method = 'GET'): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())) {
    const csrf = getCsrfToken();
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  return headers;
}

function sessionFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const method = init.method || 'GET';
  const headers = new Headers(getHeaders(method));
  new Headers(init.headers).forEach((value, key) => headers.set(key, value));
  return fetch(url, {
    ...init,
    credentials: 'include',
    headers,
  });
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }
  return response.json();
}

export const api = {
  async login(username: string, password: string): Promise<{ username: string }> {
    const response = await sessionFetch(`${apiBaseUrl()}/api/v1/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    return handleResponse<{ username: string }>(response);
  },

  async currentUser(): Promise<{ username: string }> {
    return handleResponse<{ username: string }>(await sessionFetch(`${apiBaseUrl()}/api/v1/auth/me`));
  },

  async logout(): Promise<{ status: string }> {
    return handleResponse<{ status: string }>(await sessionFetch(`${apiBaseUrl()}/api/v1/auth/logout`, { method: 'POST' }));
  },

  // Health check
  async healthCheck(): Promise<HealthStatus> {
    const response = await sessionFetch(`${apiBaseUrl()}/health`);
    return handleResponse<HealthStatus>(response);
  },

  // Chat with agent
  async chatWithAgent(request: AgentRequest): Promise<AgentResponse> {
    const response = await sessionFetch(`${apiBaseUrl()}/api/v1/agents/chat`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return handleResponse<AgentResponse>(response);
  },

  // Get message by ID
  async getMessage(messageId: string): Promise<Message> {
    const response = await sessionFetch(`${apiBaseUrl()}/api/v1/messages/${messageId}`);
    return handleResponse<Message>(response);
  },

  // List messages
  async listMessages(params?: {
    channel?: string;
    status?: string;
    limit?: number;
  }): Promise<Message[]> {
    const queryParams = new URLSearchParams();
    if (params?.channel) queryParams.append('channel', params.channel);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const response = await sessionFetch(`${apiBaseUrl()}/api/v1/messages?${queryParams.toString()}`);
    return handleResponse<Message[]>(response);
  },
};
