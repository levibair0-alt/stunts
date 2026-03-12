"""Grok Adapter - xAI Grok integration."""

import os
from typing import Any, Optional

from openai import AsyncOpenAI

from adapters.base import BaseAdapter, AdapterResult
from contracts.tool_contract import ToolContract, ToolType, ToolCapabilities


class GrokAdapter(BaseAdapter):
    """xAI Grok adapter with chat completion and streaming."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AsyncOpenAI] = None

    @property
    def tool_contract(self) -> ToolContract:
        return ToolContract(
            name="grok",
            type=ToolType.LLM,
            vendor="xAI",
            version="1.0.0",
            description="xAI Grok chat completion with streaming support",
            capabilities=ToolCapabilities(
                streaming=True,
                function_calling=True,
                vision=False,
                tools=True,
                batch=False,
                async_execution=True,
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "default": "grok-2"},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
                    "max_tokens": {"type": "integer", "minimum": 1, "maximum": 131072", "default": 4096},
                },
                "required": [],
            },
            env_vars=["XAI_API_KEY"],
            api_endpoint="https://api.x.ai/v1",
            documentation_url="https://docs.x.ai",
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        api_key = config.get("api_key") or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError("XAI_API_KEY is required")

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
            timeout=config.get("timeout", 60),
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
            model = self._config.get("model", "grok-2")
            temperature = self._config.get("temperature", 0.7)
            max_tokens = self._config.get("max_tokens", 4096)
            tools = input_data.get("tools")
            stream = input_data.get("stream", False)

            if stream:
                return await self._execute_stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )

            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )

            return AdapterResult(
                success=True,
                data={
                    "id": response.id,
                    "model": response.model,
                    "choices": [
                        {
                            "message": choice.message.model_dump(),
                            "finish_reason": choice.finish_reason,
                        }
                        for choice in response.choices
                    ],
                    "usage": response.usage.model_dump() if response.usage else None,
                },
                metadata={
                    "provider": "xai",
                    "model": model,
                },
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def _execute_stream(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[list],
    ) -> AdapterResult:
        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                stream=True,
            )

            chunks = []
            async for chunk in stream:
                chunks.append(chunk)

            return AdapterResult(
                success=True,
                data={
                    "chunks": [
                        {
                            "id": c.id,
                            "choices": [
                                {
                                    "delta": choice.delta.model_dump(),
                                    "finish_reason": choice.finish_reason,
                                }
                                for choice in c.choices
                            ],
                        }
                        for c in chunks
                    ]
                },
                metadata={"provider": "xai", "stream": True},
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.chat.completions.create(
                model=self._config.get("model", "grok-2"),
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
