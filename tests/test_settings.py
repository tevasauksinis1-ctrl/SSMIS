"""Tests for settings and configuration."""

import pytest
import tempfile
import json
from pathlib import Path

from llm_chat.config.settings import (
    Settings, ServicePorts, TTSSettings, ModelSettings,
    MCPSettings, UISettings, CUDASettings, DEFAULT_SETTINGS
)
from llm_chat.utils.config_manager import ConfigManager


class TestSettings:
    """Tests for Settings class."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.ports.ollama == 11434
        assert settings.ports.lm_studio == 1234
        assert settings.ports.tts == 8000
        assert settings.ports.mcp_memory == 3100
        
        assert settings.model.default_provider == "ollama"
        assert settings.model.temperature == 0.7
        
        assert settings.tts.enabled == False
        assert settings.tts.voice == "alloy"
        
        assert settings.mcp.enabled == True
        assert settings.mcp.port == 3100
        
        assert settings.ui.theme == "dark"
        
        assert settings.cuda.enabled == True
        assert settings.cuda.cuda_version == "12.1"
    
    def test_settings_to_dict(self):
        """Test settings serialization to dict."""
        settings = Settings()
        data = settings.to_dict()
        
        assert "ports" in data
        assert "tts" in data
        assert "model" in data
        assert "mcp" in data
        assert "ui" in data
        assert "cuda" in data
        
        assert data["ports"]["ollama"] == 11434
        assert data["model"]["temperature"] == 0.7
    
    def test_settings_from_dict(self):
        """Test settings deserialization from dict."""
        data = {
            "ports": {"ollama": 12345},
            "model": {"temperature": 0.9},
            "tts": {"enabled": True, "voice": "nova"},
        }
        
        settings = Settings.from_dict(data)
        
        assert settings.ports.ollama == 12345
        assert settings.model.temperature == 0.9
        assert settings.tts.enabled == True
        assert settings.tts.voice == "nova"
        
        # Check defaults are preserved for missing fields
        assert settings.ports.lm_studio == 1234
    
    def test_settings_roundtrip(self):
        """Test settings serialization roundtrip."""
        original = Settings()
        original.ports.ollama = 9999
        original.model.temperature = 0.5
        
        data = original.to_dict()
        restored = Settings.from_dict(data)
        
        assert restored.ports.ollama == original.ports.ollama
        assert restored.model.temperature == original.model.temperature


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_load_creates_default(self):
        """Test that loading non-existent config creates defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            manager = ConfigManager(str(config_path))
            settings = manager.load()
            
            assert settings.ports.ollama == 11434
            assert config_path.exists()
    
    def test_save_and_load(self):
        """Test saving and loading settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            manager = ConfigManager(str(config_path))
            settings = Settings()
            settings.ports.ollama = 55555
            settings.model.temperature = 0.3
            
            manager.save(settings)
            
            # Create new manager and load
            manager2 = ConfigManager(str(config_path))
            loaded = manager2.load()
            
            assert loaded.ports.ollama == 55555
            assert loaded.model.temperature == 0.3
    
    def test_reset(self):
        """Test resetting to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            manager = ConfigManager(str(config_path))
            
            # Modify and save
            settings = Settings()
            settings.ports.ollama = 99999
            manager.save(settings)
            
            # Reset
            reset_settings = manager.reset()
            
            assert reset_settings.ports.ollama == 11434
    
    def test_update(self):
        """Test updating specific settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            manager = ConfigManager(str(config_path))
            manager.load()
            
            updated = manager.update({
                "ports": {"ollama": 77777},
                "model": {"temperature": 0.1}
            })
            
            assert updated.ports.ollama == 77777
            assert updated.model.temperature == 0.1
            # Other settings should be preserved
            assert updated.ports.lm_studio == 1234
