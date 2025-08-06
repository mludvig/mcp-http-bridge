"""Configuration file handling for MCP wrapper."""

import json
import logging
from pathlib import Path
from typing import Any

from .models import MCPWrapperConfig, WrapperSettings

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._config: MCPWrapperConfig | None = None
        self._settings: WrapperSettings | None = None

    def load_config(self) -> MCPWrapperConfig:
        """Load and validate configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path) as f:
                config_data = json.load(f)

            self._config = MCPWrapperConfig(**config_data)
            logger.info(
                f"Loaded configuration for MCP server: {self._config.server.command}"
            )
            return self._config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}") from e

    def get_settings(self, **overrides) -> WrapperSettings:
        """Get runtime settings with optional overrides."""
        if self._settings is None:
            self._settings = WrapperSettings()

        # Apply any runtime overrides
        if overrides:
            settings_dict = self._settings.model_dump()
            settings_dict.update(overrides)
            return WrapperSettings(**settings_dict)

        return self._settings

    @property
    def config(self) -> MCPWrapperConfig:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def get_server_info(self) -> dict[str, Any]:
        """Get information about the configured MCP server."""
        if self._config is None:
            return {}

        return {
            "command": self._config.server.command,
            "args": self._config.server.args,
            "has_env": bool(self._config.server.env),
            "cwd": self._config.server.cwd,
        }
