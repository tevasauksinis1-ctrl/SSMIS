"""Model manager for handling model selection and switching."""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime

from llm_chat.services.ollama_client import OllamaClient
from llm_chat.services.lm_studio_client import LMStudioClient
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str
    provider: str
    size: Optional[str] = None
    modified: Optional[datetime] = None
    family: Optional[str] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "provider": self.provider,
            "size": self.size,
            "modified": self.modified.isoformat() if self.modified else None,
            "family": self.family,
            "parameters": self.parameters,
            "quantization": self.quantization,
        }


class ModelManager:
    """Manages model selection and switching across providers."""
    
    def __init__(
        self,
        ollama_host: str = "http://localhost",
        ollama_port: int = 11434,
        lm_studio_host: str = "http://localhost",
        lm_studio_port: int = 1234,
    ):
        """Initialize the model manager.
        
        Args:
            ollama_host: Ollama API host.
            ollama_port: Ollama API port.
            lm_studio_host: LM Studio API host.
            lm_studio_port: LM Studio API port.
        """
        self.ollama = OllamaClient(host=ollama_host, port=ollama_port)
        self.lm_studio = LMStudioClient(host=lm_studio_host, port=lm_studio_port)
        
        self._models_cache: Dict[str, List[ModelInfo]] = {}
        self._current_provider: str = "ollama"
        self._current_model: str = ""
        self._on_model_change: Optional[Callable[[str, str], None]] = None
    
    def set_on_model_change(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for model changes.
        
        Args:
            callback: Function called with (provider, model) when model changes.
        """
        self._on_model_change = callback
    
    @property
    def current_provider(self) -> str:
        """Get current provider."""
        return self._current_provider
    
    @property
    def current_model(self) -> str:
        """Get current model."""
        return self._current_model
    
    async def refresh_models(self) -> Dict[str, List[ModelInfo]]:
        """Refresh the list of available models from all providers.
        
        Returns:
            Dictionary mapping provider names to lists of ModelInfo.
        """
        self._models_cache.clear()
        
        # Fetch Ollama models
        try:
            ollama_models = await self.ollama.list_models_detailed()
            self._models_cache["ollama"] = []
            for m in ollama_models:
                modified = None
                if m.get("modified"):
                    try:
                        modified = datetime.fromisoformat(m["modified"])
                    except (ValueError, TypeError):
                        pass
                
                self._models_cache["ollama"].append(ModelInfo(
                    name=m.get("name", ""),
                    provider="ollama",
                    size=m.get("size"),
                    modified=modified,
                    family=m.get("details", {}).get("family"),
                    parameters=m.get("details", {}).get("parameter_size"),
                    quantization=m.get("details", {}).get("quantization_level"),
                ))
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
            self._models_cache["ollama"] = []
        
        # Fetch LM Studio models
        try:
            lm_studio_models = await self.lm_studio.list_models_detailed()
            self._models_cache["lm_studio"] = [
                ModelInfo(
                    name=m.get("id", ""),
                    provider="lm_studio",
                    family=m.get("owned_by"),
                )
                for m in lm_studio_models
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch LM Studio models: {e}")
            self._models_cache["lm_studio"] = []
        
        return self._models_cache
    
    def get_cached_models(self, provider: Optional[str] = None) -> Dict[str, List[ModelInfo]]:
        """Get cached models.
        
        Args:
            provider: Optional provider to filter by.
            
        Returns:
            Dictionary of cached models.
        """
        if provider:
            return {provider: self._models_cache.get(provider, [])}
        return self._models_cache
    
    def switch_model(self, provider: str, model: str) -> None:
        """Switch to a different model.
        
        Args:
            provider: Provider name ("ollama" or "lm_studio").
            model: Model name.
        """
        if provider not in ["ollama", "lm_studio"]:
            raise ValueError(f"Unknown provider: {provider}")
        
        self._current_provider = provider
        self._current_model = model
        
        logger.info(f"Switched to model: {model} ({provider})")
        
        if self._on_model_change:
            self._on_model_change(provider, model)
    
    async def get_model_info(self, provider: str, model: str) -> Optional[ModelInfo]:
        """Get detailed information about a specific model.
        
        Args:
            provider: Provider name.
            model: Model name.
            
        Returns:
            ModelInfo or None if not found.
        """
        if provider not in self._models_cache:
            await self.refresh_models()
        
        for m in self._models_cache.get(provider, []):
            if m.name == model:
                return m
        
        return None
    
    async def check_providers_health(self) -> Dict[str, bool]:
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
