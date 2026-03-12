"""Tests for task contract."""

import pytest
from datetime import datetime

from contracts.task_contract import TaskContract, TaskStatus, TaskMetadata


class TestTaskContract:
    """Tests for TaskContract."""

    def test_create_task(self):
        """Test creating a basic task."""
        task = TaskContract(
            id="task-001",
            name="test-task",
            input={"query": "test query"},
        )
        
        assert task.id == "task-001"
        assert task.name == "test-task"
        assert task.status == TaskStatus.PENDING
        assert task.input == {"query": "test query"}

    def test_mark_running(self):
        """Test marking task as running."""
        task = TaskContract(id="t1", name="test")
        task.mark_running()
        
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_mark_completed(self):
        """Test marking task as completed."""
        task = TaskContract(id="t1", name="test")
        task.mark_completed({"result": "success"})
        
        assert task.status == TaskStatus.COMPLETED
        assert task.output == {"result": "success"}
        assert task.completed_at is not None

    def test_mark_failed(self):
        """Test marking task as failed."""
        task = TaskContract(id="t1", name="test")
        task.mark_failed("Something went wrong")
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "Something went wrong"

    def test_metadata_defaults(self):
        """Test default metadata values."""
        task = TaskContract(id="t1", name="test")
        
        assert task.metadata.priority == "normal"
        assert task.metadata.timeout_seconds == 300
        assert task.metadata.retry_count == 0

    def test_custom_metadata(self):
        """Test custom metadata."""
        task = TaskContract(
            id="t1",
            name="test",
            metadata=TaskMetadata(
                priority="high",
                timeout_seconds=600,
                tags=["urgent", "production"],
            ),
        )
        
        assert task.metadata.priority == "high"
        assert task.metadata.timeout_seconds == 600
        assert task.metadata.tags == ["urgent", "production"]

    def test_to_yaml_dict(self):
        """Test conversion to dictionary."""
        task = TaskContract(id="t1", name="test", input={"key": "value"})
        data = task.to_yaml_dict()
        
        assert data["id"] == "t1"
        assert data["name"] == "test"
        assert data["input"] == {"key": "value"}


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Test all status values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"


class TestTaskMetadata:
    """Tests for TaskMetadata."""

    def test_priority_validation(self):
        """Test priority pattern validation."""
        with pytest.raises(Exception):
            TaskMetadata(priority="invalid")

    def test_timeout_bounds(self):
        """Test timeout boundary values."""
        # Valid values
        meta = TaskMetadata(timeout_seconds=1)
        assert meta.timeout_seconds == 1
        
        meta = TaskMetadata(timeout_seconds=3600)
        assert meta.timeout_seconds == 3600
        
        # Invalid values
        with pytest.raises(Exception):
            TaskMetadata(timeout_seconds=0)
        
        with pytest.raises(Exception):
            TaskMetadata(timeout_seconds=4000)
