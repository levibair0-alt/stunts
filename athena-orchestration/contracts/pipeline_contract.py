"""Pipeline Contract - Stable Intermediate Representation for pipelines."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from contracts.task_contract import TaskContract


class StageStatus(str, Enum):
    """Stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageContract(BaseModel):
    """
    Represents a single stage in a pipeline.
    
    Each stage has a name, adapter configuration, and optional
    before/after hooks for transformation.
    """

    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, description="Stage name")
    adapter_name: str = Field(..., description="Name of adapter to use")
    adapter_config: dict[str, Any] = Field(default_factory=dict, description="Adapter configuration")
    input_transform: Optional[dict[str, Any]] = Field(default=None, description="Input transformation")
    output_transform: Optional[dict[str, Any]] = Field(default=None, description="Output transformation")
    depends_on: list[str] = Field(default_factory=list, description="Stage dependencies")
    status: StageStatus = Field(default=StageStatus.PENDING, description="Stage status")
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def mark_running(self) -> None:
        """Mark stage as running."""
        self.status = StageStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark stage as completed."""
        self.status = StageStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark stage as failed."""
        self.status = StageStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()

    def mark_skipped(self) -> None:
        """Mark stage as skipped."""
        self.status = StageStatus.SKIPPED
        self.completed_at = datetime.utcnow()


class PipelineContract(BaseModel):
    """
    Stable Intermediate Representation for a pipeline.
    
    A pipeline is a directed acyclic graph of stages that transform
    input data through a series of adapters.
    """

    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique pipeline identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Pipeline name")
    description: Optional[str] = Field(default=None, max_length=500)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    stages: list[StageContract] = Field(default_factory=list, description="Pipeline stages")
    input_schema: dict[str, Any] = Field(default_factory=dict, description="Input JSON schema")
    output_schema: dict[str, Any] = Field(default_factory=dict, description="Output JSON schema")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Pipeline metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_stage(self, name: str) -> Optional[StageContract]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def validate_dependencies(self) -> bool:
        """Validate that all stage dependencies exist."""
        stage_names = {stage.name for stage in self.stages}
        for stage in self.stages:
            for dep in stage.depends_on:
                if dep not in stage_names:
                    return False
        return True

    def get_execution_order(self) -> list[str]:
        """
        Get stages in topological order for execution.
        
        Returns list of stage names in the order they should be executed.
        """
        if not self.validate_dependencies():
            raise ValueError("Invalid pipeline: circular or missing dependencies")

        ordered = []
        remaining = {stage.name for stage in self.stages}
        completed = set()

        while remaining:
            for name in list(remaining):
                stage = self.get_stage(name)
                if stage and all(dep in completed for dep in stage.depends_on):
                    ordered.append(name)
                    completed.add(name)
                    remaining.remove(name)
                    break
            else:
                break

        return ordered

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return self.model_dump(mode="json")
