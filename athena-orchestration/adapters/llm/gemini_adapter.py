"""Gemini Adapter - Google Gemini integration."""

import os
from typing import Any, Optional

from google.genai import AsyncClient
from google.genai.types import GenerateContentConfig, Part

from adapters.base import BaseAdapter, AdapterResult
from contracts.tool_contract import ToolContract, ToolType, ToolCapabilities


class GeminiAdapter(BaseAdapter):
    """Google Gemini adapter with multimodal and grounded generation support."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AsyncClient] = None

    @property
    def tool_contract(self) -> ToolContract:
        return ToolContract(
            name="gemini",
            type=ToolType.LLM,
            vendor="Google",
            version="1.0.0",
            description="Google Gemini with multimodal and grounded generation",
            capabilities=ToolCapabilities(
                streaming=True,
                function_calling=True,
                vision=True,
                tools=True,
                batch=True,
                async_execution=True,
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "default": "gemini-2.0-flash"},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
                    "max_output_tokens": {"type": "integer", "minimum": 1, "maximum": 8192", "default": 4096},
                    "google_api_key": {"type": "string"},
                },
                "required": [],
            },
            env_vars=["GOOGLE_API_KEY"],
            api_endpoint="https://generativelanguage.googleapis.com",
            documentation_url="https://ai.google.dev/docs",
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        api_key = config.get("api_key") or config.get("google_api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        self._client = AsyncClient(api_key=api_key)
        await super().initialize(config)

    async def execute(self, input_data: dict[str, Any]) -> AdapterResult:
        if not self._initialized or not self._client:
            return AdapterResult(
                success=False,
                error="Adapter not initialized. Call initialize() first.",
            )

        try:
            messages = input_data.get("messages", [])
            model = self._config.get("model", "gemini-2.0-flash")
            temperature = self._config.get("temperature", 0.7)
            max_output_tokens = self._config.get("max_output_tokens", 4096)
            stream = input_data.get("stream", False)

            # Convert messages to Gemini format
            contents = self._convert_messages(messages)

            config = GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

            if stream:
                return await self._execute_stream(
                    contents=contents,
                    model=model,
                    config=config,
                )

            response = await self._client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            return AdapterResult(
                success=True,
                data={
                    "model": model,
                    "content": [c.model_dump() for c in response.candidates],
                    "usage_metadata": response.usage_metadata.model_dump()
                    if response.usage_metadata
                    else None,
                },
                metadata={
                    "provider": "google",
                    "model": model,
                },
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    def _convert_messages(self, messages: list[dict]) -> list:
        """Convert messages to Gemini format."""
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Handle different content formats
            if isinstance(content, str):
                contents.append({"role": role, "parts": [{"text": content}]})
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, str):
                        parts.append({"text": part})
                    elif isinstance(part, dict):
                        if part.get("type") == "image_url":
                            # Handle image URLs
                            parts.append(
                                {"inline_data": {"mime_type": "image/jpeg", "data": part.get("url", "")}}
                            )
                        else:
                            parts.append(part)
                contents.append({"role": role, "parts": parts})
        return contents

    async def _execute_stream(
        self,
        contents: list,
        model: str,
        config: GenerateContentConfig,
    ) -> AdapterResult:
        try:
            stream = await self._client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )

            chunks = []
            async for chunk in stream:
                chunks.append(chunk)

            return AdapterResult(
                success=True,
                data={
                    "chunks": [c.model_dump() for c in chunks],
                },
                metadata={"provider": "google", "stream": True},
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            response = await self._client.aio.models.generate_content(
                model=self._config.get("model", "gemini-2.0-flash"),
                contents=[{"role": "user", "parts": [{"text": "hi"}]}],
                config=GenerateContentConfig(max_output_tokens=10),
            )
            return response is not None
        except Exception:
            return False
