"""Claude Adapter - Anthropic Claude integration."""

import os
from typing import Any, AsyncIterator, Optional

from anthropic import AsyncAnthropic

from adapters.base import BaseAdapter, AdapterResult
from contracts.tool_contract import ToolContract, ToolType, ToolCapabilities


class ClaudeAdapter(BaseAdapter):
    """Anthropic Claude adapter with tools, vision, and extended context."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AsyncAnthropic] = None

    @property
    def tool_contract(self) -> ToolContract:
        return ToolContract(
            name="claude",
            type=ToolType.LLM,
            vendor="Anthropic",
            version="1.0.0",
            description="Anthropic Claude with tools, vision, and extended context support",
            capabilities=ToolCapabilities(
                streaming=True,
                function_calling=False,  # Uses tools instead
                vision=True,
                tools=True,
                batch=True,
                async_execution=True,
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "default": "claude-sonnet-4-20250514"},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.7},
                    "max_tokens": {"type": "integer", "minimum": 1, "maximum": 200000", "default": 4096},
                },
                "required": [],
            },
            env_vars=["ANTHROPIC_API_KEY"],
            api_endpoint="https://api.anthropic.com",
            documentation_url="https://docs.anthropic.com/en/docs",
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        self._client = AsyncAnthropic(
            api_key=api_key,
            timeout=config.get("timeout", 60),
            max_retries=config.get("max_retries", 3),
        )
        await super().initialize(config)

    async def execute(self, input_data: dict[str, Any]) -> AdapterResult:
        if not self._initialized or not self._client:
            return AdapterResult(
                success=False,
                error="Adapter not initialized. Call initialize() first.",
            )

        try:
            messages = input_data.get("messages", [])
            model = self._config.get("model", "claude-sonnet-4-20250514")
            temperature = self._config.get("temperature", 0.7)
            max_tokens = input_data.get("max_tokens", self._config.get("max_tokens", 4096))
            tools = input_data.get("tools")
            stream = input_data.get("stream", False)

            # Convert messages to Anthropic format
            anthropic_messages = self._convert_messages(messages)

            extra_params = {}
            if tools:
                extra_params["tools"] = tools

            if stream:
                return await self._execute_stream(
                    messages=anthropic_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **extra_params,
                )

            response = await self._client.messages.create(
                model=model,
                messages=anthropic_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )

            return AdapterResult(
                success=True,
                data={
                    "id": response.id,
                    "model": response.model,
                    "content": [block.model_dump() for block in response.content],
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    "stop_reason": response.stop_reason,
                },
                metadata={
                    "provider": "anthropic",
                    "model": model,
                },
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert OpenAI-style messages to Anthropic format."""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                # Anthropic uses system prompt differently
                converted.append({"role": "user", "content": f"SYSTEM: {msg.get('content', '')}"})
            else:
                converted.append(msg)
        return converted

    async def _execute_stream(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> AdapterResult:
        try:
            stream = await self._client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            chunks = []
            async for chunk in stream:
                chunks.append(chunk)

            return AdapterResult(
                success=True,
                data={
                    "chunks": [
                        {
                            "type": c.type,
                            "delta": c.delta.model_dump() if hasattr(c, "delta") else None,
                        }
                        for c in chunks
                    ]
                },
                metadata={"provider": "anthropic", "stream": True},
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.messages.create(
                model=self._config.get("model", "claude-sonnet-4-20250514"),
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10,
            )
            return True
        except Exception:
            return False
