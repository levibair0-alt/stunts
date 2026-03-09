"""
Voice Control Core - Athena Command OS Interface

Provides intent-to-execution interface for "Speak and Execute" functionality
with real-time WebSocket broadcasting and Emergency Stop safety protocol.
"""

from .config import VoiceConfig

__version__ = "1.0.0"
__all__ = ["VoiceController", "VoiceConfig"]

# Lazy import VoiceController to avoid loading heavy dependencies on init
def __getattr__(name):
    if name == "VoiceController":
        from .controller import VoiceController
        return VoiceController
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
