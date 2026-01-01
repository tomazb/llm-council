/**
 * API client for the LLM Council backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

// Default timeout for requests
const DEFAULT_TIMEOUT = 30000; // 30 seconds

class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Helper function to handle API responses
 */
async function handleResponse(response, endpoint) {
  if (!response.ok) {
    let errorMessage = `Request to ${endpoint} failed`;
    let errorData = null;
    
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
function fetchWithTimeout(url, options = {}, timeout = DEFAULT_TIMEOUT) {
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
  async listConversations() {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/conversations`);
      return await handleResponse(response, 'listConversations');
    } catch (error) {
      console.error('Failed to list conversations:', error);
      throw error;
    }
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });
      return await handleResponse(response, 'createConversation');
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    try {
      if (!conversationId) {
        throw new Error('Conversation ID is required');
      }
      
      const response = await fetchWithTimeout(
        `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}`
      );
      return await handleResponse(response, 'getConversation');
    } catch (error) {
      console.error('Failed to get conversation:', error);
      throw error;
    }
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
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
      return await handleResponse(response, 'sendMessage');
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @param {AbortSignal} signal - Optional abort signal for cancellation
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent, signal) {
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

      const reader = response.body.getReader();
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
                  const event = JSON.parse(data);
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
      if (error instanceof APIError || error.name === 'AbortError') {
        throw error;
      }
      
      // Wrap other errors
      throw new APIError(error.message || 'Failed to send message');
    }
  },

  /**
   * Health check endpoint
   */
  async healthCheck() {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/health`);
      return await handleResponse(response, 'healthCheck');
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
};
