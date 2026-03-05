"""Pipeline base classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from adapters.base import BaseAdapter, AdapterResult


@dataclass
class Stage:
    """Represents a single stage in a pipeline."""

    name: str
    adapter: BaseAdapter
    config: dict[str, Any] = field(default_factory=dict)
    input_transform: Optional[callable] = None
    output_transform: Optional[callable] = None
    depends_on: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.adapter, BaseAdapter):
            raise TypeError("adapter must be an instance of BaseAdapter")


class Pipeline(ABC):
    """
    Abstract base class for pipelines.
    
    Subclasses must define the pipeline structure and stages.
    """

    name: str = "base"
    description: str = ""
    version: str = "1.0.0"
    stages: list[Stage] = []

    def __init__(self):
        self._execution_order: list[str] = []
        self._stage_results: dict[str, AdapterResult] = {}
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the pipeline with configuration."""
        ...

    @abstractmethod
    async def validate(self) -> bool:
        """Validate the pipeline configuration."""
        ...

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the pipeline with input data.
        
        Args:
            input_data: Input data for the pipeline
            
        Returns:
            Dictionary containing pipeline results
        """
        if not self.validate():
            raise ValueError("Pipeline validation failed")

        self._started_at = datetime.utcnow()
        self._stage_results = {}
        self._execution_order = self._get_execution_order()

        current_data = input_data.copy()

        for stage_name in self._execution_order:
            stage = self._get_stage(stage_name)
            if not stage:
                continue

            # Check dependencies
            deps_satisfied = all(dep in self._stage_results for dep in stage.depends_on)
            if not deps_satisfied:
                raise ValueError(f"Dependencies not satisfied for stage: {stage_name}")

            # Transform input if needed
            if stage.input_transform:
                current_data = stage.input_transform(current_data, self._stage_results)

            # Execute stage
            result = await stage.adapter.execute(current_data)

            self._stage_results[stage_name] = result

            if not result.success:
                raise RuntimeError(f"Stage {stage_name} failed: {result.error}")

            # Transform output if needed
            if stage.output_transform:
                current_data = stage.output_transform(result.data, self._stage_results)
            else:
                current_data = result.data or {}

        self._completed_at = datetime.utcnow()

        return {
            "success": True,
            "pipeline": self.name,
            "version": self.version,
            "stages": self._execution_order,
            "results": {name: r.data for name, r in self._stage_results.items()},
            "started_at": self._started_at.isoformat(),
            "completed_at": self._completed_at.isoformat(),
        }

    async def execute_stage(self, stage_name: str, input_data: dict[str, Any]) -> AdapterResult:
        """Execute a single stage."""
        stage = self._get_stage(stage_name)
        if not stage:
            return AdapterResult(success=False, error=f"Stage not found: {stage_name}")

        return await stage.adapter.execute(input_data)

    def _get_stage(self, name: str) -> Optional[Stage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def _get_execution_order(self) -> list[str]:
        """Get stages in topological order."""
        ordered = []
        remaining = {stage.name for stage in self.stages}
        completed = set()

        while remaining:
            for name in list(remaining):
                stage = self._get_stage(name)
                if stage and all(dep in completed for dep in stage.depends_on):
                    ordered.append(name)
                    completed.add(name)
                    remaining.remove(name)
                    break
            else:
                break

        return ordered

    def get_stage_result(self, stage_name: str) -> Optional[AdapterResult]:
        """Get the result of a specific stage."""
        return self._stage_results.get(stage_name)

    @property
    def stage_names(self) -> list[str]:
        """Get list of stage names."""
        return [s.name for s in self.stages]

    @property
    def is_complete(self) -> bool:
        """Check if pipeline has completed."""
        return self._completed_at is not None
