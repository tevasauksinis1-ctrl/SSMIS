"""Tests for MCP connector."""

import pytest
import tempfile
import asyncio
from pathlib import Path

from llm_chat.services.mcp_connector import MCPConnector


class TestMCPConnector:
    """Tests for MCPConnector class."""
    
    def test_init(self):
        """Test MCPConnector initialization."""
        connector = MCPConnector(host="localhost", port=3100)
        
        assert connector.base_url == "http://localhost:3100"
        assert connector.enabled == True
    
    def test_local_storage(self):
        """Test local memory fallback storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = f"{tmpdir}/memory.json"
            connector = MCPConnector(memory_file=memory_file)
            connector.enabled = False  # Force local storage
            
            async def test():
                # Store
                result = await connector.store_memory(
                    key="test_key",
                    value="test_value",
                    namespace="test"
                )
                assert result == True
                
                # Retrieve
                value = await connector.retrieve_memory(
                    key="test_key",
                    namespace="test"
                )
                assert value == "test_value"
                
                # Delete
                await connector.delete_memory(
                    key="test_key",
                    namespace="test"
                )
                
                value = await connector.retrieve_memory(
                    key="test_key",
                    namespace="test"
                )
                assert value is None
            
            asyncio.get_event_loop().run_until_complete(test())
    
    def test_list_memories_local(self):
        """Test listing memories from local storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = f"{tmpdir}/memory.json"
            connector = MCPConnector(memory_file=memory_file)
            connector.enabled = False
            
            async def test():
                await connector.store_memory("key1", "value1", "ns")
                await connector.store_memory("key2", "value2", "ns")
                await connector.store_memory("key3", "value3", "other")
                
                items = await connector.list_memories("ns")
                
                assert len(items) == 2
            
            asyncio.get_event_loop().run_until_complete(test())
    
    def test_search_memories_local(self):
        """Test searching memories in local storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = f"{tmpdir}/memory.json"
            connector = MCPConnector(memory_file=memory_file)
            connector.enabled = False
            
            async def test():
                await connector.store_memory("python", "python programming", "code")
                await connector.store_memory("javascript", "javascript code", "code")
                
                results = await connector.search_memories("python", "code")
                
                assert len(results) == 1
            
            asyncio.get_event_loop().run_until_complete(test())
    
    def test_conversation_context(self):
        """Test storing and retrieving conversation context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = f"{tmpdir}/memory.json"
            connector = MCPConnector(memory_file=memory_file)
            connector.enabled = False
            
            async def test():
                context = {"summary": "Test conversation", "topics": ["testing"]}
                
                await connector.store_conversation_context("conv123", context)
                
                retrieved = await connector.retrieve_conversation_context("conv123")
                
                assert retrieved["summary"] == "Test conversation"
                assert "testing" in retrieved["topics"]
            
            asyncio.get_event_loop().run_until_complete(test())
    
    def test_clear_local_memory(self):
        """Test clearing local memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = f"{tmpdir}/memory.json"
            connector = MCPConnector(memory_file=memory_file)
            connector.enabled = False
            
            async def test():
                await connector.store_memory("key1", "value1", "ns")
                await connector.store_memory("key2", "value2", "ns")
                
                connector.clear_local_memory()
                
                items = await connector.list_memories("ns")
                assert len(items) == 0
            
            asyncio.get_event_loop().run_until_complete(test())
