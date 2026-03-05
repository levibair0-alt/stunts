"""Research Pipeline Example - Sample pipeline demonstrating multi-adapter flow."""

from typing import Any

from adapters.base import AdapterResult
from adapters.llm import GPTAdapter, ClaudeAdapter
from adapters.notion import NotionAdapter
from pipelines.base import Pipeline, Stage
from pipelines.registry import register_pipeline


@register_pipeline("research")
class ResearchPipeline(Pipeline):
    """
    Sample research pipeline that:
    1. Gathers information using GPT
    2. Analyzes findings with Claude
    3. Publishes results to Notion
    """

    name = "research"
    description = "Research pipeline: gather → analyze → publish"
    version = "1.0.0"

    def __init__(self):
        super().__init__()
        self.gpt_adapter = GPTAdapter()
        self.claude_adapter = ClaudeAdapter()
        self.notion_adapter = NotionAdapter()

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize all adapters."""
        await self.gpt_adapter.initialize(config.get("gpt", {}))
        await self.claude_adapter.initialize(config.get("claude", {}))
        await self.notion_adapter.initialize(config.get("notion", {}))

        # Define stages
        self.stages = [
            Stage(
                name="gather",
                adapter=self.gpt_adapter,
                config=config.get("gather", {}),
                depends_on=[],
            ),
            Stage(
                name="analyze",
                adapter=self.claude_adapter,
                config=config.get("analyze", {}),
                depends_on=["gather"],
                output_transform=self._analyze_transform,
            ),
            Stage(
                name="publish",
                adapter=self.notion_adapter,
                config=config.get("publish", {}),
                depends_on=["analyze"],
                input_transform=self._publish_transform,
            ),
        ]

    async def validate(self) -> bool:
        """Validate pipeline configuration."""
        return (
            self.gpt_adapter.is_initialized
            and self.claude_adapter.is_initialized
            and self.notion_adapter.is_initialized
        )

    def _analyze_transform(
        self, output: dict[str, Any], previous_results: dict[str, AdapterResult]
    ) -> dict[str, Any]:
        """Transform gather output for analyze stage."""
        gather_result = previous_results.get("gather")
        if not gather_result or not gather_result.data:
            return output

        # Extract content from gather stage
        messages = []
        if gather_result.data.get("choices"):
            content = gather_result.data["choices"][0]["message"]["content"]
            messages.append({"role": "user", "content": f"Analyze this: {content}"})

        return {"messages": messages, "operation": "analyze"}

    def _publish_transform(
        self, output: dict[str, Any], previous_results: dict[str, AdapterResult]
    ) -> dict[str, Any]:
        """Transform analyze output for publish stage."""
        analyze_result = previous_results.get("analyze")
        if not analyze_result or not analyze_result.data:
            return output

        # Extract analysis content
        content = ""
        if analyze_result.data.get("content"):
            for block in analyze_result.data["content"]:
                if block.get("type") == "text":
                    content += block.get("text", {}).get("content", "")

        return {
            "operation": "create_page",
            "properties": {
                "Name": {"title": [{"text": {"content": "Research Results"}}]}
            },
            "content": content,
        }
