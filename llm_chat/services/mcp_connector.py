"""MCP (Model Context Protocol) memory server connector."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

import aiohttp

from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class MCPConnector:
    """Connector for MCP memory server for persistent context."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3100,
        memory_file: Optional[str] = None,
    ):
        """Initialize the MCP connector.
        
        Args:
            host: MCP server host.
            port: MCP server port.
            memory_file: Local memory file for fallback storage.
        """
        self.base_url = f"http://{host}:{port}"
        self._session: Optional[aiohttp.ClientSession] = None
        self._enabled = True
        
        # Fallback local storage
        if memory_file:
            self.memory_file = Path(memory_file).expanduser()
        else:
            self.memory_file = Path.home() / ".llm_chat" / "memory.json"
        
        self._local_memory: Dict[str, Any] = {}
        self._load_local_memory()
    
    def _load_local_memory(self) -> None:
        """Load local memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._local_memory = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load local memory: {e}")
                self._local_memory = {}
    
    def _save_local_memory(self) -> None:
        """Save local memory to file."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self._local_memory, f, indent=2)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    @property
    def enabled(self) -> bool:
        """Check if MCP is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set MCP enabled state."""
        self._enabled = value
    
    async def health_check(self) -> bool:
        """Check if MCP server is available.
        
        Returns:
            True if server is reachable, False otherwise.
        """
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"MCP health check failed: {e}")
            return False
    
    async def store_memory(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store a memory item.
        
        Args:
            key: Memory key.
            value: Value to store.
            namespace: Memory namespace.
            metadata: Optional metadata.
            
        Returns:
            True if stored successfully.
        """
        memory_item = {
            "key": key,
            "value": value,
            "namespace": namespace,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        if self._enabled:
            try:
                session = await self._get_session()
                async with session.post(
                    f"{self.base_url}/memory",
                    json=memory_item,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
            except Exception as e:
                logger.warning(f"Failed to store memory in MCP server: {e}")
        
        # Fallback to local storage
        ns_key = f"{namespace}:{key}"
        self._local_memory[ns_key] = memory_item
        self._save_local_memory()
        return True
    
    async def retrieve_memory(
        self,
        key: str,
        namespace: str = "default",
    ) -> Optional[Any]:
        """Retrieve a memory item.
        
        Args:
            key: Memory key.
            namespace: Memory namespace.
            
        Returns:
            Stored value or None if not found.
        """
        if self._enabled:
            try:
                session = await self._get_session()
                async with session.get(
                    f"{self.base_url}/memory/{namespace}/{key}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("value")
            except Exception as e:
                logger.warning(f"Failed to retrieve memory from MCP server: {e}")
        
        # Fallback to local storage
        ns_key = f"{namespace}:{key}"
        item = self._local_memory.get(ns_key)
        return item.get("value") if item else None
    
    async def delete_memory(
        self,
        key: str,
        namespace: str = "default",
    ) -> bool:
        """Delete a memory item.
        
        Args:
            key: Memory key.
            namespace: Memory namespace.
            
        Returns:
            True if deleted successfully.
        """
        if self._enabled:
            try:
                session = await self._get_session()
                async with session.delete(
                    f"{self.base_url}/memory/{namespace}/{key}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
            except Exception as e:
                logger.warning(f"Failed to delete memory from MCP server: {e}")
        
        # Fallback to local storage
        ns_key = f"{namespace}:{key}"
        if ns_key in self._local_memory:
            del self._local_memory[ns_key]
            self._save_local_memory()
        return True
    
    async def list_memories(
        self,
        namespace: str = "default",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List memory items in a namespace.
        
        Args:
            namespace: Memory namespace.
            limit: Maximum number of items to return.
            
        Returns:
            List of memory items.
        """
        if self._enabled:
            try:
                session = await self._get_session()
                async with session.get(
                    f"{self.base_url}/memory/{namespace}",
                    params={"limit": limit},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
            except Exception as e:
                logger.warning(f"Failed to list memories from MCP server: {e}")
        
        # Fallback to local storage
        prefix = f"{namespace}:"
        items = [
            item for key, item in self._local_memory.items()
            if key.startswith(prefix)
        ]
        return items[:limit]
    
    async def search_memories(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories by content.
        
        Args:
            query: Search query.
            namespace: Memory namespace.
            limit: Maximum number of results.
            
        Returns:
            List of matching memory items.
        """
        if self._enabled:
            try:
                session = await self._get_session()
                async with session.post(
                    f"{self.base_url}/memory/search",
                    json={"query": query, "namespace": namespace, "limit": limit},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
            except Exception as e:
                logger.warning(f"Failed to search memories in MCP server: {e}")
        
        # Simple local search fallback
        query_lower = query.lower()
        prefix = f"{namespace}:"
        results = []
        
        for key, item in self._local_memory.items():
            if not key.startswith(prefix):
                continue
            
            # Search in key and value
            if query_lower in key.lower():
                results.append(item)
            elif isinstance(item.get("value"), str) and query_lower in item["value"].lower():
                results.append(item)
        
        return results[:limit]
    
    async def store_conversation_context(
        self,
        conversation_id: str,
        context: Dict[str, Any],
    ) -> bool:
        """Store conversation context for persistence.
        
        Args:
            conversation_id: Conversation ID.
            context: Context data to store.
            
        Returns:
            True if stored successfully.
        """
        return await self.store_memory(
            key=f"conversation:{conversation_id}",
            value=context,
            namespace="conversations",
            metadata={"type": "conversation_context"},
        )
    
    async def retrieve_conversation_context(
        self,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve conversation context.
        
        Args:
            conversation_id: Conversation ID.
            
        Returns:
            Stored context or None.
        """
        return await self.retrieve_memory(
            key=f"conversation:{conversation_id}",
            namespace="conversations",
        )
    
    def clear_local_memory(self) -> None:
        """Clear all local memory."""
        self._local_memory.clear()
        self._save_local_memory()
        logger.info("Cleared local memory")
