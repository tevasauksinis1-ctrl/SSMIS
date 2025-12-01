"""Configuration manager for loading and saving settings."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from llm_chat.config.settings import Settings


class ConfigManager:
    """Manages application configuration loading and saving."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config manager.
        
        Args:
            config_path: Optional path to config file. Defaults to ~/.llm_chat/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".llm_chat" / "config.json"
        
        self._settings: Optional[Settings] = None
    
    def ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Settings:
        """Load settings from config file.
        
        Returns:
            Settings object with loaded or default values.
        """
        if self._settings is not None:
            return self._settings
        
        self.ensure_config_dir()
        
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._settings = Settings.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                # Fall back to defaults on error
                self._settings = Settings()
        else:
            self._settings = Settings()
            self.save(self._settings)
        
        return self._settings
    
    def save(self, settings: Settings) -> None:
        """Save settings to config file.
        
        Args:
            settings: Settings object to save.
        """
        self.ensure_config_dir()
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, indent=2)
        
        self._settings = settings
    
    def reset(self) -> Settings:
        """Reset settings to defaults.
        
        Returns:
            Default Settings object.
        """
        self._settings = Settings()
        self.save(self._settings)
        return self._settings
    
    def update(self, updates: Dict[str, Any]) -> Settings:
        """Update specific settings.
        
        Args:
            updates: Dictionary of settings to update.
            
        Returns:
            Updated Settings object.
        """
        current = self.load()
        current_dict = current.to_dict()
        
        # Deep merge updates
        self._deep_merge(current_dict, updates)
        
        self._settings = Settings.from_dict(current_dict)
        self.save(self._settings)
        return self._settings
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep merge updates into base dictionary.
        
        Args:
            base: Base dictionary to merge into.
            updates: Updates to merge.
        """
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
