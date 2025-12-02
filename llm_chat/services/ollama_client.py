"""Ollama API client for chat interactions."""

import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

import aiohttp

from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, host: str = "http://localhost", port: int = 11434):
        """Initialize the Ollama client.
        
        Args:
            host: Ollama API host.
            port: Ollama API port.
        """
        self.base_url = f"{host}:{port}"
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def health_check(self) -> bool:
        """Check if Ollama is running.
        
        Returns:
            True if Ollama is reachable, False otherwise.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models.
        
        Returns:
            List of model names.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def list_models_detailed(self) -> List[Dict[str, Any]]:
        """List available models with detailed information.
        
        Returns:
            List of model dictionaries with detailed info.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Send a chat message and get response.
        
        Args:
            model: Model name to use.
            messages: List of message dictionaries with "role" and "content".
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional API parameters.
            
        Returns:
            Assistant response text.
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        payload.update(kwargs)
        
        async with session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API error: {response.status} - {error_text}")
            
            data = await response.json()
            return data.get("message", {}).get("content", "")
    
    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response.
        
        Args:
            model: Model name to use.
            messages: List of message dictionaries with "role" and "content".
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional API parameters.
            
        Yields:
            Response tokens as they arrive.
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        payload.update(kwargs)
        
        async with session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API error: {response.status} - {error_text}")
            
            async for line in response.content:
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
    
    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Generate text from a prompt.
        
        Args:
            model: Model name to use.
            prompt: Input prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional API parameters.
            
        Returns:
            Generated text.
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        payload.update(kwargs)
        
        async with session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API error: {response.status} - {error_text}")
            
            data = await response.json()
            return data.get("response", "")
    
    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Pull a model from Ollama library.
        
        Args:
            model: Model name to pull.
            
        Yields:
            Progress updates.
        """
        session = await self._get_session()
        
        async with session.post(
            f"{self.base_url}/api/pull",
            json={"name": model, "stream": True},
            timeout=aiohttp.ClientTimeout(total=3600)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to pull model: {response.status} - {error_text}")
            
            async for line in response.content:
                if line:
                    try:
                        yield json.loads(line.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
