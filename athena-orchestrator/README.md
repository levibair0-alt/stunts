# Athena Orchestrator

Multi-project AI workflow orchestration system with ChatGPT, Notion, Git, and CTO.new integration.

## Overview

Athena Orchestrator is your **project operating system** - a centralized brain that manages:
- Multi-project AI task planning and execution
- Git automation with guardrails and rate limiting
- Notion workspace integration (master registry + per-project databases)
- CTO.new execution adapter (clean, swappable)
- Continuous task processing with per-project frequencies

## Architecture

```
athena-orchestrator/
 config/               # Configuration & guardrails
   ├── projects.json              # Project registry (stunts as #1)
   ├── agents.yaml                # Agent-specific settings
   ├── permissions.yaml           # Per-project permissions
   ├── settings.yaml              # System-wide guardrails
   └── athena_875_taxonomy.yaml   # ATHENA 875 industry taxonomy
 agents/               # AI agents with safety checks
   ├── planner_agent.py           # Task planning (OpenAI integration point)
   ├── executor_agent.py          # Task execution with permissions
   ├── commit_agent.py            # Git commits with rate limiting
   └── athena_875_classifier.py   # ATHENA 875 submission classifier
 notion/               # Notion integration
   ├── notion_client.py           # Master DB + per-project DB support
   └── templates/                 # Database schemas (5 JSON files)
 cto/                  # CTO.new adapter
   └── connector.py               # Clean execution adapter (stub)
 git/                  # Git operations
   └── git_manager.py             # Branch, commit, push with prefix support
 runner/               # Continuous task processing
   └── main_loop.py               # Main execution loop
 templates/            # Standardized formats
   ├── task_output_format.json
   └── submission_schema.yaml     # ATHENA 875 submission format
 docs/                 # Documentation
   └── ATHENA_875_CLASSIFIER.md   # Classifier documentation
```

## Setup

### 1. Install Dependencies

```bash
cd athena-orchestrator
pip install -r requirements.txt
```

### 2. Configure Projects

Edit `config/projects.json` to add your projects:

```json
[
  {
    "name": "my-project",
    "repo": "/path/to/repo",
    "branch": "main",
    "run_frequency": 300,
    "auto_commit": true,
    "notion_db_tasks": "database-id-here",
    "notion_db_runs": "database-id-here",
    "notion_db_docs": "database-id-here"
  }
]
```

### 3. Set Up Notion Workspace

#### Create Master Databases (under /Orchestrator Control)

1. **Projects Database** - Use `notion/templates/master_projects_db_schema.json`
2. **Global Runs Database** - Use `notion/templates/master_runs_db_schema.json`

#### Create Per-Project Databases (under /Project Name)

1. **Tasks Database** - Use `notion/templates/project_tasks_db_schema.json`
2. **Runs Database** - Use `notion/templates/project_runs_db_schema.json`
3. **Docs Database** - Use `notion/templates/project_docs_db_schema.json`

Add database IDs to `config/projects.json`.

### 4. Configure Environment Variables

Create `.env` file:

```env
NOTION_API_KEY=your_notion_integration_token
OPENAI_API_KEY=your_openai_api_key
CTO_API_KEY=your_cto_api_key
CTO_BASE_URL=https://api.cto.new
```

## Guardrails

All guardrails are enforced in `config/settings.yaml` and MUST be active:

```yaml
max_commits_per_hour: 20    # Global commit rate limit
branch_prefix: "task/"         # All branches must use this prefix
auto_merge: false              # Never auto-merge to main
require_tests: false           # Optional: require tests before commit
log_level: INFO               # Logging verbosity
```

**Agents will refuse to act if these aren't loaded.**

## Per-Project Permissions

Configure individual project rules in `config/permissions.yaml`:

```yaml
stunts:
  auto_commit_allowed: true
  auto_merge_allowed: false
  require_tests: false
  max_branches: 10
  allowed_file_types: ["*"]
  blocked_files: ["*.secret", "*.key", "*.pem"]
```

## Usage

### Run Once (Testing)

```bash
cd athena-orchestrator
python runner/main_loop.py
```

### Run Continuous Mode

Edit `runner/main_loop.py`, uncomment:
```python
loop.run_continuous()
```

Then run:
```bash
python runner/main_loop.py
```

## Task Lifecycle

1. **Notion** → New task added to project's Tasks DB
2. **Planner Agent** → Creates execution plan (OpenAI API)
3. **Executor Agent** → Validates permissions, executes task
4. **Commit Agent** → Commits changes (if auto_commit enabled)
5. **Notion** → Logs run to Global Runs + Project Runs DBs

## ATHENA 875 Protocol - Submission Classifier

The orchestrator includes an **ATHENA 875 Protocol-compliant submission classifier** for categorizing marketplace submissions into 10 industry categories.

### Quick Start

```bash
cd athena-orchestrator
python agents/athena_875_classifier.py
```

### Usage Example

```python
from agents.athena_875_classifier import Athena875Classifier

# Initialize classifier
classifier = Athena875Classifier(config_path="./config")

# Prepare submission
submission = {
    'title': 'MediTrack - Patient Management Platform',
    'description': '''Comprehensive healthcare platform for hospitals and clinics
    to manage patient records, appointments, and medical histories.''',
    'tags': ['healthcare', 'telemedicine', 'EHR'],
    'website_url': 'https://meditrack.health'
}

# Classify
result = classifier.classify_submission(submission)

if result.meets_thresholds:
    print(f"Industry: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Score: {result.classification_score}")
```

### Features

- ✅ **10 Industry Categories**: Technology, Finance, Healthcare, Education, Retail, Manufacturing, Media, Real Estate, Transportation, Professional Services
- ✅ **Deterministic Scoring**: Configurable keyword weights and thresholds
- ✅ **Confidence Metrics**: min_score=3, min_margin=1 (configurable)
- ✅ **Handshake Verification**: Protocol compliance checks
- ✅ **YAML Taxonomy**: Easy-to-update configuration without code changes

### Documentation

Full classifier documentation: [docs/ATHENA_875_CLASSIFIER.md](docs/ATHENA_875_CLASSIFIER.md)

## Testing

Test with one project (stunts) before adding others:

```bash
# Test planner
cd athena-orchestrator
python agents/planner_agent.py

# Test executor
python agents/executor_agent.py

# Test commit agent
python agents/commit_agent.py

# Test ATHENA 875 classifier
python agents/athena_875_classifier.py

# Test full loop
python runner/main_loop.py
```

## Adding More Projects

1. Add project to `config/projects.json`
2. Add permissions to `config/permissions.yaml`
3. Create Notion databases in workspace
4. Add database IDs to project config
5. Run orchestrator

## Safety Features

- ✅ **Max commits per hour** - Prevents repo flooding
- ✅ **Branch prefix enforcement** - All branches use `task/` prefix
- ✅ **Auto-merge disabled** - Never auto-merge to main
- ✅ **Per-project permissions** - Different rules per project
- ✅ **File type blocking** - Blocks *.secret, *.key, *.pem
- ✅ **Guardrails verification** - Agents refuse to act if not loaded

## Next Steps (Wiring)

After skeleton setup, wire:

### Phase 1
- [ ] Environment variables (NOTION_API_KEY, OPENAI_API_KEY)
- [ ] OpenAI planner integration in `agents/planner_agent.py`
- [ ] Notion client real API calls in `notion/notion_client.py`
- [ ] Local dry-run mode for testing

### Phase 2
- [ ] CTO.new connector real API in `cto/connector.py`
- [ ] Auto branch + commit loop
- [ ] PR system integration
- [ ] Multi-project scaling (5 projects)

### Phase 3
- [ ] Dashboard visibility
- [ ] Task routing logic
- [ ] Throttling + safety audit logs

## Troubleshooting

**Guardrails not loaded:**
- Check `config/settings.yaml` exists and has required keys
- Agents will refuse to act if guardrails missing

**Commit blocked:**
- Check `max_commits_per_hour` limit
- Review `config/commit_history.json`

**Permission denied:**
- Check `config/permissions.yaml` for project settings
- Verify `auto_commit_allowed` is true

**Notion not logging:**
- Check NOTION_API_KEY is set
- Verify database IDs in `config/projects.json`
- Client logs warnings if not configured

## License

MIT

## Support

This is the foundational skeleton. Wire integrations carefully and test thoroughly before production use.
