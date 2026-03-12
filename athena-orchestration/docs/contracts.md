# Contracts Documentation

Contracts are Stable Intermediate Representations (IRs) that ensure type safety and schema validation across the orchestration system.

## TaskContract

Represents a unit of work to be executed.

```python
from contracts import TaskContract, TaskStatus

task = TaskContract(
    id="task-001",
    name="my-task",
    input={"query": "What is AI?"},
    metadata={"priority": "high"}
)
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier |
| `name` | str | Human-readable name |
| `input` | dict | Task input data |
| `output` | dict | Task output (after execution) |
| `status` | TaskStatus | Current status |
| `metadata` | TaskMetadata | Additional config |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `started_at` | datetime | Execution start time |
| `completed_at` | datetime | Execution completion time |
| `error` | str | Error message if failed |
| `adapter_name` | str | Adapter used |

### TaskStatus

- `pending` - Not yet executed
- `running` - Currently executing
- `completed` - Successfully completed
- `failed` - Execution failed
- `cancelled` - Cancelled before completion

### TaskMetadata

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `priority` | str | "normal" | low/normal/high/critical |
| `timeout_seconds` | int | 300 | Max execution time |
| `retry_count` | int | 0 | Number of retries |
| `tags` | list[str] | [] | Optional tags |
| `created_by` | str | None | Creator identifier |
| `source` | str | None | Source system |
| `custom` | dict | {} | Custom fields |

## PipelineContract

Represents a workflow of stages.

```python
from contracts import PipelineContract, StageContract, StageStatus

pipeline = PipelineContract(
    id="pipeline-001",
    name="research",
    stages=[
        StageContract(
            name="gather",
            adapter_name="gpt",
            depends_on=[]
        ),
        StageContract(
            name="analyze",
            adapter_name="claude",
            depends_on=["gather"]
        )
    ]
)
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier |
| `name` | str | Pipeline name |
| `description` | str | Description |
| `version` | str | Semantic version |
| `stages` | list[StageContract] | Pipeline stages |
| `input_schema` | dict | JSON Schema for input |
| `output_schema` | dict | JSON Schema for output |
| `metadata` | dict | Additional config |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update |

### StageContract

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Stage name |
| `adapter_name` | str | Adapter to use |
| `adapter_config` | dict | Adapter configuration |
| `input_transform` | dict | Input transformation |
| `output_transform` | dict | Output transformation |
| `depends_on` | list[str] | Stage dependencies |
| `status` | StageStatus | Execution status |

## ToolContract

Metadata describing adapter capabilities.

```python
from contracts import ToolContract, ToolType, ToolCapabilities

tool = ToolContract(
    name="gpt",
    type=ToolType.LLM,
    vendor="OpenAI",
    capabilities=ToolCapabilities(
        streaming=True,
        function_calling=True
    )
)
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Tool name |
| `type` | ToolType | llm/notion/github/custom |
| `vendor` | str | Vendor name |
| `version` | str | Tool version |
| `description` | str | Description |
| `capabilities` | ToolCapabilities | Feature flags |
| `config_schema` | dict | Configuration schema |
| `env_vars` | list[str] | Required env vars |
| `api_endpoint` | str | API URL |

### ToolCapabilities

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `streaming` | bool | false | Supports streaming |
| `function_calling` | bool | false | Supports function calling |
| `vision` | bool | false | Supports vision/multimodal |
| `tools` | bool | false | Supports tools |
| `batch` | bool | false | Supports batch processing |
| `async_execution` | bool | true | Supports async |

## YAML Schemas

YAML schemas are stored in `contracts/schemas/`:

- `task_schema.yaml` - Task contract schema
- `pipeline_schema.yaml` - Pipeline contract schema

Validate on CI:

```python
from ops.ci import validate_contract

is_valid, error = validate_contract("task", data)
```
