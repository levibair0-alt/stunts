"""Adapters package - Per-vendor bindings for LLM and platform integrations."""

from adapters.base import BaseAdapter, AdapterResult
from adapters.llm import (
    GPTAdapter,
    ClaudeAdapter,
    GrokAdapter,
    GeminiAdapter,
    NotebookLMAdapter,
)
from adapters.notion import NotionAdapter
from adapters.github import GitHubAdapter

__all__ = [
    "BaseAdapter",
    "AdapterResult",
    "GPTAdapter",
    "ClaudeAdapter",
    "GrokAdapter",
    "GeminiAdapter",
    "NotebookLMAdapter",
    "NotionAdapter",
    "GitHubAdapter",
]
