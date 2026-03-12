"""Pipelines package - Workflow definitions and execution."""

from pipelines.base import Pipeline, Stage
from pipelines.registry import PipelineRegistry

__all__ = [
    "Pipeline",
    "Stage",
    "PipelineRegistry",
]
