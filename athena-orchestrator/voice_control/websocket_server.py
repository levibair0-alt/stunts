"""
WebSocket server for real-time broadcasting to Fractal Engine View.
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    websockets = None
    WebSocketServerProtocol = None


class BroadcastType(Enum):
    """Types of broadcast messages."""

    INTENT_DETECTED = "intent_detected"
    STATUS_UPDATE = "status_update"
    ENGINE_TRIGGERED = "engine_triggered"
    EXECUTION_RESULT = "execution_result"
    EMERGENCY_ALERT = "emergency_alert"
    SYSTEM_MESSAGE = "system_message"


@dataclass
class BroadcastMessage:
    """Message structure for WebSocket broadcasts."""

    type: str
    payload: dict[str, Any]
    timestamp: str

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(
            {
                "type": self.type,
                "payload": self.payload,
                "timestamp": self.timestamp,
            }
        )


class VoiceWebSocketServer:
    """
    WebSocket server for broadcasting voice control events to Fractal View.
    Port: 8766 (Voice Control Bus)
    """

    def __init__(self, host: str = "localhost", port: int = 8766):
        """
        Initialize WebSocket server.

        Args:
            host: Server host address
            port: Server port
        """
        self.host = host
        self.port = port
        self._clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._running = False
        self._fallback_mode = not HAS_WEBSOCKETS

        if self._fallback_mode:
            print("⚠️  websockets not installed - running in fallback mode (console output only)")

    async def start(self) -> None:
        """Start the WebSocket server."""
        if self._fallback_mode:
            self._running = True
            print(f"🔌 WebSocket server (fallback mode) on port {self.port}")
            return

        if websockets is None:
            raise RuntimeError("websockets library not installed")

        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
        )
        self._running = True
        print(f"🔌 WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self._fallback_mode:
            self._running = False
            print("🔌 WebSocket server stopped")
            return

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        # Close all client connections
        for client in self._clients.copy():
            await client.close()

        self._running = False
        print("🔌 WebSocket server stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle a new client connection."""
        if self._fallback_mode or websockets is None:
            return

        self._clients.add(websocket)
        print(f"🔌 Client connected. Total clients: {len(self._clients)}")

        try:
            await self._broadcast(
                BroadcastType.STATUS_UPDATE.value,
                {"status": "CONNECTED", "client_count": len(self._clients)},
            )

            # Keep connection alive and handle incoming messages
            async for message in websocket:
                await self._handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            print(f"🔌 Client disconnected. Total clients: {len(self._clients)}")

    async def _handle_message(
        self, websocket: WebSocketServerProtocol, message: str
    ) -> None:
        """Handle incoming message from client."""
        if self._fallback_mode:
            return

        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            elif msg_type == "subscribe":
                # Client can subscribe to specific events
                pass

        except json.JSONDecodeError:
            print(f"Invalid message received: {message}")

    async def _broadcast(self, msg_type: str, payload: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        from datetime import datetime

        message = BroadcastMessage(
            type=msg_type,
            payload=payload,
            timestamp=datetime.now().isoformat(),
        )

        # In fallback mode, just print to console
        if self._fallback_mode:
            print(f"📡 [{msg_type}] {payload}")
            return

        if not self._clients or websockets is None:
            return

        json_message = message.to_json()

        # Send to all connected clients
        disconnected = set()
        for client in self._clients:
            try:
                await client.send(json_message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        self._clients -= disconnected

    def broadcast_intent_detected(
        self,
        intent: str,
        confidence: float,
        raw_transcript: str,
        engine: Optional[str] = None,
    ) -> None:
        """
        Broadcast intent detection event.

        Args:
            intent: Detected intent type
            confidence: Confidence score
            raw_transcript: Original transcript
            engine: Target engine name
        """
        asyncio.create_task(
            self._broadcast(
                BroadcastType.INTENT_DETECTED.value,
                {
                    "intent": intent,
                    "confidence": round(confidence, 3),
                    "raw_transcript": raw_transcript,
                    "engine": engine,
                },
            )
        )

    def broadcast_status_update(self, status: str) -> None:
        """
        Broadcast status update.

        Args:
            status: Current system status (LISTENING, PROCESSING, EXECUTING, IDLE)
        """
        asyncio.create_task(
            self._broadcast(
                BroadcastType.STATUS_UPDATE.value,
                {"status": status},
            )
        )

    def broadcast_engine_triggered(self, engine: str, action: str) -> None:
        """
        Broadcast engine trigger event.

        Args:
            engine: Engine name (Sensor, Validator, Generator, Monetizer, Auditor)
            action: Action being performed
        """
        asyncio.create_task(
            self._broadcast(
                BroadcastType.ENGINE_TRIGGERED.value,
                {
                    "engine": engine,
                    "action": action,
                },
            )
        )

    def broadcast_execution_result(
        self,
        success: bool,
        output: str,
        duration_ms: int,
        engine: Optional[str] = None,
    ) -> None:
        """
        Broadcast command execution result.

        Args:
            success: Whether execution was successful
            output: Command output
            duration_ms: Execution duration in milliseconds
            engine: Engine that processed the command
        """
        asyncio.create_task(
            self._broadcast(
                BroadcastType.EXECUTION_RESULT.value,
                {
                    "success": success,
                    "output": output[:500],  # Limit output length
                    "duration_ms": duration_ms,
                    "engine": engine,
                },
            )
        )

    def broadcast_emergency_alert(self, message: str = "EMERGENCY STOP ACTIVATED") -> None:
        """
        Broadcast emergency alert to all clients.

        Args:
            message: Alert message
        """
        asyncio.create_task(
            self._broadcast(
                BroadcastType.EMERGENCY_ALERT.value,
                {
                    "level": "CRITICAL",
                    "message": message,
                    "action": "HALT_ALL_ENGINES",
                },
            )
        )

    def broadcast_system_message(self, message: str, level: str = "info") -> None:
        """
        Broadcast a system message.

        Args:
            message: Message text
            level: Message level (info, warning, error)
        """
        asyncio.create_task(
            self._broadcast(
                BroadcastType.SYSTEM_MESSAGE.value,
                {
                    "level": level,
                    "message": message,
                },
            )
        )

    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running

    def get_client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self._clients)
