"""Sentry configuration for error tracking."""

import os
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration


def setup_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    release: Optional[str] = None,
    sample_rate: float = 1.0,
    traces_sample_rate: float = 0.1,
) -> Optional[sentry_sdk.Hub]:
    """
    Initialize Sentry for error tracking.
    
    Args:
        dsn: Sentry DSN URL. Reads from SENTRY_DSN env var if not provided.
        environment: Environment name (development, staging, production)
        release: Release version. Auto-detects from git if available.
        sample_rate: Error sampling rate (0.0 to 1.0)
        traces_sample_rate: Trace sampling rate for performance monitoring
        
    Returns:
        Sentry hub if initialized, None if no DSN provided
    """
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        return None

    # Auto-detect release from git
    if not release:
        try:
            import subprocess

            release = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--always"], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()
            )
        except Exception:
            release = "unknown"

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=25,  # WARNING level
        event_level=30,  # ERROR level
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        sample_rate=sample_rate,
        traces_sample_rate=traces_sample_rate,
        integrations=[
            logging_integration,
            ThreadingIntegration(propagate_original=True),
        ],
        # Attachments are disabled by default for privacy
        send_default_pii=False,
        # Disable default integrations we don't need
        default_integrations=False,
        # Include paths for better stack traces
        include_local_variables=True,
    )

    return sentry_sdk.hub


def get_sentry_middleware(app):
    """
    Get Sentry ASGI middleware for FastAPI/Starlette apps.
    
    Usage:
        app = FastAPI()
        app.add_middleware(get_sentry_middleware)
    """
    return SentryAsgiMiddleware(app)


def capture_exception(err: Exception, extra: Optional[dict] = None) -> None:
    """
    Capture an exception with optional extra context.
    
    Args:
        err: Exception to capture
        extra: Additional context to attach
    """
    if extra:
        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(err)
    else:
        sentry_sdk.capture_exception(err)


def capture_message(message: str, level: str = "info", extra: Optional[dict] = None) -> None:
    """
    Capture a message with optional extra context.
    
    Args:
        message: Message to capture
        level: Log level (debug, info, warning, error, critical)
        extra: Additional context to attach
    """
    if extra:
        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    else:
        sentry_sdk.capture_message(message, level=level)
