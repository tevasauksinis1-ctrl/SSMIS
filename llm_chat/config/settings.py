"""Application settings and configuration."""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class ServicePorts:
    """Port configuration for service isolation."""
    ollama: int = 11434
    lm_studio: int = 1234
    tts: int = 8000
    mcp_memory: int = 3100


@dataclass
class TTSSettings:
    """Text-to-Speech settings."""
    enabled: bool = False
    api_url: str = "http://localhost:8000/v1/audio/speech"
    model: str = "tts-1"
    voice: str = "alloy"
    speed: float = 1.0


@dataclass
class ModelSettings:
    """Model configuration settings."""
    default_provider: str = "ollama"
    default_model: str = "llama2"
    temperature: float = 0.7
    max_tokens: int = 2048
    context_length: int = 4096


@dataclass
class MCPSettings:
    """MCP memory server settings."""
    enabled: bool = True
    host: str = "localhost"
    port: int = 3100
    memory_file: str = "~/.llm_chat/memory.json"


@dataclass
class UISettings:
    """User interface settings."""
    theme: str = "dark"
    font_size: int = 12
    font_family: str = "Segoe UI"
    window_width: int = 800
    window_height: int = 600
    start_minimized: bool = False
    minimize_to_tray: bool = True
    show_system_tray: bool = True


@dataclass
class CUDASettings:
    """CUDA/GPU acceleration settings."""
    enabled: bool = True
    cuda_version: str = "12.1"
    device_id: int = 0


@dataclass
class Settings:
    """Main application settings."""
    ports: ServicePorts = field(default_factory=ServicePorts)
    tts: TTSSettings = field(default_factory=TTSSettings)
    model: ModelSettings = field(default_factory=ModelSettings)
    mcp: MCPSettings = field(default_factory=MCPSettings)
    ui: UISettings = field(default_factory=UISettings)
    cuda: CUDASettings = field(default_factory=CUDASettings)
    
    # Application paths
    config_dir: str = field(default_factory=lambda: str(Path.home() / ".llm_chat"))
    history_file: str = field(default_factory=lambda: str(Path.home() / ".llm_chat" / "history.json"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "ports": {
                "ollama": self.ports.ollama,
                "lm_studio": self.ports.lm_studio,
                "tts": self.ports.tts,
                "mcp_memory": self.ports.mcp_memory,
            },
            "tts": {
                "enabled": self.tts.enabled,
                "api_url": self.tts.api_url,
                "model": self.tts.model,
                "voice": self.tts.voice,
                "speed": self.tts.speed,
            },
            "model": {
                "default_provider": self.model.default_provider,
                "default_model": self.model.default_model,
                "temperature": self.model.temperature,
                "max_tokens": self.model.max_tokens,
                "context_length": self.model.context_length,
            },
            "mcp": {
                "enabled": self.mcp.enabled,
                "host": self.mcp.host,
                "port": self.mcp.port,
                "memory_file": self.mcp.memory_file,
            },
            "ui": {
                "theme": self.ui.theme,
                "font_size": self.ui.font_size,
                "font_family": self.ui.font_family,
                "window_width": self.ui.window_width,
                "window_height": self.ui.window_height,
                "start_minimized": self.ui.start_minimized,
                "minimize_to_tray": self.ui.minimize_to_tray,
                "show_system_tray": self.ui.show_system_tray,
            },
            "cuda": {
                "enabled": self.cuda.enabled,
                "cuda_version": self.cuda.cuda_version,
                "device_id": self.cuda.device_id,
            },
            "config_dir": self.config_dir,
            "history_file": self.history_file,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        settings = cls()
        
        if "ports" in data:
            ports = data["ports"]
            settings.ports = ServicePorts(
                ollama=ports.get("ollama", 11434),
                lm_studio=ports.get("lm_studio", 1234),
                tts=ports.get("tts", 8000),
                mcp_memory=ports.get("mcp_memory", 3100),
            )
        
        if "tts" in data:
            tts = data["tts"]
            settings.tts = TTSSettings(
                enabled=tts.get("enabled", False),
                api_url=tts.get("api_url", "http://localhost:8000/v1/audio/speech"),
                model=tts.get("model", "tts-1"),
                voice=tts.get("voice", "alloy"),
                speed=tts.get("speed", 1.0),
            )
        
        if "model" in data:
            model = data["model"]
            settings.model = ModelSettings(
                default_provider=model.get("default_provider", "ollama"),
                default_model=model.get("default_model", "llama2"),
                temperature=model.get("temperature", 0.7),
                max_tokens=model.get("max_tokens", 2048),
                context_length=model.get("context_length", 4096),
            )
        
        if "mcp" in data:
            mcp = data["mcp"]
            settings.mcp = MCPSettings(
                enabled=mcp.get("enabled", True),
                host=mcp.get("host", "localhost"),
                port=mcp.get("port", 3100),
                memory_file=mcp.get("memory_file", "~/.llm_chat/memory.json"),
            )
        
        if "ui" in data:
            ui = data["ui"]
            settings.ui = UISettings(
                theme=ui.get("theme", "dark"),
                font_size=ui.get("font_size", 12),
                font_family=ui.get("font_family", "Segoe UI"),
                window_width=ui.get("window_width", 800),
                window_height=ui.get("window_height", 600),
                start_minimized=ui.get("start_minimized", False),
                minimize_to_tray=ui.get("minimize_to_tray", True),
                show_system_tray=ui.get("show_system_tray", True),
            )
        
        if "cuda" in data:
            cuda = data["cuda"]
            settings.cuda = CUDASettings(
                enabled=cuda.get("enabled", True),
                cuda_version=cuda.get("cuda_version", "12.1"),
                device_id=cuda.get("device_id", 0),
            )
        
        if "config_dir" in data:
            settings.config_dir = data["config_dir"]
        
        if "history_file" in data:
            settings.history_file = data["history_file"]
        
        return settings


# Default settings instance
DEFAULT_SETTINGS = Settings()
