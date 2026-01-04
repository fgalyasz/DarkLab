"""
Configuration Manager for Photo Editor
Handles application settings and state persistence
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QRect


class ConfigManager:
    """Manages application configuration and state"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path.home() / ".photo_editor" / "config.json"
        # Get project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        self.default_config_file = project_root / "config" / "default_config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self.logger.info("Configuration loaded successfully")
            else:
                self._config = self._load_default_config()
                self.save_config()
                self.logger.info("Default configuration created")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._config = self._load_default_config()
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, default=str)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from file"""
        try:
            with open(self.default_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load default config file: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration if file loading fails"""
        return {
            "window": {
                "geometry": None,
                "maximized": False,
                "current_panel": "library"
            },
            "theme": {
                "name": "dark",
                "accent_color": "#007AFF"
            },
            "panels": {
                "library": {},
                "develop": {},
                "print": {},
                "slideshow": {},
                "website": {}
            }
        }
    
    def get_window_geometry(self) -> Optional[QRect]:
        """Get saved window geometry"""
        geometry_data = self.get("window.geometry")
        if geometry_data:
            return QRect(
                geometry_data.get("x", 100),
                geometry_data.get("y", 100),
                geometry_data.get("width", 1200),
                geometry_data.get("height", 800)
            )
        return None
    
    def set_window_geometry(self, geometry: QRect) -> None:
        """Save window geometry"""
        self.set("window.geometry", {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height()
        })
    
    def get_current_panel(self) -> str:
        """Get current active panel"""
        return self.get("window.current_panel", "library")
    
    def set_current_panel(self, panel_name: str) -> None:
        """Set current active panel"""
        self.set("window.current_panel", panel_name)
