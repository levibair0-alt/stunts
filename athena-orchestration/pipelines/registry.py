"""Pipeline registry for dynamic pipeline loading."""

from typing import Any, Optional, Type

from pipelines.base import Pipeline


class PipelineRegistry:
    """
    Registry for pipeline discovery and instantiation.
    
    Pipelines can be registered programmatically or discovered
    from a configuration file.
    """

    def __init__(self):
        self._pipelines: dict[str, Type[Pipeline]] = {}
        self._instances: dict[str, Pipeline] = {}

    def register(self, name: str, pipeline_class: Type[Pipeline]) -> None:
        """
        Register a pipeline class.
        
        Args:
            name: Pipeline name
            pipeline_class: Pipeline class to register
        """
        if not issubclass(pipeline_class, Pipeline):
            raise TypeError(f"{pipeline_class} must be a subclass of Pipeline")
        self._pipelines[name] = pipeline_class

    def unregister(self, name: str) -> None:
        """Unregister a pipeline."""
        self._pipelines.pop(name, None)
        self._instances.pop(name, None)

    def get(self, name: str) -> Optional[Type[Pipeline]]:
        """Get a pipeline class by name."""
        return self._pipelines.get(name)

    def create(self, name: str, config: Optional[dict[str, Any]] = None) -> Pipeline:
        """
        Create a pipeline instance.
        
        Args:
            name: Pipeline name
            config: Configuration for the pipeline
            
        Returns:
            Pipeline instance
        """
        pipeline_class = self._pipelines.get(name)
        if not pipeline_class:
            raise KeyError(f"Pipeline not found: {name}")

        instance = pipeline_class()
        self._instances[name] = instance

        if config:
            import asyncio

            asyncio.run(instance.initialize(config))

        return instance

    def get_instance(self, name: str) -> Optional[Pipeline]:
        """Get an existing pipeline instance."""
        return self._instances.get(name)

    def list_pipelines(self) -> list[str]:
        """List all registered pipeline names."""
        return list(self._pipelines.keys())

    def clear(self) -> None:
        """Clear all registered pipelines."""
        self._pipelines.clear()
        self._instances.clear()


# Global registry instance
_global_registry = PipelineRegistry()


def get_registry() -> PipelineRegistry:
    """Get the global pipeline registry."""
    return _global_registry


def register_pipeline(name: str) -> callable:
    """
    Decorator to register a pipeline class.
    
    Usage:
        @register_pipeline("my-pipeline")
        class MyPipeline(Pipeline):
            ...
    """

    def decorator(cls: Type[Pipeline]) -> Type[Pipeline]:
        _global_registry.register(name, cls)
        return cls

    return decorator
