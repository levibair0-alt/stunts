"""
Command bus for routing intents to handlers with audit logging.
"""

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from .intent_parser import IntentType, ParsedIntent


class ExecutionStatus(Enum):
    """Execution status values."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    output: str
    error: Optional[str]
    duration_ms: int
    status: ExecutionStatus


class AuditLogger:
    """SQLite-based audit logging for voice commands."""

    def __init__(self, db_path: str = "voice_commands.db"):
        """
        Initialize audit logger.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS voice_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    raw_transcript TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    confidence REAL,
                    parameters TEXT,
                    execution_status TEXT,
                    execution_output TEXT,
                    execution_error TEXT,
                    duration_ms INTEGER,
                    triggered_engine TEXT
                )
            """
            )
            conn.commit()

    def log_command(
        self,
        transcript: str,
        intent: IntentType,
        confidence: float,
        parameters: dict[str, Any],
        status: ExecutionStatus,
        output: str = "",
        error: str = "",
        duration_ms: int = 0,
        triggered_engine: Optional[str] = None,
    ) -> int:
        """
        Log a voice command to the audit database.

        Args:
            transcript: Raw transcript text
            intent: Detected intent type
            confidence: Intent confidence score
            parameters: Command parameters as dict
            status: Execution status
            output: Command output
            error: Error message if any
            duration_ms: Execution duration in milliseconds
            triggered_engine: Name of triggered engine

        Returns:
            ID of the logged command
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO voice_commands
                (timestamp, raw_transcript, intent, confidence, parameters,
                 execution_status, execution_output, execution_error,
                 duration_ms, triggered_engine)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    transcript,
                    intent.value if hasattr(intent, 'value') else intent,
                    confidence,
                    json.dumps(parameters),
                    status.value if hasattr(status, 'value') else status,
                    output,
                    error,
                    duration_ms,
                    triggered_engine,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_commands(
        self, limit: int = 10, intent_filter: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get recent commands from audit log.

        Args:
            limit: Maximum number of commands to return
            intent_filter: Optional intent type filter

        Returns:
            List of command records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if intent_filter:
                cursor = conn.execute(
                    """
                    SELECT * FROM voice_commands
                    WHERE intent = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (intent_filter, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM voice_commands
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_command_stats(self) -> dict[str, Any]:
        """Get statistics about logged commands."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN execution_status = 'failure' THEN 1 ELSE 0 END) as failure_count,
                    SUM(CASE WHEN execution_status = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
                    AVG(confidence) as avg_confidence,
                    AVG(duration_ms) as avg_duration
                FROM voice_commands
            """
            )
            row = cursor.fetchone()
            return {
                "total_commands": row[0],
                "successful": row[1],
                "failed": row[2],
                "blocked": row[3],
                "avg_confidence": row[4] or 0.0,
                "avg_duration_ms": row[5] or 0.0,
            }


class CommandBus:
    """
    Routes commands to appropriate handlers with validation and logging.
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
        safe_mode_enabled: bool = True,
    ):
        """
        Initialize command bus.

        Args:
            audit_logger: Audit logger instance
            safe_mode_enabled: Whether SAFE_MODE is active
        """
        self.audit_logger = audit_logger
        self.safe_mode_enabled = safe_mode_enabled
        self._handlers: dict[IntentType, Callable[[ParsedIntent], CommandResult]] = {}
        self._middleware: list[Callable[[ParsedIntent], Optional[str]]] = []
        self._callbacks: list[Callable[[ParsedIntent, CommandResult], None]] = []

    def register_handler(
        self,
        intent_type: IntentType,
        handler: Callable[[ParsedIntent], CommandResult],
    ) -> None:
        """
        Register a handler for an intent type.

        Args:
            intent_type: Intent type to handle
            handler: Handler function that returns CommandResult
        """
        self._handlers[intent_type] = handler

    def register_middleware(
        self,
        middleware: Callable[[ParsedIntent], Optional[str]],
    ) -> None:
        """
        Register middleware for validation.

        Args:
            middleware: Function that returns error message or None
        """
        self._middleware.append(middleware)

    def register_callback(
        self,
        callback: Callable[[ParsedIntent, CommandResult], None],
    ) -> None:
        """
        Register a callback for command completion.

        Args:
            callback: Function called with (intent, result)
        """
        self._callbacks.append(callback)

    def dispatch(self, intent: ParsedIntent) -> CommandResult:
        """
        Dispatch an intent to the appropriate handler.

        Args:
            intent: Parsed intent to execute

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()

        # Run validation middleware
        for middleware in self._middleware:
            error = middleware(intent)
            if error:
                duration_ms = int((time.time() - start_time) * 1000)
                result = CommandResult(
                    success=False,
                    output="",
                    error=error,
                    duration_ms=duration_ms,
                    status=ExecutionStatus.BLOCKED,
                )
                self._log_and_notify(intent, result)
                return result

        # Find handler
        handler = self._handlers.get(intent.intent_type)
        if not handler:
            duration_ms = int((time.time() - start_time) * 1000)
            result = CommandResult(
                success=False,
                output="",
                error=f"No handler registered for intent type: {intent.intent_type}",
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )
            self._log_and_notify(intent, result)
            return result

        # Execute handler
        try:
            result = handler(intent)
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            result = CommandResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration_ms,
                status=ExecutionStatus.FAILURE,
            )

        # Log and notify
        self._log_and_notify(intent, result)

        return result

    def _log_and_notify(self, intent: ParsedIntent, result: CommandResult) -> None:
        """Log command and notify callbacks."""
        # Log to audit database
        self.audit_logger.log_command(
            transcript=intent.raw_transcript,
            intent=intent.intent_type,
            confidence=intent.confidence,
            parameters=intent.parameters,
            status=result.status,
            output=result.output,
            error=result.error or "",
            duration_ms=result.duration_ms,
            triggered_engine=intent.target_engine,
        )

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(intent, result)
            except Exception as e:
                print(f"Callback error: {e}")

    def get_handler_for_intent(
        self, intent_type: IntentType
    ) -> Optional[Callable[[ParsedIntent], CommandResult]]:
        """Get the handler for an intent type."""
        return self._handlers.get(intent_type)
