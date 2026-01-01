"""Type definitions for the LLM Council backend."""

from typing import List, Dict, Any, Optional, TypedDict, Union
from datetime import datetime


class Message(TypedDict):
    """Message structure in conversations."""
    role: str  # 'user' or 'assistant'
    content: Optional[str]  # For user messages
    stage1: Optional[List[Dict[str, Any]]]  # For assistant messages
    stage2: Optional[List[Dict[str, Any]]]  # For assistant messages
    stage3: Optional[Dict[str, Any]]  # For assistant messages
    metadata: Optional[Dict[str, Any]]  # For assistant messages
    loading: Optional[Dict[str, bool]]  # Loading state for stages


class Conversation(TypedDict):
    """Conversation structure."""
    id: str
    created_at: str
    title: str
    messages: List[Message]


class ConversationMetadata(TypedDict):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class ModelResponse(TypedDict):
    """Response from a single model."""
    model: str
    response: str


class ModelRanking(TypedDict):
    """Ranking from a single model."""
    model: str
    ranking: str
    parsed_ranking: List[str]


class AggregateRanking(TypedDict):
    """Aggregate ranking information."""
    model: str
    average_rank: float
    rankings_count: int


class CouncilMetadata(TypedDict):
    """Metadata from council process."""
    label_to_model: Dict[str, str]
    aggregate_rankings: List[AggregateRanking]


class CouncilResults(TypedDict):
    """Results from the full council process."""
    stage1: List[ModelResponse]
    stage2: List[ModelRanking]
    stage3: ModelResponse
    metadata: CouncilMetadata


class StreamEvent(TypedDict):
    """Server-sent event structure."""
    type: str
    data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]


# Union types for API responses
APIResponse = Union[Conversation, ConversationMetadata, CouncilResults, Dict[str, Any]]
StreamEventHandler = callable[[str, StreamEvent], None]
