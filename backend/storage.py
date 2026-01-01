"""Async JSON-based storage for conversations."""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
from .config import DATA_DIR

logger = logging.getLogger(__name__)


async def ensure_data_dir():
    """Ensure the data directory exists."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def get_conversation_path(conversation_id: str) -> str:
    """Get the file path for a conversation."""
    return os.path.join(DATA_DIR, f"{conversation_id}.json")


def validate_conversation_id(conversation_id: str) -> bool:
    """Validate conversation ID to prevent directory traversal."""
    if not conversation_id or not isinstance(conversation_id, str):
        return False
    # Basic validation: allow only alphanumeric, hyphens, and underscores
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', conversation_id))


async def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        New conversation dict
    """
    if not validate_conversation_id(conversation_id):
        raise ValueError(f"Invalid conversation ID: {conversation_id}")

    await ensure_data_dir()

    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": []
    }

    # Save to file
    path = get_conversation_path(conversation_id)
    try:
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(conversation, indent=2))
    except OSError as e:
        logger.error(f"Failed to create conversation {conversation_id}: {e}")
        raise

    return conversation


async def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    if not validate_conversation_id(conversation_id):
        return None

    path = get_conversation_path(conversation_id)

    if not os.path.exists(path):
        return None

    try:
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load conversation {conversation_id}: {e}")
        return None


async def save_conversation(conversation: Dict[str, Any]):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
    """
    if not validate_conversation_id(conversation.get('id', '')):
        raise ValueError(f"Invalid conversation ID: {conversation.get('id')}")

    await ensure_data_dir()

    path = get_conversation_path(conversation['id'])
    try:
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(conversation, indent=2))
    except OSError as e:
        logger.error(f"Failed to save conversation {conversation['id']}: {e}")
        raise


async def list_conversations() -> List[Dict[str, Any]]:
    """
    List all conversations (metadata only).

    Returns:
        List of conversation metadata dicts
    """
    await ensure_data_dir()

    conversations = []
    try:
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                path = os.path.join(DATA_DIR, filename)
                try:
                    async with aiofiles.open(path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        # Return metadata only
                        conversations.append({
                            "id": data["id"],
                            "created_at": data["created_at"],
                            "title": data.get("title", "New Conversation"),
                            "message_count": len(data["messages"])
                        })
                except (OSError, json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to read conversation file {filename}: {e}")
                    continue
    except OSError as e:
        logger.error(f"Failed to list conversations: {e}")
        return []

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


async def add_user_message(conversation_id: str, content: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
    """
    if not content or not isinstance(content, str):
        raise ValueError("Message content must be a non-empty string")

    conversation = await get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "user",
        "content": content
    })

    await save_conversation(conversation)


async def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
    """
    conversation = await get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    })

    await save_conversation(conversation)


async def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    if not title or not isinstance(title, str):
        raise ValueError("Title must be a non-empty string")

    conversation = await get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title.strip()
    await save_conversation(conversation)
