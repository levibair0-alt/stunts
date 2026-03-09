"""
Main controller for Voice Control Core - orchestrates the full pipeline.
"""

import asyncio
import signal
import sys
import time
from enum import Enum
from typing import Optional

from .command_bus import AuditLogger, CommandBus
from .config import VoiceConfig
from .emergency_stop import EmergencyStopProtocol
from .executor import CommandExecutor
from .intent_parser import IntentParser, IntentType, ParsedIntent
from .safe_mode import SafeModeGuard
from .voice_input import TranscriptionResult, VoiceInput
from .wake_word import WakeWordDetector
from .websocket_server import VoiceWebSocketServer


class SystemState(Enum):
    """Voice Control system states."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    ERROR = "ERROR"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class VoiceController:
    """
    Main controller for Voice Control Core.

    Orchestrates the full pipeline:
    Audio Capture → Wake Word → Transcription → Intent Parsing →
    Command Bus → Executor → WebSocket Broadcast → Audit Log
    """

    def __init__(
        self,
        config: Optional[VoiceConfig] = None,
        demo_mode: bool = False,
    ):
        """
        Initialize Voice Controller.

        Args:
            config: Voice configuration
            demo_mode: Whether to run in demo mode with simulated input
        """
        self.config = config or VoiceConfig()
        self.demo_mode = demo_mode

        # Initialize components
        self.voice_input = VoiceInput(
            sample_rate=self.config.sample_rate,
            chunk_size=self.config.chunk_size,
            channels=self.config.channels,
            model_size=self.config.whisper_model,
        )

        self.wake_word_detector = WakeWordDetector(
            wake_word=self.config.wake_word,
            sensitivity=self.config.wake_word_sensitivity,
        )

        self.intent_parser = IntentParser(
            confidence_execute=self.config.confidence_execute,
            confidence_clarify=self.config.confidence_clarify,
            safe_mode_enabled=self.config.safe_mode_enabled,
        )

        self.audit_logger = AuditLogger(db_path=self.config.audit_db_path)

        self.safe_mode_guard = SafeModeGuard(
            custom_patterns=self.config.dangerous_patterns,
            enabled=self.config.safe_mode_enabled,
        )

        self.command_executor = CommandExecutor(
            safe_mode_guard=self.safe_mode_guard,
        )

        self.command_bus = CommandBus(
            audit_logger=self.audit_logger,
            safe_mode_enabled=self.config.safe_mode_enabled,
        )

        self.websocket_server = VoiceWebSocketServer(
            host=self.config.websocket_host,
            port=self.config.websocket_port,
        )

        self.emergency_stop = EmergencyStopProtocol(
            websocket_server=self.websocket_server,
            audit_logger=self.audit_logger,
        )

        # State management
        self.state = SystemState.IDLE
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Demo mode commands
        self._demo_commands = [
            "Athena show me opportunities",
            "Athena generate offer for freelancers",
            "Athena verify last session",
            "Athena audit status",
            "Athena emergency stop",
            "Resume Athena operations",
        ]
        self._demo_index = 0

        # Register handlers
        self._register_command_handlers()

        # Setup signal handlers
        self._setup_signals()

    def _register_command_handlers(self) -> None:
        """Register command handlers with the command bus."""
        # Register handlers for each intent type
        for intent_type in IntentType:
            if intent_type not in [IntentType.UNKNOWN, IntentType.CLARIFY]:
                self.command_bus.register_handler(
                    intent_type,
                    self._create_handler(intent_type),
                )

        # Register callback for WebSocket broadcasts
        self.command_bus.register_callback(self._on_command_complete)

    def _create_handler(self, intent_type: IntentType):
        """Create a handler function for an intent type."""

        async def handler(intent: ParsedIntent):
            # Check emergency stop first
            if self.emergency_stop.is_frozen():
                if intent.intent_type == IntentType.RESUME:
                    success = await self.emergency_stop.resume(intent.raw_transcript)
                    if success:
                        self.state = SystemState.IDLE
                    return await self._create_result(success, "System resumed")
                else:
                    return await self._create_result(
                        False,
                        "System frozen. Say 'resume Athena operations' to continue.",
                    )

            # Execute the command
            return await self.command_executor.execute(intent)

        return handler

    async def _create_result(self, success: bool, message: str):
        """Create a simple CommandResult."""
        from .command_bus import CommandResult, ExecutionStatus

        return CommandResult(
            success=success,
            output=message if success else "",
            error=None if success else message,
            duration_ms=0,
            status=ExecutionStatus.SUCCESS if success else ExecutionStatus.BLOCKED,
        )

    def _on_command_complete(self, intent: ParsedIntent, result):
        """Callback when command execution completes."""
        # Broadcast result to WebSocket
        self.websocket_server.broadcast_execution_result(
            success=result.success,
            output=result.output,
            duration_ms=result.duration_ms,
            engine=intent.target_engine,
        )

    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_event_loop().add_signal_handler(
                sig, lambda: asyncio.create_task(self._shutdown())
            )

    async def _shutdown(self) -> None:
        """Graceful shutdown handler."""
        print("\n🛑 Shutting down Voice Control...")
        self._running = False
        self._shutdown_event.set()

        # Stop recording
        self.voice_input.stop_recording()

        # Stop WebSocket server
        await self.websocket_server.stop()

        print("✅ Voice Control shut down complete")

    async def run(self) -> None:
        """Main execution loop."""
        print("\n" + "=" * 50)
        print("🎙️  VOICE CONTROL CORE - ATHENA COMMAND OS")
        print("=" * 50)
        print(f"Mode: {'DEMO' if self.demo_mode else 'LIVE'}")
        print(f"Wake Word: '{self.config.wake_word.title()}'")
        print(f"WebSocket: ws://{self.config.websocket_host}:{self.config.websocket_port}")
        print(f"Safe Mode: {'ON' if self.config.safe_mode_enabled else 'OFF'}")
        print("=" * 50 + "\n")

        # Start WebSocket server
        await self.websocket_server.start()

        # Start voice input
        if not self.demo_mode:
            if not self.voice_input.start_recording():
                print("❌ Failed to start audio recording")
                return

        self._running = True
        self.state = SystemState.LISTENING

        # Broadcast initial status
        self.websocket_server.broadcast_status_update("LISTENING")

        try:
            if self.demo_mode:
                await self._run_demo_mode()
            else:
                await self._run_live_mode()
        except asyncio.CancelledError:
            pass

    async def _run_live_mode(self) -> None:
        """Run in live mode with actual microphone input."""
        print("🎤 Listening for voice commands...")
        print(f"   Say '{self.config.wake_word.title()}' followed by your command")
        print("   Press Ctrl+C to exit\n")

        while self._running and not self._shutdown_event.is_set():
            try:
                # Check for config reload
                self.config.check_reload()

                # Record audio
                self.state = SystemState.LISTENING
                self.websocket_server.broadcast_status_update("LISTENING")

                audio_data = self.voice_input.record_audio(duration=5.0)

                if not audio_data:
                    await asyncio.sleep(0.1)
                    continue

                # Transcribe
                self.state = SystemState.PROCESSING
                self.websocket_server.broadcast_status_update("PROCESSING")

                result = self.voice_input.transcribe(audio_data)

                if not result.text:
                    continue

                print(f"📝 Heard: '{result.text}' (confidence: {result.confidence:.2f})")

                # Check wake word
                detected, command_text = self.wake_word_detector.detect(result.text)

                if not detected:
                    continue

                if not command_text:
                    print("👂 Wake word detected, waiting for command...")
                    # Record additional audio for command
                    audio_data = self.voice_input.record_audio(duration=3.0)
                    if audio_data:
                        result = self.voice_input.transcribe(audio_data)
                        command_text = result.text

                if not command_text:
                    continue

                # Process the command
                await self._process_command(command_text, result.confidence)

            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                self.state = SystemState.ERROR

            await asyncio.sleep(0.1)

    async def _run_demo_mode(self) -> None:
        """Run in demo mode with simulated voice input."""
        print("🎬 DEMO MODE - Simulating voice commands\n")

        for command in self._demo_commands:
            if not self._running or self._shutdown_event.is_set():
                break

            print(f"\n🎤 Simulating: '{command}'")

            # Simulate wake word detection
            detected, command_text = self.wake_word_detector.detect(command)

            if not detected:
                print("   (Wake word not detected, skipping)")
                continue

            # Process the command
            await self._process_command(command_text or command, 0.9)

            # Wait between commands
            await asyncio.sleep(3.0)

        print("\n✅ Demo completed")
        await self._shutdown()

    async def _process_command(self, transcript: str, confidence: float) -> None:
        """
        Process a voice command through the full pipeline.

        Args:
            transcript: The transcribed command text
            confidence: Transcription confidence score
        """
        print(f"⚡ Processing: '{transcript}'")

        # Check emergency stop commands first
        is_emergency, cmd_type = self.emergency_stop.check_emergency_command(transcript)

        if is_emergency:
            if cmd_type == "stop":
                result = await self.emergency_stop.activate(transcript)
                self.state = SystemState.EMERGENCY_STOP
                print(f"🚨 {result.message}")
                return
            elif cmd_type == "resume":
                success = await self.emergency_stop.resume(transcript)
                if success:
                    self.state = SystemState.IDLE
                return

        # Parse intent
        intent = self.intent_parser.parse(transcript, confidence)

        # Broadcast intent detection
        self.websocket_server.broadcast_intent_detected(
            intent=intent.intent_type.value,
            confidence=intent.confidence,
            raw_transcript=transcript,
            engine=intent.target_engine,
        )

        print(f"   Intent: {intent.intent_type.value} (confidence: {intent.confidence:.2f})")

        # Handle clarification
        if intent.requires_clarification:
            print(f"   Clarification needed: {intent.clarification_prompt}")
            self.websocket_server.broadcast_system_message(
                f"Clarification needed: {intent.clarification_prompt}",
                level="warning",
            )
            return

        # Check confidence
        if intent.confidence < self.config.confidence_clarify:
            print("   Confidence too low, ignoring")
            self.websocket_server.broadcast_system_message(
                "I didn't catch that, please repeat",
                level="warning",
            )
            return

        # Broadcast engine trigger
        if intent.target_engine:
            self.websocket_server.broadcast_engine_triggered(
                engine=intent.target_engine,
                action=intent.intent_type.value,
            )

        # Execute command
        self.state = SystemState.EXECUTING
        self.websocket_server.broadcast_status_update("EXECUTING")

        result = self.command_bus.dispatch(intent)

        # Display result
        if result.success:
            print(f"   ✅ Success: {result.output[:100]}")
        else:
            print(f"   ❌ Failed: {result.error or 'Unknown error'}")

        # Return to idle
        self.state = SystemState.IDLE
        self.websocket_server.broadcast_status_update("IDLE")

    def get_state(self) -> SystemState:
        """Get current system state."""
        return self.state

    def is_running(self) -> bool:
        """Check if the controller is running."""
        return self._running
