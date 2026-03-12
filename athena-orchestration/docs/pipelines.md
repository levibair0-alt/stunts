# Pipelines Documentation

Pipelines compose adapters into reusable workflows.

## Base Pipeline

```python
from pipelines import Pipeline, Stage
from adapters import GPTAdapter

class MyPipeline(Pipeline):
    name = "my-pipeline"
    description = "My custom pipeline"
    version = "1.0.0"
    
    async def initialize(self, config: dict) -> None:
        self.adapter = GPTAdapter()
        await self.adapter.initialize(config.get("adapter", {}))
        
        self.stages = [
            Stage(
                name="process",
                adapter=self.adapter,
                depends_on=[]
            )
        ]
    
    async def validate(self) -> bool:
        return self.adapter.is_initialized
```

## Using the Registry

### Register a Pipeline

```python
from pipelines import PipelineRegistry, register_pipeline

@register_pipeline("my-pipeline")
class MyPipeline(Pipeline):
    ...
```

### Create and Execute

```python
from pipelines import get_registry

registry = get_registry()

# Create pipeline
pipeline = registry.create("my-pipeline", config)

# Execute
result = await pipeline.execute(input_data)
```

## Example: Research Pipeline

```python
from pipelines import get_registry

# Get the pre-registered research pipeline
registry = get_registry()
pipeline = registry.create("research", {
    "gpt": {"model": "gpt-4o"},
    "claude": {"model": "claude-sonnet-4-20250514"},
    "notion": {"database_id": "your-db-id"}
})

# Execute with input
result = await pipeline.execute({
    "query": "What are the latest AI trends?"
})

print(result["success"])  # True
print(result["stages"])   # ["gather", "analyze", "publish"]
```

## Stage Configuration

Each stage can have:

```python
Stage(
    name="stage-name",
    adapter=my_adapter,
    config={"key": "value"},        # Adapter config
    depends_on=["previous-stage"],  # Dependencies
    input_transform=func,           # Transform input
    output_transform=func           # Transform output
)
```

### Transforms

Transform functions modify data between stages:

```python
def my_transform(output, previous_results):
    # output: Current stage's output
    # previous_results: Dict of all previous stage results
    return {"modified": output}
```

## Execution Order

Pipelines execute stages in topological order based on dependencies:

```python
pipeline = MyPipeline()
await pipeline.initialize(config)

# Get execution order
order = pipeline.stage_names
# ["stage1", "stage2", "stage3"]
```

## Getting Results

```python
result = await pipeline.execute(input_data)

# Get specific stage result
stage_result = pipeline.get_stage_result("stage-name")
```

## Custom Pipeline Example

```python
from pipelines import Pipeline, Stage, register_pipeline
from adapters import GPTAdapter, GitHubAdapter

@register_pipeline("code-review")
class CodeReviewPipeline(Pipeline):
    name = "code-review"
    description = "Automated code review pipeline"
    version = "1.0.0"
    
    async def initialize(self, config: dict) -> None:
        self.gpt = GPTAdapter()
        self.github = GitHubAdapter()
        
        await self.gpt.initialize(config.get("gpt", {}))
        await self.github.initialize(config.get("github", {}))
        
        self.stages = [
            Stage(
                name="get_changes",
                adapter=self.github,
                config=config.get("get_changes", {}),
            ),
            Stage(
                name="review",
                adapter=self.gpt,
                depends_on=["get_changes"],
                output_transform=self._format_review,
            ),
            Stage(
                name="create_pr_comment",
                adapter=self.github,
                depends_on=["review"],
            ),
        ]
    
    async def validate(self) -> bool:
        return self.gpt.is_initialized and self.github.is_initialized
    
    def _format_review(self, output, previous_results):
        return {
            "messages": [{
                "role": "user",
                "content": f"Review this code:\n{output.get('diff', '')}"
            }]
        }
```

## Best Practices

1. **Always validate** - Implement `validate()` to check configuration
2. **Handle errors** - Use try/except in stages
3. **Transform data** - Use transforms to adapt between stages
4. **Log progress** - Track execution with timestamps
5. **Test pipelines** - Mock adapters for unit tests
