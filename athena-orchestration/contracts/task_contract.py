"""Task Contract - Stable Intermediate Representation for tasks."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskMetadata(BaseModel):
    """Additional metadata for task execution."""

    model_config = ConfigDict(strict=True)

    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    retry_count: int = Field(default=0, ge=0, le=5)
    tags: list[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    source: Optional[str] = None
    custom: dict[str, Any] = Field(default_factory=dict)


class TaskContract(BaseModel):
    """
    Stable Intermediate Representation for a task.
    
    This is the canonical contract that all adapters and pipelines
    use to communicate. It ensures type safety and schema validation.
    """

    model_config = ConfigDict(strict=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable task name")
    input: dict[str, Any] = Field(default_factory=dict, description="Task input data")
    output: Optional[dict[str, Any]] = Field(default=None, description="Task output data")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    metadata: TaskMetadata = Field(default_factory=TaskMetadata, description="Task metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    adapter_name: Optional[str] = Field(default=None, description="Adapter used for execution")

    def mark_running(self) -> None:
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_completed(self, output: dict[str, Any]) -> None:
        """Mark task as completed with output."""
        self.status = TaskStatus.COMPLETED
        self.output = output
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return self.model_dump(mode="json")
