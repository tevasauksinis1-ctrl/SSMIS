"""Chat client for managing conversations with LLM models."""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from datetime import datetime

from llm_chat.services.ollama_client import OllamaClient
from llm_chat.services.lm_studio_client import LMStudioClient
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    model: Optional[str] = None
    provider: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "provider": self.provider,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            model=data.get("model"),
            provider=data.get("provider"),
        )


@dataclass
class Conversation:
    """Represents a chat conversation."""
    id: str
    title: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
        )


class ChatClient:
    """Main chat client for interacting with LLM models."""
    
    def __init__(
        self,
        ollama_host: str = "http://localhost",
        ollama_port: int = 11434,
        lm_studio_host: str = "http://localhost",
        lm_studio_port: int = 1234,
    ):
        """Initialize the chat client.
        
        Args:
            ollama_host: Ollama API host.
            ollama_port: Ollama API port.
            lm_studio_host: LM Studio API host.
            lm_studio_port: LM Studio API port.
        """
        self.ollama = OllamaClient(host=ollama_host, port=ollama_port)
        self.lm_studio = LMStudioClient(host=lm_studio_host, port=lm_studio_port)
        
        self._current_provider: str = "ollama"
        self._current_model: str = "llama2"
        self._conversation: List[Message] = []
        self._system_prompt: Optional[str] = None
        
        # Model settings
        self.temperature: float = 0.7
        self.max_tokens: int = 2048
        self.context_length: int = 4096
    
    @property
    def current_provider(self) -> str:
        """Get current provider name."""
        return self._current_provider
    
    @property
    def current_model(self) -> str:
        """Get current model name."""
        return self._current_model
    
    def set_provider(self, provider: str) -> None:
        """Set the current provider.
        
        Args:
            provider: Provider name ("ollama" or "lm_studio").
        """
        if provider not in ["ollama", "lm_studio"]:
            raise ValueError(f"Unknown provider: {provider}")
        self._current_provider = provider
        logger.info(f"Switched to provider: {provider}")
    
    def set_model(self, model: str) -> None:
        """Set the current model.
        
        Args:
            model: Model name.
        """
        self._current_model = model
        logger.info(f"Switched to model: {model}")
    
    def set_system_prompt(self, prompt: Optional[str]) -> None:
        """Set the system prompt.
        
        Args:
            prompt: System prompt or None to clear.
        """
        self._system_prompt = prompt
    
    def clear_conversation(self) -> None:
        """Clear the current conversation."""
        self._conversation.clear()
        logger.info("Conversation cleared")
    
    def get_conversation(self) -> List[Message]:
        """Get the current conversation messages."""
        return self._conversation.copy()
    
    def _get_client(self):
        """Get the appropriate client for the current provider."""
        if self._current_provider == "ollama":
            return self.ollama
        elif self._current_provider == "lm_studio":
            return self.lm_studio
        else:
            raise ValueError(f"Unknown provider: {self._current_provider}")
    
    async def send_message(
        self,
        message: str,
        stream: bool = False,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Send a message and get a response.
        
        Args:
            message: User message to send.
            stream: Whether to stream the response.
            on_token: Callback for streaming tokens.
            
        Returns:
            Assistant response.
        """
        # Add user message to conversation
        user_message = Message(
            role="user",
            content=message,
            model=self._current_model,
            provider=self._current_provider,
        )
        self._conversation.append(user_message)
        
        # Build messages list for API
        messages = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        
        for msg in self._conversation:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Get client and send request
        client = self._get_client()
        
        try:
            if stream and on_token:
                response_text = ""
                async for token in client.chat_stream(
                    model=self._current_model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                ):
                    response_text += token
                    on_token(token)
                response = response_text
            else:
                response = await client.chat(
                    model=self._current_model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            
            # Add assistant message to conversation
            assistant_message = Message(
                role="assistant",
                content=response,
                model=self._current_model,
                provider=self._current_provider,
            )
            self._conversation.append(assistant_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            # Remove the user message if request failed
            self._conversation.pop()
            raise
    
    async def list_models(self) -> Dict[str, List[str]]:
        """List available models from all providers.
        
        Returns:
            Dictionary mapping provider names to lists of model names.
        """
        models = {}
        
        try:
            ollama_models = await self.ollama.list_models()
            models["ollama"] = ollama_models
        except Exception as e:
            logger.warning(f"Failed to get Ollama models: {e}")
            models["ollama"] = []
        
        try:
            lm_studio_models = await self.lm_studio.list_models()
            models["lm_studio"] = lm_studio_models
        except Exception as e:
            logger.warning(f"Failed to get LM Studio models: {e}")
            models["lm_studio"] = []
        
        return models
    
    async def check_health(self) -> Dict[str, bool]:
        """Check health of all providers.
        
        Returns:
            Dictionary mapping provider names to health status.
        """
        health = {}
        
        try:
            health["ollama"] = await self.ollama.health_check()
        except Exception:
            health["ollama"] = False
        
        try:
            health["lm_studio"] = await self.lm_studio.health_check()
        except Exception:
            health["lm_studio"] = False
        
        return health
