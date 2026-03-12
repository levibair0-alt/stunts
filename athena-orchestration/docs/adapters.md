# Adapters Documentation

Adapters provide vendor-specific implementations for LLM providers and platforms.

## Base Adapter

All adapters implement the `BaseAdapter` interface:

```python
from adapters import BaseAdapter, AdapterResult

class MyAdapter(BaseAdapter):
    @property
    def tool_contract(self) -> ToolContract:
        ...
    
    async def initialize(self, config: dict) -> None:
        ...
    
    async def execute(self, input_data: dict) -> AdapterResult:
        ...
    
    async def health_check(self) -> bool:
        ...
```

### AdapterResult

All executions return an `AdapterResult`:

```python
result = await adapter.execute(data)

if result.success:
    print(result.data)
else:
    print(result.error)
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether execution succeeded |
| `data` | dict | Output data |
| `error` | str | Error message |
| `metadata` | dict | Additional metadata |

## LLM Adapters

### GPTAdapter

OpenAI GPT integration.

```python
from adapters import GPTAdapter

adapter = GPTAdapter()
await adapter.initialize({
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096
})

result = await adapter.execute({
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "stream": False  # or True for streaming
})
```

**Environment Variables:**
- `OPENAI_API_KEY`

**Configuration:**
```python
{
    "model": "gpt-4o",           # Model name
    "temperature": 0.7,          # 0-2
    "max_tokens": 4096,          # Max response tokens
    "base_url": None,            # Custom endpoint
    "timeout": 60                # Request timeout
}
```

### ClaudeAdapter

Anthropic Claude integration.

```python
from adapters import ClaudeAdapter

adapter = ClaudeAdapter()
await adapter.initialize({
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.7
})

result = await adapter.execute({
    "messages": [{"role": "user", "content": "Hello!"}]
})
```

**Environment Variables:**
- `ANTHROPIC_API_KEY`

### GrokAdapter

xAI Grok integration.

```python
from adapters import GrokAdapter

adapter = GrokAdapter()
await adapter.initialize({
    "model": "grok-2"
})
```

**Environment Variables:**
- `XAI_API_KEY`

### GeminiAdapter

Google Gemini integration.

```python
from adapters import GeminiAdapter

adapter = GeminiAdapter()
await adapter.initialize({
    "model": "gemini-2.0-flash",
    "temperature": 0.7
})

result = await adapter.execute({
    "messages": [{"role": "user", "content": "Hello!"}]
})
```

**Environment Variables:**
- `GOOGLE_API_KEY`

### NotebookLMAdapter

Google NotebookLM (placeholder implementation).

```python
from adapters import NotebookLMAdapter

adapter = NotebookLMAdapter()
await adapter.initialize({
    "project_id": "my-project"
})

# Generate audio overview (placeholder)
result = await adapter.execute({
    "operation": "generate_audio",
    "sources": ["source1", "source2"]
})
```

## Platform Adapters

### NotionAdapter

Notion workspace integration.

```python
from adapters import NotionAdapter

adapter = NotionAdapter()
await adapter.initialize({
    "database_id": "your-database-id"
})

# Create a page
result = await adapter.execute({
    "operation": "create_page",
    "properties": {
        "Name": {"title": [{"text": {"content": "My Page"}}]}
    },
    "content": "Page content here"
})

# Query database
result = await adapter.execute({
    "operation": "query_database",
    "filter": {
        "property": "Status",
        "select": {"equals": "Done"}
    }
})
```

**Operations:**
- `create_page` - Create new page
- `update_page` - Update existing page
- `get_page` - Get page by ID
- `delete_page` - Archive page
- `query_database` - Query database
- `create_database` - Create database
- `append_block_children` - Add blocks

**Environment Variables:**
- `NOTION_API_KEY`

### GitHubAdapter

GitHub integration.

```python
from adapters import GitHubAdapter

adapter = GitHubAdapter()
await adapter.initialize({
    "repo_owner": "myorg",
    "repo_name": "myrepo"
})

# Create PR
result = await adapter.execute({
    "operation": "create_pr",
    "title": "Add new feature",
    "body": "Description",
    "head": "feature-branch",
    "base": "main"
})

# Create issue
result = await adapter.execute({
    "operation": "create_issue",
    "title": "Bug report",
    "body": "Description",
    "labels": ["bug"]
})
```

**Operations:**
- `create_pr` - Create pull request
- `get_pr` - Get PR by number
- `list_prs` - List PRs
- `create_issue` - Create issue
- `get_issue` - Get issue
- `list_issues` - List issues
- `create_branch` - Create branch
- `delete_branch` - Delete branch
- `trigger_workflow` - Trigger workflow

**Environment Variables:**
- `GITHUB_TOKEN`

## Health Checks

All adapters implement `health_check()`:

```python
is_healthy = await adapter.health_check()
```

Returns `True` if the adapter can make successful API calls.
