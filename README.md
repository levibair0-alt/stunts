# Stunts

Dope build

---

## 🧠 Athena Orchestrator

This repository contains **athena-orchestrator** - your multi-project AI workflow orchestration system.

### Quick Start

```bash
cd athena-orchestrator
pip install -r requirements.txt
python runner/main_loop.py
```

### Architecture

```
stunts/
 athena-orchestrator/    ← AI orchestration brain
    ├── config/               # Projects, agents, permissions, settings
    ├── agents/               # Planner, Executor, Commit agents
    ├── notion/               # Notion workspace integration
    ├── cto/                  # CTO.new execution adapter
    ├── git/                  # Git operations automation
    ├── runner/               # Continuous task processing
    └── templates/            # Standardized formats
 mlstudio/               ← Chat export converter toolkit
    ├── convert_chat_export.py  # Main conversion script
    ├── chatgpt_parser.py       # ChatGPT format parser
    ├── examples/               # Sample export files
    └── outputs/                # Generated Markdown files
```

### Key Features

- 🤖 **Multi-project AI orchestration** - Manage 5+ projects from one system
- 🔒 **Guardrails & safety** - Max commits, branch prefixes, rate limiting
- 📝 **Notion workspace model** - Master DB + per-project DBs
- 🔄 **Git automation** - Auto branch, commit, push with safety checks
- ⚡ **Continuous runner** - Poll and process tasks automatically
- 🎯 **ATHENA 875 Classifier** - 10-industry submission classifier with deterministic scoring
- 🚀 **CI/CD Pipeline** - Automated testing, security scanning, and compliance checks

### Development

```bash
cd athena-orchestrator

# Install development dependencies
make install-dev

# Run tests
make test

# Run deterministic CI build
make ci-build

# Check code quality
make lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

### Documentation

Full documentation: [athena-orchestrator/README.md](athena-orchestrator/README.md)

### Status

**Current Phase:** Skeleton built ✅

**Next Steps:**
- [ ] Wire Notion integration
- [ ] Add OpenAI planner
- [ ] Connect CTO.new executor
- [ ] Test with stunts project
- [ ] Scale to 5 projects

---

## 💬 MLStudio - Chat Export Converter

A Python toolkit for converting AI chat exports into readable Markdown documents.

### Quick Start

```bash
cd mlstudio
python convert_chat_export.py examples/chatgpt_example.json
```

### Features

- 📄 **ChatGPT Support** - Convert ChatGPT conversation exports to Markdown
- 🎨 **Clean Formatting** - Preserves code blocks, timestamps, and message structure
- 🔧 **Extensible** - Designed to support Claude, Gemini, and other chat services
- 📁 **Organized Output** - Auto-generated filenames in dedicated `outputs/` directory

### Exporting from ChatGPT

1. Go to ChatGPT Settings → Data controls
2. Click "Export data"
3. Download and extract `conversations.json`
4. Run: `python convert_chat_export.py conversations.json`

Full documentation: [mlstudio/README.md](mlstudio/README.md)

---

Built with cto.new 🚀
