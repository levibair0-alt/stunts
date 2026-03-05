"""GPT Adapter - OpenAI GPT integration."""

import os
from typing import Any, AsyncIterator, Optional

from openai import AsyncOpenAI

from adapters.base import BaseAdapter, AdapterResult
from contracts.tool_contract import ToolContract, ToolType, ToolCapabilities


class GPTAdapter(BaseAdapter):
    """OpenAI GPT adapter with chat completion, streaming, and function calling."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AsyncOpenAI] = None

    @property
    def tool_contract(self) -> ToolContract:
        return ToolContract(
            name="gpt",
            type=ToolType.LLM,
            vendor="OpenAI",
            version="1.0.0",
            description="OpenAI GPT chat completion with streaming and function calling",
            capabilities=ToolCapabilities(
                streaming=True,
                function_calling=True,
                vision=False,
                tools=True,
                batch=True,
                async_execution=True,
            ),
            config_schema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "default": "gpt-4o"},
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7},
                    "max_tokens": {"type": "integer", "minimum": 1, "maximum": 128000, "default": 4096},
                },
                "required": [],
            },
            env_vars=["OPENAI_API_KEY"],
            api_endpoint="https://api.openai.com/v1",
            documentation_url="https://platform.openai.com/docs",
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.get("base_url"),
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
            model = self._config.get("model", "gpt-4o")
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
                    "provider": "openai",
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
                metadata={"provider": "openai", "stream": True},
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            # Simple health check - try a minimal request
            await self._client.chat.completions.create(
                model=self._config.get("model", "gpt-4o"),
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
