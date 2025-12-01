"""Tests for history manager."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from llm_chat.core.history_manager import HistoryManager
from llm_chat.core.chat_client import Message, Conversation


class TestHistoryManager:
    """Tests for HistoryManager class."""
    
    def test_create_conversation(self):
        """Test creating a new conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv = hm.create_conversation("Test Chat")
            
            assert conv.title == "Test Chat"
            assert conv.id is not None
            assert len(conv.messages) == 0
    
    def test_get_conversation(self):
        """Test retrieving a conversation by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv = hm.create_conversation("Test")
            retrieved = hm.get_conversation(conv.id)
            
            assert retrieved is not None
            assert retrieved.id == conv.id
            assert retrieved.title == "Test"
    
    def test_get_nonexistent_conversation(self):
        """Test retrieving a non-existent conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            result = hm.get_conversation("nonexistent-id")
            
            assert result is None
    
    def test_list_conversations(self):
        """Test listing all conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            hm.create_conversation("First")
            hm.create_conversation("Second")
            hm.create_conversation("Third")
            
            convs = hm.list_conversations()
            
            assert len(convs) == 3
    
    def test_list_conversations_limit(self):
        """Test listing conversations with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            for i in range(10):
                hm.create_conversation(f"Conv {i}")
            
            convs = hm.list_conversations(limit=5)
            
            assert len(convs) == 5
    
    def test_add_message(self):
        """Test adding a message to a conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv = hm.create_conversation("Test")
            msg = Message(role="user", content="Hello!")
            
            hm.add_message(conv.id, msg)
            
            retrieved = hm.get_conversation(conv.id)
            assert len(retrieved.messages) == 1
            assert retrieved.messages[0].content == "Hello!"
    
    def test_update_title(self):
        """Test updating conversation title."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv = hm.create_conversation("Original")
            hm.update_title(conv.id, "Updated Title")
            
            retrieved = hm.get_conversation(conv.id)
            assert retrieved.title == "Updated Title"
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv = hm.create_conversation("To Delete")
            conv_id = conv.id
            
            hm.delete_conversation(conv_id)
            
            assert hm.get_conversation(conv_id) is None
    
    def test_clear_all(self):
        """Test clearing all conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            hm.create_conversation("One")
            hm.create_conversation("Two")
            
            hm.clear_all()
            
            assert len(hm.list_conversations()) == 0
    
    def test_search(self):
        """Test searching conversations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv1 = hm.create_conversation("Python Help")
            conv2 = hm.create_conversation("JavaScript Tutorial")
            
            results = hm.search("python")
            
            assert len(results) == 1
            assert results[0].title == "Python Help"
    
    def test_export_json(self):
        """Test exporting conversation as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hm = HistoryManager(f"{tmpdir}/history.json")
            
            conv = hm.create_conversation("Export Test")
            msg = Message(role="user", content="Test message")
            hm.add_message(conv.id, msg)
            
            export = hm.export_conversation(conv.id, format="json")
            
            import json
            data = json.loads(export)
            assert data["title"] == "Export Test"
            assert len(data["messages"]) == 1
    
    def test_persistence(self):
        """Test that history persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = f"{tmpdir}/history.json"
            
            # Create and save
            hm1 = HistoryManager(history_file)
            conv = hm1.create_conversation("Persistent")
            msg = Message(role="user", content="Persisted message")
            hm1.add_message(conv.id, msg)
            
            # Load in new instance
            hm2 = HistoryManager(history_file)
            convs = hm2.list_conversations()
            
            assert len(convs) == 1
            assert convs[0].title == "Persistent"
            assert len(convs[0].messages) == 1
