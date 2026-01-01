import { useState, useEffect, useReducer, useCallback, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { api } from './api';
import './App.css';
import {
  Conversation,
  ConversationMetadata,
  AppState,
  AppAction,
  StreamEvent
} from './types';

// Action types for state management
const actionTypes = {
  SET_CONVERSATIONS: 'SET_CONVERSATIONS',
  SET_CURRENT_CONVERSATION_ID: 'SET_CURRENT_CONVERSATION_ID',
  SET_CURRENT_CONVERSATION: 'SET_CURRENT_CONVERSATION',
  ADD_CONVERSATION: 'ADD_CONVERSATION',
  SET_LOADING: 'SET_LOADING',
  UPDATE_MESSAGE_STAGE: 'UPDATE_MESSAGE_STAGE',
  SET_MESSAGE_LOADING: 'SET_MESSAGE_LOADING',
  COMPLETE_MESSAGE: 'COMPLETE_MESSAGE',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR'
} as const;

// Initial state
const initialState: AppState = {
  conversations: [],
  currentConversationId: null,
  currentConversation: null,
  isLoading: false,
  error: null
};

// Reducer function for state management
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case actionTypes.SET_CONVERSATIONS:
      return { ...state, conversations: action.payload };
    
    case actionTypes.SET_CURRENT_CONVERSATION_ID:
      return { ...state, currentConversationId: action.payload };
    
    case actionTypes.SET_CURRENT_CONVERSATION:
      return { ...state, currentConversation: action.payload };
    
    case actionTypes.ADD_CONVERSATION:
      return {
        ...state,
        conversations: [action.payload, ...state.conversations]
      };
    
    case actionTypes.SET_LOADING:
      return { ...state, isLoading: action.payload };
    
    case actionTypes.UPDATE_MESSAGE_STAGE:
      const { messageType, stage, data, metadata } = action.payload;
      if (!state.currentConversation) return state;
      
      const updatedMessages = state.currentConversation.messages.map((msg, index) => {
        if (index === state.currentConversation!.messages.length - 1) {
          return {
            ...msg,
            [stage]: data,
            ...(metadata && { metadata }),
            loading: {
              ...msg.loading,
              [stage]: false
            }
          };
        }
        return msg;
      });
      return {
        ...state,
        currentConversation: {
          ...state.currentConversation,
          messages: updatedMessages
        }
      };
    
    case actionTypes.SET_MESSAGE_LOADING:
      const { stage: loadingStage } = action.payload;
      if (!state.currentConversation) return state;
      
      const messagesWithLoading = state.currentConversation.messages.map((msg, index) => {
        if (index === state.currentConversation!.messages.length - 1) {
          return {
            ...msg,
            loading: {
              ...msg.loading,
              [loadingStage]: true
            }
          };
        }
        return msg;
      });
      return {
        ...state,
        currentConversation: {
          ...state.currentConversation,
          messages: messagesWithLoading
        }
      };
    
    case actionTypes.COMPLETE_MESSAGE:
      const { stage: completeStage, data: completeData } = action.payload;
      if (!state.currentConversation) return state;
      
      const completedMessages = state.currentConversation.messages.map((msg, index) => {
        if (index === state.currentConversation!.messages.length - 1) {
          return {
            ...msg,
            [completeStage]: completeData,
            loading: {
              ...msg.loading,
              [completeStage]: false
            }
          };
        }
        return msg;
      });
      return {
        ...state,
        currentConversation: {
          ...state.currentConversation,
          messages: completedMessages
        }
      };
    
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload };
    
    case actionTypes.CLEAR_ERROR:
      return { ...state, error: null };
    
    default:
      return state;
  }
}

function App() {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (state.currentConversationId) {
      loadConversation(state.currentConversationId);
    }
  }, [state.currentConversationId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const loadConversations = useCallback(async () => {
    try {
      const convs = await api.listConversations();
      dispatch({ type: actionTypes.SET_CONVERSATIONS, payload: convs });
    } catch (error) {
      console.error('Failed to load conversations:', error);
      const message = error instanceof Error ? error.message : 'Failed to load conversations';
      dispatch({ type: actionTypes.SET_ERROR, payload: message });
    }
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await api.getConversation(id);
      dispatch({ type: actionTypes.SET_CURRENT_CONVERSATION, payload: conv });
      dispatch({ type: actionTypes.CLEAR_ERROR });
    } catch (error) {
      console.error('Failed to load conversation:', error);
      const message = error instanceof Error ? error.message : 'Failed to load conversation';
      dispatch({ type: actionTypes.SET_ERROR, payload: message });
    }
  }, []);

  const handleNewConversation = useCallback(async () => {
    try {
      dispatch({ type: actionTypes.CLEAR_ERROR });
      const newConv = await api.createConversation();
      dispatch({
        type: actionTypes.ADD_CONVERSATION,
        payload: { 
          id: newConv.id, 
          created_at: newConv.created_at, 
          message_count: 0 
        }
      });
      dispatch({ type: actionTypes.SET_CURRENT_CONVERSATION_ID, payload: newConv.id });
    } catch (error) {
      console.error('Failed to create conversation:', error);
      const message = error instanceof Error ? error.message : 'Failed to create conversation';
      dispatch({ type: actionTypes.SET_ERROR, payload: message });
    }
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    dispatch({ type: actionTypes.SET_CURRENT_CONVERSATION_ID, payload: id });
  }, []);

  const handleSendMessage = useCallback(async (content: string) => {
    if (!state.currentConversationId || state.isLoading) return;

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    dispatch({ type: actionTypes.SET_LOADING, payload: true });
    dispatch({ type: actionTypes.CLEAR_ERROR });

    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user' as const, content };
      const updatedConversation = {
        ...state.currentConversation!,
        messages: [...state.currentConversation!.messages, userMessage]
      };
      dispatch({ type: actionTypes.SET_CURRENT_CONVERSATION, payload: updatedConversation });

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant' as const,
        stage1: undefined,
        stage2: undefined,
        stage3: undefined,
        metadata: undefined,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      const conversationWithAssistant = {
        ...updatedConversation,
        messages: [...updatedConversation.messages, assistantMessage]
      };
      dispatch({ type: actionTypes.SET_CURRENT_CONVERSATION, payload: conversationWithAssistant });

      // Send message with streaming
      await api.sendMessageStream(
        state.currentConversationId, 
        content, 
        (eventType: string, event: StreamEvent) => {
          switch (eventType) {
            case 'stage1_start':
              dispatch({ type: actionTypes.SET_MESSAGE_LOADING, payload: { stage: 'stage1' } });
              break;

            case 'stage1_complete':
              dispatch({ 
                type: actionTypes.UPDATE_MESSAGE_STAGE, 
                payload: { messageType: 'assistant', stage: 'stage1', data: event.data } 
              });
              break;

            case 'stage2_start':
              dispatch({ type: actionTypes.SET_MESSAGE_LOADING, payload: { stage: 'stage2' } });
              break;

            case 'stage2_complete':
              dispatch({ 
                type: actionTypes.UPDATE_MESSAGE_STAGE, 
                payload: { 
                  messageType: 'assistant', 
                  stage: 'stage2', 
                  data: event.data, 
                  metadata: event.metadata 
                } 
              });
              break;

            case 'stage3_start':
              dispatch({ type: actionTypes.SET_MESSAGE_LOADING, payload: { stage: 'stage3' } });
              break;

            case 'stage3_complete':
              dispatch({ 
                type: actionTypes.UPDATE_MESSAGE_STAGE, 
                payload: { messageType: 'assistant', stage: 'stage3', data: event.data } 
              });
              break;

            case 'title_complete':
              // Reload conversations to get updated title
              loadConversations();
              break;

            case 'complete':
              // Stream complete, reload conversations list
              loadConversations();
              dispatch({ type: actionTypes.SET_LOADING, payload: false });
              break;

            case 'error':
              console.error('Stream error:', event.message);
              dispatch({ type: actionTypes.SET_ERROR, payload: event.message || 'Unknown error' });
              dispatch({ type: actionTypes.SET_LOADING, payload: false });
              break;

            default:
              console.log('Unknown event type:', eventType);
          }
        },
        abortControllerRef.current.signal
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Don't show error for aborted requests
      if (!(error instanceof Error && error.name === 'AbortError')) {
        // Remove optimistic messages on error
        const revertedConversation = {
          ...state.currentConversation!,
          messages: state.currentConversation!.messages.slice(0, -2)
        };
        dispatch({ type: actionTypes.SET_CURRENT_CONVERSATION, payload: revertedConversation });
        const message = error instanceof Error ? error.message : 'Failed to send message';
        dispatch({ type: actionTypes.SET_ERROR, payload: message });
      }
      
      dispatch({ type: actionTypes.SET_LOADING, payload: false });
    } finally {
      abortControllerRef.current = null;
    }
  }, [state.currentConversationId, state.currentConversation, state.isLoading, loadConversations]);

  return (
    <div className="app">
      <Sidebar
        conversations={state.conversations}
        currentConversationId={state.currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
      <ChatInterface
        conversation={state.currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={state.isLoading}
        error={state.error}
      />
    </div>
  );
}

export default App;
