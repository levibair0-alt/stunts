"""
Emergency Stop protocol for immediate system halt.
"""

import asyncio
import os
import signal
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EmergencyState(Enum):
    """Emergency stop states."""

    NORMAL = "normal"
    PENDING = "pending"
    ACTIVE = "active"
    RESUMING = "resuming"


@dataclass
class EmergencyStopResult:
    """Result of emergency stop activation."""

    success: bool
    processes_terminated: int
    audit_entry_id: Optional[int]
    message: str


class EmergencyStopProtocol:
    """
    Emergency Stop Protocol for Athena Command OS.

    Handles:
    - Voice-activated emergency stop
    - Process termination with grace period
    - Immutable audit logging
    - System freeze until resume
    - Visual feedback to Fractal View
    """

    # Emergency stop voice commands
    STOP_COMMANDS = [
        "emergency stop",
        "kill switch",
        "halt system",
        "stop all",
        "abort all",
        "system halt",
        "emergency shutdown",
        "athena emergency stop",
        "athena kill switch",
        "athena halt system",
    ]

    # Resume voice commands
    RESUME_COMMANDS = [
        "resume athena operations",
        "resume system",
        "continue operations",
        "start athena again",
        "resume athena",
        "athena resume",
        "resume operations",
        "system resume",
    ]

    def __init__(
        self,
        websocket_server: Optional[object] = None,
        audit_logger: Optional[object] = None,
        grace_period: float = 0.5,
    ):
        """
        Initialize emergency stop protocol.

        Args:
            websocket_server: WebSocket server for broadcasting alerts
            audit_logger: Audit logger for emergency events
            grace_period: Seconds to wait before SIGKILL after SIGTERM
        """
        self.websocket_server = websocket_server
        self.audit_logger = audit_logger
        self.grace_period = grace_period
        self.state = EmergencyState.NORMAL
        self._active_processes: set[int] = set()
        self._emergency_start_time: Optional[float] = None
        self._frozen = False

    def check_emergency_command(self, transcript: str) -> tuple[bool, str]:
        """
        Check if transcript contains an emergency stop command.

        Args:
            transcript: Voice transcript to check

        Returns:
            Tuple of (is_emergency, command_type)
            command_type is 'stop', 'resume', or 'none'
        """
        transcript_lower = transcript.lower().strip()

        for cmd in self.STOP_COMMANDS:
            if cmd in transcript_lower:
                return True, "stop"

        for cmd in self.RESUME_COMMANDS:
            if cmd in transcript_lower:
                return True, "resume"

        return False, "none"

    async def activate(self, transcript: str = "") -> EmergencyStopResult:
        """
        Activate emergency stop protocol.

        Args:
            transcript: The voice command that triggered the stop

        Returns:
            EmergencyStopResult with activation details
        """
        if self.state == EmergencyState.ACTIVE:
            return EmergencyStopResult(
                success=True,
                processes_terminated=0,
                audit_entry_id=None,
                message="Emergency stop already active",
            )

        print("\n🚨 EMERGENCY STOP ACTIVATED 🚨")
        self.state = EmergencyState.PENDING
        self._emergency_start_time = time.time()

        # 1. Broadcast RED ALERT to all Fractal View nodes
        if self.websocket_server:
            self.websocket_server.broadcast_emergency_alert(
                "EMERGENCY STOP ACTIVATED - SYSTEM HALTING"
            )

        # 2. Terminate all active subprocesses
        processes_terminated = await self._terminate_all_processes()

        # 3. Write immutable audit entry
        audit_entry_id = None
        if self.audit_logger:
            audit_entry_id = self.audit_logger.log_command(
                transcript=transcript or "Emergency stop activated",
                intent_type="EMERGENCY_STOP",
                confidence=1.0,
                parameters={"trigger": "voice_command", "transcript": transcript},
                status="blocked",
                output="EMERGENCY STOP ACTIVATED",
                triggered_engine=None,
            )

        # 4. Freeze system
        self.state = EmergencyState.ACTIVE
        self._frozen = True

        # 5. Broadcast visual feedback (all nodes flash RED)
        if self.websocket_server:
            self.websocket_server.broadcast_system_message(
                "SYSTEM HALTED - All engines stopped",
                level="critical",
            )

        return EmergencyStopResult(
            success=True,
            processes_terminated=processes_terminated,
            audit_entry_id=audit_entry_id,
            message="Emergency stop activated. System frozen. Say 'resume Athena operations' to continue.",
        )

    async def resume(self, transcript: str = "") -> bool:
        """
        Resume operations after emergency stop.

        Args:
            transcript: The voice command that triggered resume

        Returns:
            True if successfully resumed
        """
        if self.state != EmergencyState.ACTIVE:
            return False

        print("\n🟢 RESUMING ATHENA OPERATIONS")

        self.state = EmergencyState.RESUMING

        # Clear frozen state
        self._frozen = False

        # Log resume event
        if self.audit_logger:
            self.audit_logger.log_command(
                transcript=transcript or "Resume operations",
                intent_type="RESUME",
                confidence=1.0,
                parameters={"trigger": "voice_command", "transcript": transcript},
                status="success",
                output="System resumed from emergency stop",
                triggered_engine=None,
            )

        # Broadcast resume status
        if self.websocket_server:
            self.websocket_server.broadcast_system_message(
                "System resumed - Operations continuing",
                level="info",
            )
            self.websocket_server.broadcast_status_update("IDLE")

        self.state = EmergencyState.NORMAL
        print("✅ System operations resumed")

        return True

    async def _terminate_all_processes(self) -> int:
        """
        Terminate all active subprocesses.

        Returns:
            Number of processes terminated
        """
        terminated_count = 0

        # Get list of processes to terminate
        processes_to_kill = list(self._active_processes)

        for pid in processes_to_kill:
            try:
                # Send SIGTERM first
                os.kill(pid, signal.SIGTERM)
                terminated_count += 1
            except ProcessLookupError:
                # Process already gone
                pass
            except Exception as e:
                print(f"Error terminating process {pid}: {e}")

        # Wait grace period
        await asyncio.sleep(self.grace_period)

        # Send SIGKILL to remaining processes
        for pid in processes_to_kill:
            try:
                # Check if process still exists
                os.kill(pid, 0)  # Signal 0 tests if process exists
                # Process still alive, send SIGKILL
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                # Process already gone
                pass
            except Exception as e:
                print(f"Error force-killing process {pid}: {e}")

        # Clear process list
        self._active_processes.clear()

        return terminated_count

    def register_process(self, pid: int) -> None:
        """Register a process for monitoring."""
        self._active_processes.add(pid)

    def unregister_process(self, pid: int) -> None:
        """Unregister a monitored process."""
        self._active_processes.discard(pid)

    def is_frozen(self) -> bool:
        """Check if the system is currently frozen."""
        return self._frozen

    def get_state(self) -> EmergencyState:
        """Get current emergency state."""
        return self.state

    def get_elapsed_time(self) -> Optional[float]:
        """
        Get elapsed time since emergency stop was activated.

        Returns:
            Seconds since activation, or None if not active
        """
        if self._emergency_start_time is None:
            return None
        return time.time() - self._emergency_start_time
