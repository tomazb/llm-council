// Type definitions for the LLM Council frontend

export interface Message {
  role: 'user' | 'assistant';
  content?: string;
  stage1?: ModelResponse[];
  stage2?: ModelRanking[];
  stage3?: ModelResponse;
  metadata?: CouncilMetadata;
  loading?: {
    stage1: boolean;
    stage2: boolean;
    stage3: boolean;
  };
}

export interface ModelResponse {
  model: string;
  response: string;
}

export interface ModelRanking {
  model: string;
  ranking: string;
  parsed_ranking: string[];
}

export interface AggregateRanking {
  model: string;
  average_rank: number;
  rankings_count: number;
}

export interface CouncilMetadata {
  label_to_model: Record<string, string>;
  aggregate_rankings: AggregateRanking[];
}

export interface Conversation {
  id: string;
  created_at: string;
  title: string;
  messages: Message[];
}

export interface ConversationMetadata {
  id: string;
  created_at: string;
  title: string;
  message_count: number;
}

export interface StreamEvent {
  type: string;
  data?: any;
  metadata?: CouncilMetadata;
}

export interface CouncilResults {
  stage1: ModelResponse[];
  stage2: ModelRanking[];
  stage3: ModelResponse;
  metadata: CouncilMetadata;
}

export interface HealthResponse {
  status: string;
  storage: string;
  service: string;
  models_count: number;
  rate_limit: string;
}

// API Request/Response types
export interface CreateConversationRequest {
  // Empty request body
}

export interface SendMessageRequest {
  content: string;
}

export interface APIError {
  message: string;
  status?: number;
  data?: any;
}

// Component Props types
export interface SidebarProps {
  conversations: ConversationMetadata[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
}

export interface ChatInterfaceProps {
  conversation: Conversation | null;
  onSendMessage: (content: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export interface Stage1Props {
  responses: ModelResponse[];
}

export interface Stage2Props {
  rankings: ModelRanking[];
  labelToModel?: Record<string, string>;
  aggregateRankings?: AggregateRanking[];
}

export interface Stage3Props {
  finalResponse: ModelResponse;
}

// App State types
export interface AppState {
  conversations: ConversationMetadata[];
  currentConversationId: string | null;
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
}

export type AppAction =
  | { type: 'SET_CONVERSATIONS'; payload: ConversationMetadata[] }
  | { type: 'SET_CURRENT_CONVERSATION_ID'; payload: string | null }
  | { type: 'SET_CURRENT_CONVERSATION'; payload: Conversation }
  | { type: 'ADD_CONVERSATION'; payload: ConversationMetadata }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'UPDATE_MESSAGE_STAGE'; payload: { messageType: string; stage: string; data: any; metadata?: any } }
  | { type: 'SET_MESSAGE_LOADING'; payload: { stage: string } }
  | { type: 'COMPLETE_MESSAGE'; payload: { stage: string; data: any } }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' };

// API Client types
export type StreamEventHandler = (eventType: string, event: StreamEvent) => void;
