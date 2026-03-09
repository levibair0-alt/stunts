"""
Configuration management for Voice Control Core with hot-reload support.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class VoiceConfig:
    """Configuration for Voice Control Core."""

    # Audio settings
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    audio_format: str = "int16"

    # Wake word settings
    wake_word: str = "athena"
    wake_word_sensitivity: float = 0.8

    # Transcription settings
    whisper_model: str = "base"
    transcription_language: str = "en"

    # Confidence thresholds
    confidence_execute: float = 0.7
    confidence_clarify: float = 0.4
    confidence_reject: float = 0.0

    # WebSocket settings
    websocket_host: str = "localhost"
    websocket_port: int = 8766

    # Database settings
    audit_db_path: str = "voice_commands.db"

    # Safety settings
    safe_mode_enabled: bool = True
    require_confirmation_for_dangerous: bool = True

    # Execution settings
    command_timeout: int = 30
    subprocess_timeout: int = 60

    # Demo mode settings
    demo_commands_file: Optional[str] = None

    # Intent mapping
    intent_map: dict[str, str] = field(
        default_factory=lambda: {
            "QUERY": "Sensor",
            "VERIFY": "Validator",
            "CREATE": "Generator",
            "MONETIZE": "Monetizer",
            "AUDIT": "Auditor",
        }
    )

    # Dangerous patterns (regex)
    dangerous_patterns: list[str] = field(
        default_factory=lambda: [
            r"rm\s+-rf",
            r"format\s+",
            r"shutdown\s+-h\s+now",
            r"sudo.*rm",
            r"dd\s+if=.*of=/dev",
            r"mkfs\.",
            r">\s*/dev/sd",
        ]
    )

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config with optional file loading."""
        self._config_path: Optional[str] = config_path
        self._last_modified: float = 0

        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)

    def load_from_file(self, path: str) -> None:
        """Load configuration from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        for key, value in data.items():
            if hasattr(self, key) and not key.startswith("_"):
                setattr(self, key, value)

        self._config_path = path
        self._last_modified = os.path.getmtime(path)

    def save_to_file(self, path: Optional[str] = None) -> None:
        """Save configuration to JSON file."""
        save_path = path or self._config_path
        if not save_path:
            raise ValueError("No config path specified")

        data = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def check_reload(self) -> bool:
        """Check if config file has changed and reload if necessary."""
        if not self._config_path or not os.path.exists(self._config_path):
            return False

        current_mtime = os.path.getmtime(self._config_path)
        if current_mtime > self._last_modified:
            self.load_from_file(self._config_path)
            return True

        return False

    def get_engine_for_intent(self, intent: str) -> Optional[str]:
        """Get the engine name for a given intent."""
        return self.intent_map.get(intent.upper())

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }
