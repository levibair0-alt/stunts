"""Tool Contract - Metadata definitions for adapters."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolType(str, Enum):
    """Type of tool/adapter."""

    LLM = "llm"
    NOTION = "notion"
    GITHUB = "github"
    CUSTOM = "custom"


class ToolCapabilities(BaseModel):
    """Capabilities of a tool adapter."""

    streaming: bool = Field(default=False, description="Supports streaming responses")
    function_calling: bool = Field(default=False, description="Supports function calling")
    vision: bool = Field(default=False, description="Supports vision/multimodal")
    tools: bool = Field(default=False, description="Supports tool use")
    batch: bool = Field(default=False, description="Supports batch processing")
    async_execution: bool = Field(default=True, description="Supports async execution")


class ToolContract(BaseModel):
    """
    Metadata contract for adapter tools.
    
    Describes the capabilities and configuration of an adapter.
    """

    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, description="Tool name")
    type: ToolType = Field(..., description="Tool type")
    vendor: str = Field(..., description="Vendor name")
    version: str = Field(default="1.0.0", description="Tool version")
    description: Optional[str] = Field(default=None, max_length=500)
    capabilities: ToolCapabilities = Field(default_factory=ToolCapabilities)
    config_schema: dict[str, Any] = Field(default_factory=dict, description="Configuration schema")
    env_vars: list[str] = Field(default_factory=list, description="Required environment variables")
    api_endpoint: Optional[str] = Field(default=None, description="API endpoint URL")
    documentation_url: Optional[str] = Field(default=None, description="Documentation URL")

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        # Basic validation - can be extended with JSON Schema
        required = self.config_schema.get("required", [])
        for key in required:
            if key not in config:
                return False
        return True

    def get_required_env_vars(self) -> list[str]:
        """Get list of required environment variables."""
        return self.env_vars
