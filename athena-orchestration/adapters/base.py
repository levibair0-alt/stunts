"""Base adapter interface for all vendor integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from contracts.tool_contract import ToolContract


@dataclass
class AdapterResult:
    """Result from adapter execution."""

    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAdapter(ABC):
    """
    Abstract base class for all adapters.
    
    All vendor adapters must implement this interface to ensure
    consistent behavior across different integrations.
    """

    def __init__(self):
        self._config: dict[str, Any] = {}
        self._initialized: bool = False

    @property
    @abstractmethod
    def tool_contract(self) -> ToolContract:
        """Return the tool contract metadata."""
        ...

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize the adapter with configuration.
        
        Args:
            config: Configuration dictionary for the adapter
        """
        self._config = config
        self._initialized = True

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> AdapterResult:
        """
        Execute the adapter with input data.
        
        Args:
            input_data: Input data for execution
            
        Returns:
            AdapterResult with success status and output data
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the adapter is healthy and ready to use.
        
        Returns:
            True if adapter is healthy, False otherwise
        """
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if adapter is initialized."""
        return self._initialized

    @property
    def config(self) -> dict[str, Any]:
        """Get current configuration."""
        return self._config.copy()

    async def cleanup(self) -> None:
        """Clean up resources. Override if needed."""
        self._initialized = False
        self._config = {}
