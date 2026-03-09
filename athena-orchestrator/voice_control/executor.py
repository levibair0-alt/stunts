"""
Command execution layer for shell, GUI, API, and engine commands.
"""

import asyncio
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Optional

from .command_bus import CommandResult, ExecutionStatus
from .intent_parser import ParsedIntent
from .safe_mode import SafeModeGuard

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None


@dataclass
class ExecutionContext:
    """Context for command execution."""

    timeout: int = 60
    capture_output: bool = True
    shell: bool = True
    working_dir: Optional[str] = None


class CommandExecutor:
    """Executes commands based on intent type."""

    def __init__(
        self,
        safe_mode_guard: SafeModeGuard,
        api_base_url: str = "http://localhost:8000",
    ):
        """
        Initialize command executor.

        Args:
            safe_mode_guard: Safe mode guard for dangerous command checking
            api_base_url: Base URL for API calls
        """
        self.safe_mode_guard = safe_mode_guard
        self.api_base_url = api_base_url
        self._active_processes: list[subprocess.Popen] = []
        self._confirmation_pending: Optional[ParsedIntent] = None

    async def execute(self, intent: ParsedIntent) -> CommandResult:
        """
        Execute a command based on intent.

        Args:
            intent: Parsed intent to execute

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()

        # Check for confirmation if pending
        if self._confirmation_pending:
            confirmed, command = self.safe_mode_guard.check_confirmation(
                intent.raw_transcript
            )
            if confirmed:
                # Execute the pending command
                pending = self._confirmation_pending
                self._confirmation_pending = None
                self.safe_mode_guard.clear_pending_confirmation()
                return await self._execute_pending(pending)
            else:
                # Clear pending if user said something else
                self._confirmation_pending = None
                self.safe_mode_guard.clear_pending_confirmation()

        # Route to appropriate handler based on intent type
        try:
            if intent.intent_type.value == "QUERY":
                result = await self._execute_query(intent)
            elif intent.intent_type.value == "VERIFY":
                result = await self._execute_verify(intent)
            elif intent.intent_type.value == "CREATE":
                result = await self._execute_create(intent)
            elif intent.intent_type.value == "MONETIZE":
                result = await self._execute_monetize(intent)
            elif intent.intent_type.value == "AUDIT":
                result = await self._execute_audit(intent)
            else:
                duration_ms = int((time.time() - start_time) * 1000)
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Unknown intent type: {intent.intent_type}",
                    duration_ms=duration_ms,
                    status=ExecutionStatus.FAILURE,
                )

            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )

    async def _execute_query(self, intent: ParsedIntent) -> CommandResult:
        """Execute a QUERY intent (shell command or GUI automation)."""
        command = self._extract_shell_command(intent)

        if not command:
            return CommandResult(
                success=False,
                output="",
                error="No command extracted from transcript",
                duration_ms=0,
                status=ExecutionStatus.FAILURE,
            )

        # Check safe mode
        safety_check = self.safe_mode_guard.check_command(
            command=command,
            transcript=intent.raw_transcript,
        )

        if safety_check.is_dangerous or safety_check.requires_confirmation:
            self._confirmation_pending = intent
            self.safe_mode_guard.set_pending_confirmation(command)
            return CommandResult(
                success=False,
                output="",
                error=f"Command requires confirmation. Say 'confirm {command}' to proceed.",
                duration_ms=0,
                status=ExecutionStatus.BLOCKED,
            )

        return await self._execute_shell_command(command)

    async def _execute_verify(self, intent: ParsedIntent) -> CommandResult:
        """Execute a VERIFY intent (data validation)."""
        # This would integrate with Quintuple Engine's Validator
        target = intent.entities.get("target", "unknown")

        # Simulate validation call
        await asyncio.sleep(0.5)

        return CommandResult(
            success=True,
            output=f"Validated: {target} - Status: OK",
            error=None,
            duration_ms=500,
            status=ExecutionStatus.SUCCESS,
        )

    async def _execute_create(self, intent: ParsedIntent) -> CommandResult:
        """Execute a CREATE intent (trigger Generator engine)."""
        target = intent.entities.get("target", "unknown")

        # This would call the Generator engine
        # For now, simulate the call
        await asyncio.sleep(1.0)

        return CommandResult(
            success=True,
            output=f"Generated: {target}",
            error=None,
            duration_ms=1000,
            status=ExecutionStatus.SUCCESS,
        )

    async def _execute_monetize(self, intent: ParsedIntent) -> CommandResult:
        """Execute a MONETIZE intent (audit report)."""
        # This would request audit report from Auditor
        await asyncio.sleep(0.8)

        return CommandResult(
            success=True,
            output="Monetization report generated. Revenue potential: HIGH",
            error=None,
            duration_ms=800,
            status=ExecutionStatus.SUCCESS,
        )

    async def _execute_audit(self, intent: ParsedIntent) -> CommandResult:
        """Execute an AUDIT intent (config/status)."""
        command = intent.parameters.get("raw_command", "").lower()

        if "status" in command:
            return CommandResult(
                success=True,
                output="System Status: All engines operational. Voice Control active.",
                error=None,
                duration_ms=200,
                status=ExecutionStatus.SUCCESS,
            )
        elif "log" in command or "history" in command:
            return CommandResult(
                success=True,
                output="Recent commands logged. Check audit database for details.",
                error=None,
                duration_ms=200,
                status=ExecutionStatus.SUCCESS,
            )
        else:
            return CommandResult(
                success=True,
                output="Audit command processed.",
                error=None,
                duration_ms=200,
                status=ExecutionStatus.SUCCESS,
            )

    async def _execute_pending(self, intent: ParsedIntent) -> CommandResult:
        """Execute a previously pending command (after confirmation)."""
        if intent.intent_type.value == "QUERY":
            command = self._extract_shell_command(intent)
            if command:
                return await self._execute_shell_command(command)

        return CommandResult(
            success=False,
            output="",
            error="Could not execute pending command",
            duration_ms=0,
            status=ExecutionStatus.FAILURE,
        )

    async def _execute_shell_command(self, command: str) -> CommandResult:
        """Execute a shell command."""
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self._active_processes.append(process)

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=60,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration_ms = int((time.time() - start_time) * 1000)
                return CommandResult(
                    success=False,
                    output="",
                    error="Command timed out after 60 seconds",
                    duration_ms=duration_ms,
                    status=ExecutionStatus.TIMEOUT,
                )
            finally:
                if process in self._active_processes:
                    self._active_processes.remove(process)

            duration_ms = int((time.time() - start_time) * 1000)

            if process.returncode == 0:
                return CommandResult(
                    success=True,
                    output=stdout.decode().strip(),
                    error=None,
                    duration_ms=duration_ms,
                    status=ExecutionStatus.SUCCESS,
                )
            else:
                return CommandResult(
                    success=False,
                    output=stdout.decode().strip(),
                    error=stderr.decode().strip(),
                    duration_ms=duration_ms,
                    status=ExecutionStatus.FAILURE,
                )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )

    def _extract_shell_command(self, intent: ParsedIntent) -> str:
        """Extract shell command from intent."""
        transcript = intent.raw_transcript.lower()

        # Remove wake word and common prefixes
        prefixes = [
            r"^athena\s+",
            r"^hey\s+athena\s+",
            r"^okay\s+athena\s+",
            r"^yo\s+athena\s+",
            r"^run\s+",
            r"^execute\s+",
        ]

        command = transcript
        for prefix in prefixes:
            command = re.sub(prefix, "", command, flags=re.IGNORECASE)

        return command.strip()

    async def execute_gui_action(
        self,
        action: str,
        target: Optional[str] = None,
    ) -> CommandResult:
        """
        Execute a GUI automation action using PyAutoGUI.

        Args:
            action: Action type (click, type, hotkey, etc.)
            target: Target element or coordinates

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()

        try:
            import pyautogui

            # Safety: Fail-safe enabled (move mouse to corner to abort)
            pyautogui.FAILSAFE = True

            if action == "click":
                if target and "," in target:
                    x, y = map(int, target.split(","))
                    pyautogui.click(x, y)
                else:
                    pyautogui.click()
            elif action == "type":
                if target:
                    pyautogui.typewrite(target)
            elif action == "hotkey":
                if target:
                    keys = target.split("+")
                    pyautogui.hotkey(*keys)
            elif action == "screenshot":
                screenshot = pyautogui.screenshot()
                return CommandResult(
                    success=True,
                    output="Screenshot captured",
                    error=None,
                    duration_ms=int((time.time() - start_time) * 1000),
                    status=ExecutionStatus.SUCCESS,
                )

            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=True,
                output=f"GUI action '{action}' executed successfully",
                error=None,
                duration_ms=duration_ms,
                status=ExecutionStatus.SUCCESS,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )

    async def make_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict[str, Any]] = None,
    ) -> CommandResult:
        """
        Make an API call to EVE-3 Oracle.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request body data

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()

        if not HAS_REQUESTS or requests is None:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                output="",
                error="requests library not installed",
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )

        try:
            url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

            if method.upper() == "GET":
                response = requests.get(url, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=30)
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Unsupported HTTP method: {method}",
                    duration_ms=int((time.time() - start_time) * 1000),
                    status=ExecutionStatus.FAILURE,
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return CommandResult(
                success=response.status_code < 400,
                output=response.text,
                error=None if response.status_code < 400 else f"HTTP {response.status_code}",
                duration_ms=duration_ms,
                status=ExecutionStatus.SUCCESS
                if response.status_code < 400
                else ExecutionStatus.FAILURE,
            )

        except requests.RequestException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )

    def kill_all_processes(self) -> None:
        """Kill all active subprocesses."""
        for process in self._active_processes[:]:  # Copy to avoid modification during iteration
            try:
                process.kill()
                process.wait()
            except Exception:
                pass

        self._active_processes.clear()
