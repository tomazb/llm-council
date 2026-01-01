"""Test storage functionality."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from backend import storage
from backend.config import settings


@pytest.fixture
async def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override settings data dir
        original_data_dir = settings.data_dir
        settings.data_dir = temp_dir
        
        yield temp_dir
        
        # Restore original data dir
        settings.data_dir = original_data_dir


@pytest.mark.asyncio
async def test_create_conversation(temp_data_dir):
    """Test creating a new conversation."""
    conversation_id = "test-conv-123"
    
    conv = await storage.create_conversation(conversation_id)
    
    assert conv["id"] == conversation_id
    assert conv["title"] == "New Conversation"
    assert conv["messages"] == []
    assert "created_at" in conv
    
    # Check file was created
    file_path = os.path.join(temp_data_dir, f"{conversation_id}.json")
    assert os.path.exists(file_path)


@pytest.mark.asyncio
async def test_get_conversation(temp_data_dir):
    """Test retrieving a conversation."""
    conversation_id = "test-conv-456"
    
    # Create conversation first
    created = await storage.create_conversation(conversation_id)
    
    # Retrieve it
    retrieved = await storage.get_conversation(conversation_id)
    
    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["title"] == created["title"]


@pytest.mark.asyncio
async def test_get_nonexistent_conversation(temp_data_dir):
    """Test retrieving a non-existent conversation."""
    result = await storage.get_conversation("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_add_user_message(temp_data_dir):
    """Test adding a user message to a conversation."""
    conversation_id = "test-conv-msg"
    
    # Create conversation
    await storage.create_conversation(conversation_id)
    
    # Add user message
    await storage.add_user_message(conversation_id, "Hello, world!")
    
    # Retrieve and check
    conv = await storage.get_conversation(conversation_id)
    assert len(conv["messages"]) == 1
    assert conv["messages"][0]["role"] == "user"
    assert conv["messages"][0]["content"] == "Hello, world!"


@pytest.mark.asyncio
async def test_invalid_conversation_id():
    """Test validation of conversation IDs."""
    with pytest.raises(ValueError, match="Invalid conversation ID"):
        await storage.create_conversation("../../../etc/passwd")
    
    with pytest.raises(ValueError, match="Invalid conversation ID"):
        await storage.create_conversation("")
    
    with pytest.raises(ValueError, match="Invalid conversation ID"):
        await storage.create_conversation(None)


@pytest.mark.asyncio
async def test_list_conversations(temp_data_dir):
    """Test listing conversations."""
    # Create multiple conversations
    conv1 = await storage.create_conversation("conv1")
    conv2 = await storage.create_conversation("conv2")
    
    # List conversations
    conversations = await storage.list_conversations()
    
    assert len(conversations) == 2
    
    # Should be sorted by creation time (newest first)
    assert conversations[0]["id"] == "conv2"  # Created second
    assert conversations[1]["id"] == "conv1"  # Created first
    
    # Check metadata structure
    for conv in conversations:
        assert "id" in conv
        assert "created_at" in conv
        assert "title" in conv
        assert "message_count" in conv
        assert "messages" not in conv  # Should not include full messages
