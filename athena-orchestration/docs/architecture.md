# Athena Orchestration Architecture

## Overview

Athena Orchestration is a **control repo** providing unified orchestration for multiple LLM providers and platforms. It uses a contract-driven approach with stable Intermediate Representations (IRs).

## Core Concepts

### Contracts (IRs)

Contracts define stable interfaces between components:

- **TaskContract**: Represents a unit of work
- **PipelineContract**: Defines a workflow of stages
- **ToolContract**: Metadata for adapter capabilities

### Adapters

Adapters are vendor-specific implementations that conform to the `BaseAdapter` interface:

```
BaseAdapter
├── LLM Adapters
│   ├── GPTAdapter (OpenAI)
│   ├── ClaudeAdapter (Anthropic)
│   ├── GrokAdapter (xAI)
│   ├── GeminiAdapter (Google)
│   └── NotebookLMAdapter (Google)
├── Platform Adapters
│   ├── NotionAdapter
│   └── GitHubAdapter
```

### Pipelines

Pipelines compose adapters into workflows:

```
Pipeline
├── Stage (name, adapter, config)
├── Stage (name, adapter, config, depends_on)
└── Stage (name, adapter, config, depends_on)
```

## Data Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  Pipeline       │
│  (composes      │
│   stages)       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Stage 1│ │Stage 2│
│(GPT)  │ │(Claude│
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌──────────────┐
│  Results     │
└──────────────┘
```

## Configuration

Configuration flows through multiple layers:

1. **Environment Variables**: API keys and secrets
2. **Adapter Config**: Per-adapter settings (model, temperature, etc.)
3. **Pipeline Config**: Stage configuration and dependencies

## Error Handling

All adapters:
- Return `AdapterResult` with success/error status
- Wrap SDK calls with try/except
- Support optional Sentry integration

## Extension Points

### Adding a New LLM

1. Create adapter class implementing `BaseAdapter`
2. Define `tool_contract` property
3. Implement `execute()` and `health_check()` methods
4. Register in `adapters/llm/__init__.py`

### Adding a New Pipeline

1. Subclass `Pipeline`
2. Implement `initialize()` and `validate()`
3. Define stages with dependencies
4. Register with `@register_pipeline` decorator

## Directory Structure

```
athena-orchestration/
├── contracts/           # IR definitions
│   ├── task_contract.py
│   ├── pipeline_contract.py
│   ├── tool_contract.py
│   └── schemas/         # YAML schemas
├── adapters/            # Vendor integrations
│   ├── base.py
│   ├── llm/             # LLM adapters
│   ├── notion/
│   └── github/
├── pipelines/           # Workflow definitions
│   ├── base.py
│   ├── registry.py
│   └── examples/
├── ops/                 # CI/Sentry/Docker
│   ├── sentry_config.py
│   ├── ci/
│   └── docker/
└── docs/                # Documentation
```
