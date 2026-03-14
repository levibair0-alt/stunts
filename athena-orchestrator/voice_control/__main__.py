#!/usr/bin/env python3
"""
Voice Control Core - Entry Point

Usage:
    python -m voice_control
    python -m voice_control --demo
"""

import argparse
import asyncio
import sys

from .controller import VoiceController
from .config import VoiceConfig


def main() -> int:
    """Main entry point for the Voice Control module."""
    parser = argparse.ArgumentParser(
        description="Voice Control Core - Athena Command OS Interface"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with simulated voice input",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8766,
        help="WebSocket port (default: 8766)",
    )

    args = parser.parse_args()

    try:
        config = VoiceConfig()
        if args.config:
            config.load_from_file(args.config)
        if args.port:
            config.websocket_port = args.port

        controller = VoiceController(config=config, demo_mode=args.demo)
        asyncio.run(controller.run())
        return 0

    except KeyboardInterrupt:
        print("\n🛑 Voice Control stopped by user")
        return 0
    except Exception as e:
        print(f"\n💥 Voice Control error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
