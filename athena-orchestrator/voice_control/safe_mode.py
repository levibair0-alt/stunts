"""
SAFE_MODE protection for dangerous command detection and confirmation.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""

    is_safe: bool
    is_dangerous: bool
    requires_confirmation: bool
    reason: Optional[str] = None
    confirmation_phrase: Optional[str] = None


class SafeModeGuard:
    """Protects against execution of dangerous commands."""

    # Default dangerous command patterns
    DEFAULT_PATTERNS = [
        (r"rm\s+-rf", "Mass deletion command detected"),
        (r"format\s+", "Disk formatting command detected"),
        (r"shutdown\s+-h\s+now", "System shutdown command detected"),
        (r"sudo.*rm", "Elevated deletion command detected"),
        (r"dd\s+if=.*of=/dev", "Direct disk write command detected"),
        (r"mkfs\.", "Filesystem creation command detected"),
        (r">\s*/dev/sd", "Disk device overwrite detected"),
        (r":\(\)\{\s*:\|:\|&\};:", "Fork bomb detected"),
        (r"chmod\s+-R\s+777\s+/", "Dangerous recursive permissions change"),
        (r"mv\s+.*\s+/dev/null", "File destruction via /dev/null"),
        (r"del\s+/[fFqQs]", "Windows mass deletion detected"),
        (r"rd\s+/s\s+/q", "Windows directory removal detected"),
        (r"format\s+[a-z]:\s+/[yYqQ]", "Windows format with force flag"),
    ]

    # High-risk keywords that require confirmation
    HIGH_RISK_KEYWORDS = [
        "delete",
        "remove",
        "drop",
        "truncate",
        "destroy",
        "kill",
        "terminate",
        "uninstall",
        "disable",
        "stop",
        "halt",
    ]

    def __init__(self, custom_patterns: Optional[list[str]] = None, enabled: bool = True):
        """
        Initialize safe mode guard.

        Args:
            custom_patterns: Additional dangerous patterns to check
            enabled: Whether safe mode is enabled
        """
        self.enabled = enabled
        self.patterns: list[tuple[re.Pattern, str]] = []

        # Compile default patterns
        for pattern, reason in self.DEFAULT_PATTERNS:
            self.patterns.append((re.compile(pattern, re.IGNORECASE), reason))

        # Add custom patterns
        if custom_patterns:
            for pattern in custom_patterns:
                self.patterns.append((re.compile(pattern, re.IGNORECASE), "Custom dangerous pattern"))

        self._pending_confirmation: Optional[str] = None
        self._pending_command: Optional[str] = None

    def check_command(
        self,
        command: str,
        command_type: str = "shell",
        transcript: Optional[str] = None,
    ) -> SafetyCheckResult:
        """
        Check if a command is safe to execute.

        Args:
            command: The command to check
            command_type: Type of command (shell, gui, api, engine)
            transcript: Original voice transcript for context

        Returns:
            SafetyCheckResult with safety status and confirmation requirements
        """
        if not self.enabled:
            return SafetyCheckResult(
                is_safe=True,
                is_dangerous=False,
                requires_confirmation=False,
            )

        # Check against dangerous patterns
        for pattern, reason in self.patterns:
            if pattern.search(command):
                return SafetyCheckResult(
                    is_safe=False,
                    is_dangerous=True,
                    requires_confirmation=True,
                    reason=reason,
                    confirmation_phrase=f"confirm {command}",
                )

        # Check for high-risk keywords in transcript
        if transcript:
            transcript_lower = transcript.lower()
            for keyword in self.HIGH_RISK_KEYWORDS:
                if keyword in transcript_lower:
                    return SafetyCheckResult(
                        is_safe=True,
                        is_dangerous=False,
                        requires_confirmation=True,
                        reason=f"High-risk keyword '{keyword}' detected",
                        confirmation_phrase=f"confirm {transcript}",
                    )

        return SafetyCheckResult(
            is_safe=True,
            is_dangerous=False,
            requires_confirmation=False,
        )

    def check_confirmation(self, transcript: str) -> tuple[bool, Optional[str]]:
        """
        Check if the transcript contains a confirmation.

        Args:
            transcript: The voice transcript to check

        Returns:
            Tuple of (confirmed, command)
        """
        transcript_lower = transcript.lower().strip()

        # Check for explicit confirmation phrases
        confirmation_phrases = [
            r"^confirm\s+(.+)$",
            r"^yes[,.]?\s+(.+)$",
            r"^yes[,.]?\s+confirm\s+(.+)$",
            r"^execute\s+(.+)$",
            r"^proceed\s+with\s+(.+)$",
            r"^do\s+it[,.]?\s+(.+)$",
        ]

        for pattern in confirmation_phrases:
            match = re.search(pattern, transcript_lower)
            if match:
                command = match.group(1).strip()
                return True, command

        # Simple "yes" confirmation if we have a pending command
        if self._pending_command and transcript_lower in ["yes", "confirm", "proceed", "execute"]:
            return True, self._pending_command

        return False, None

    def set_pending_confirmation(self, command: str) -> None:
        """Set a command awaiting confirmation."""
        self._pending_command = command

    def clear_pending_confirmation(self) -> None:
        """Clear any pending confirmation."""
        self._pending_command = None

    def has_pending_confirmation(self) -> bool:
        """Check if there's a command awaiting confirmation."""
        return self._pending_command is not None

    def get_pending_command(self) -> Optional[str]:
        """Get the command awaiting confirmation."""
        return self._pending_command
