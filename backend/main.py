"""FastAPI backend for LLM Council."""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
import json
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from . import storage
from .council import run_full_council, generate_conversation_title
from .config import settings
from .types import Conversation, ConversationMetadata, CouncilResults, StreamEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="LLM Council API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for local development (configurable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    storage: str
    service: str
    models_count: int
    rate_limit: str


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Detailed health check endpoint."""
    try:
        # Test storage
        await storage.ensure_data_dir()
        return HealthResponse(
            status="healthy",
            storage="ok",
            service="LLM Council API",
            models_count=len(settings.council_models),
            rate_limit=f"{settings.rate_limit_requests}/{settings.rate_limit_window}s"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/conversations", response_model=List[ConversationMetadata])
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def list_conversations(request: Request) -> List[ConversationMetadata]:
    """List all conversations (metadata only)."""
    try:
        return await storage.list_conversations()
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@app.post("/api/conversations", response_model=Conversation)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def create_conversation(
    request: Request, 
    create_request: CreateConversationRequest
) -> Conversation:
    """Create a new conversation."""
    try:
        conversation_id = str(uuid.uuid4())
        conversation = await storage.create_conversation(conversation_id)
        logger.info(f"Created conversation {conversation_id}")
        return conversation
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def get_conversation(request: Request, conversation_id: str) -> Conversation:
    """Get a specific conversation with all its messages."""
    try:
        conversation = await storage.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@app.post("/api/conversations/{conversation_id}/message", response_model=CouncilResults)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def send_message(
    request: Request, 
    conversation_id: str, 
    message_request: SendMessageRequest
) -> CouncilResults:
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    try:
        # Check if conversation exists
        conversation = await storage.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if this is the first message
        is_first_message = len(conversation["messages"]) == 0

        # Add user message
        await storage.add_user_message(conversation_id, message_request.content)

        # If this is the first message, generate a title
        if is_first_message:
            title = await generate_conversation_title(message_request.content)
            await storage.update_conversation_title(conversation_id, title)

        # Run the 3-stage council process
        stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
            message_request.content
        )

        # Add assistant message with all stages
        await storage.add_assistant_message(
            conversation_id,
            stage1_results,
            stage2_results,
            stage3_result
        )

        logger.info(f"Processed message for conversation {conversation_id}")
        
        # Return the complete response with metadata
        return CouncilResults(
            stage1=stage1_results,
            stage2=stage2_results,
            stage3=stage3_result,
            metadata=metadata
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send message to {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@app.post("/api/conversations/{conversation_id}/message/stream")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def send_message_stream(
    request: Request, 
    conversation_id: str, 
    message_request: SendMessageRequest
) -> StreamingResponse:
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    try:
        # Check if conversation exists
        conversation = await storage.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if this is the first message
        is_first_message = len(conversation["messages"]) == 0

        async def event_generator():
            try:
                # Add user message
                await storage.add_user_message(conversation_id, message_request.content)

                # Start title generation in parallel (don't await yet)
                title_task = None
                if is_first_message:
                    title_task = asyncio.create_task(
                        generate_conversation_title(message_request.content)
                    )

                # Stage 1: Collect responses
                yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
                from .council import stage1_collect_responses
                stage1_results = await stage1_collect_responses(message_request.content)
                yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

                # Stage 2: Collect rankings
                yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
                from .council import stage2_collect_rankings, calculate_aggregate_rankings
                stage2_results, label_to_model = await stage2_collect_rankings(
                    message_request.content, stage1_results
                )
                aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
                yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

                # Stage 3: Synthesize final answer
                yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
                from .council import stage3_synthesize_final
                stage3_result = await stage3_synthesize_final(
                    message_request.content, stage1_results, stage2_results
                )
                yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

                # Wait for title generation if it was started
                if title_task:
                    title = await title_task
                    await storage.update_conversation_title(conversation_id, title)
                    yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

                # Save complete assistant message
                await storage.add_assistant_message(
                    conversation_id,
                    stage1_results,
                    stage2_results,
                    stage3_result
                )

                logger.info(f"Completed streaming for conversation {conversation_id}")

                # Send completion event
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"

            except Exception as e:
                logger.error(f"Error in stream for conversation {conversation_id}: {e}")
                # Send error event
                yield f"data: {json.dumps({'type': 'error', 'message': 'Internal server error'})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start stream for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start stream")


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting LLM Council API on {settings.api_host}:{settings.api_port}")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, debug=settings.debug)
