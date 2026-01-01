/**
 * API client for the LLM Council backend.
 */

import {
  Conversation,
  ConversationMetadata,
  CouncilResults,
  StreamEvent,
  CreateConversationRequest,
  SendMessageRequest,
  HealthResponse,
  StreamEventHandler
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

// Default timeout for requests
const DEFAULT_TIMEOUT = 30000; // 30 seconds

export class APIError extends Error {
  public status?: number;
  public data?: any;

  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Helper function to handle API responses
 */
async function handleResponse<T>(response: Response, endpoint: string): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request to ${endpoint} failed`;
    let errorData: any = null;
    
    try {
      errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch (e) {
      errorMessage = `${errorMessage}: ${response.statusText}`;
    }
    
    throw new APIError(errorMessage, response.status, errorData);
  }
  
  return response.json();
}

/**
 * Helper function to create fetch with timeout
 */
function fetchWithTimeout(url: string, options: RequestInit = {}, timeout: number = DEFAULT_TIMEOUT): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  return fetch(url, {
    ...options,
    signal: controller.signal
  }).finally(() => {
    clearTimeout(timeoutId);
  });
}

export const api = {
  /**
   * List all conversations.
   */
  async listConversations(): Promise<ConversationMetadata[]> {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/conversations`);
      return await handleResponse<ConversationMetadata[]>(response, 'listConversations');
    } catch (error) {
      console.error('Failed to list conversations:', error);
      throw error;
    }
  },

  /**
   * Create a new conversation.
   */
  async createConversation(): Promise<Conversation> {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });
      return await handleResponse<Conversation>(response, 'createConversation');
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    try {
      if (!conversationId) {
        throw new Error('Conversation ID is required');
      }
      
      const response = await fetchWithTimeout(
        `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}`
      );
      return await handleResponse<Conversation>(response, 'getConversation');
    } catch (error) {
      console.error('Failed to get conversation:', error);
      throw error;
    }
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId: string, content: string): Promise<CouncilResults> {
    try {
      if (!conversationId || !content) {
        throw new Error('Conversation ID and content are required');
      }
      
      const response = await fetchWithTimeout(
        `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}/message`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content }),
        }
      );
      return await handleResponse<CouncilResults>(response, 'sendMessage');
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  },

  /**
   * Send a message and receive streaming updates.
   */
  async sendMessageStream(
    conversationId: string, 
    content: string, 
    onEvent: StreamEventHandler, 
    signal?: AbortSignal
  ): Promise<void> {
    try {
      if (!conversationId || !content) {
        throw new Error('Conversation ID and content are required');
      }
      
      if (!onEvent || typeof onEvent !== 'function') {
        throw new Error('Event callback function is required');
      }

      const response = await fetch(
        `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}/message/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content }),
          signal
        }
      );

      if (!response.ok) {
        let errorMessage = 'Failed to send message';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          errorMessage = `${errorMessage}: ${response.statusText}`;
        }
        throw new APIError(errorMessage, response.status);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          // Check if aborted
          if (signal && signal.aborted) {
            reader.cancel();
            throw new Error('Request was aborted');
          }

          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          
          // Keep the last incomplete line in buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (data) {
                try {
                  const event: StreamEvent = JSON.parse(data);
                  onEvent(event.type, event);
                } catch (e) {
                  console.error('Failed to parse SSE event:', e, 'Data:', data);
                  onEvent('error', { message: 'Failed to parse server response' });
                }
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Failed to send message stream:', error);
      
      // Re-throw API errors and abort errors
      if (error instanceof APIError || error instanceof Error && error.name === 'AbortError') {
        throw error;
      }
      
      // Wrap other errors
      throw new APIError(error instanceof Error ? error.message : 'Failed to send message');
    }
  },

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/health`);
      return await handleResponse<HealthResponse>(response, 'healthCheck');
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
};
