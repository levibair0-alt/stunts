# Athena Orchestration

Unified orchestration spine that unifies all LLM frontends with Notion and GitHub into a composable pipeline system.

## Overview

Athena Orchestration is a **control repo** providing:
- **Contracts**: Stable Intermediate Representations (IRs) for tasks, pipelines, and tools
- **Adapters**: Per-vendor bindings for GPT, Claude, Grok, Gemini, NotebookLM, Notion, and GitHub
- **Pipelines**: Composable workflow definitions with stage execution
- **Ops**: CI validation, Sentry error tracking, and Docker deployment

## Architecture

```
athena-orchestration/
├── contracts/           # Stable Intermediate Representations (IRs)
│   ├── schemas/         # YAML schema definitions
│   ├── task_contract.py
│   ├── pipeline_contract.py
│   └── tool_contract.py
├── adapters/            # Per-tool bindings
│   ├── base.py          # Base adapter interface
│   ├── llm/             # LLM vendor adapters
│   ├── notion/          # Notion integration
│   └── github/          # GitHub integration
├── pipelines/           # Workflow definitions
│   ├── base.py          # Pipeline base class
│   ├── registry.py      # Dynamic pipeline loader
│   └── examples/        # Sample pipelines
├── ops/                 # CI/Sentry/Docker glue
│   ├── sentry_config.py
│   ├── ci/
│   └── docker/
├── docs/                # Documentation
├── tests/               # Test suite
└── pyproject.toml       # Project config (uv)
```

## Quick Start

### Installation

```bash
cd athena-orchestration
uv sync
```

### Environment Setup

Copy `.env.example` to `.env` and configure:

```env
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
XAI_API_KEY=xai-...
GOOGLE_API_KEY=AI...

# Platform Integrations
NOTION_API_KEY=secret_...
GITHUB_TOKEN=ghp_...

# Monitoring
SENTRY_DSN=https://...
```

### Basic Usage

```python
from contracts import TaskContract, PipelineContract
from adapters.llm import GPTAdapter, ClaudeAdapter
from pipelines import PipelineRegistry

# Create a task
task = TaskContract(
    id="task-001",
    name="research-task",
    input={"query": "What is the best approach to..."},
    metadata={"priority": "high"}
)

# Execute with your preferred LLM
adapter = GPTAdapter()
result = await adapter.execute(task.model_dump())
```

## Adapters

### LLM Adapters

| Adapter | Vendor | Features |
|---------|--------|----------|
| `GPTAdapter` | OpenAI | Chat completion, streaming, function calling |
| `ClaudeAdapter` | Anthropic | Tools, vision, extended context |
| `GrokAdapter` | xAI | Chat completion, streaming |
| `GeminiAdapter` | Google | Multimodal, grounded generation |
| `NotebookLMAdapter` | NotebookLM | Audio overview, source analysis |

### Platform Adapters

| Adapter | Features |
|---------|----------|
| `NotionAdapter` | Page CRUD, database queries, block updates |
| `GitHubAdapter` | PR creation, issue management, workflow triggers |

## Pipelines

Define composable workflows:

```python
from pipelines import Pipeline, Stage

class ResearchPipeline(Pipeline):
    name = "research"
    stages = [
        Stage("gather", adapter=GPTAdapter()),
        Stage("analyze", adapter=ClaudeAdapter()),
        Stage("publish", adapter=NotionAdapter()),
    ]
```

## Contracts

All data flows use Pydantic v2 models with strict validation:

- `TaskContract`: Task IR definitions
- `PipelineContract`: Pipeline IR definitions
- `ToolContract`: Tool metadata models

YAML schemas are stored in `contracts/schemas/` and validated on CI.

## Development

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

### Docker

```bash
docker compose -f ops/docker/docker-compose.yml up
```

## License

MIT
