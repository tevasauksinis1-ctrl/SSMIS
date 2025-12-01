"""LM Studio API client for chat interactions."""

import json
from typing import List, Dict, Any, Optional, AsyncGenerator

import aiohttp

from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class LMStudioClient:
    """Client for interacting with LM Studio OpenAI-compatible API."""
    
    def __init__(self, host: str = "http://localhost", port: int = 1234):
        """Initialize the LM Studio client.
        
        Args:
            host: LM Studio API host.
            port: LM Studio API port.
        """
        self.base_url = f"{host}:{port}/v1"
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
        """Check if LM Studio is running.
        
        Returns:
            True if LM Studio is reachable, False otherwise.
        """
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"LM Studio health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models.
        
        Returns:
            List of model names.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["id"] for model in data.get("data", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list LM Studio models: {e}")
            return []
    
    async def list_models_detailed(self) -> List[Dict[str, Any]]:
        """List available models with detailed information.
        
        Returns:
            List of model dictionaries with detailed info.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                return []
        except Exception as e:
            logger.error(f"Failed to list LM Studio models: {e}")
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
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        payload.update(kwargs)
        
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"LM Studio API error: {response.status} - {error_text}")
            
            data = await response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
    
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
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        payload.update(kwargs)
        
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"LM Studio API error: {response.status} - {error_text}")
            
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
    
    async def completions(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Generate text from a prompt using completions API.
        
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
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        payload.update(kwargs)
        
        async with session.post(
            f"{self.base_url}/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"LM Studio API error: {response.status} - {error_text}")
            
            data = await response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("text", "")
            return ""
