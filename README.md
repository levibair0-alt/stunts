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
```

### Key Features

- 🤖 **Multi-project AI orchestration** - Manage 5+ projects from one system
- 🔒 **Guardrails & safety** - Max commits, branch prefixes, rate limiting
- 📝 **Notion workspace model** - Master DB + per-project DBs
- 🔄 **Git automation** - Auto branch, commit, push with safety checks
- ⚡ **Continuous runner** - Poll and process tasks automatically
- 🎯 **ATHENA 875 Classifier** - 10-industry submission classifier with deterministic scoring

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

Built with cto.new 🚀
