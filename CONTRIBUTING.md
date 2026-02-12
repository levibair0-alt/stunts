# Contributing to Athena Orchestrator

Thank you for your interest in contributing to Athena Orchestrator!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/levibair0-alt/stunts.git
cd stunts/athena-orchestrator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
make install-dev
```

## Development Workflow

### Running Tests
```bash
make test           # Run tests
make test-cov       # Run tests with coverage
```

### Code Quality
```bash
make lint           # Check code quality
make format         # Auto-format code
make security       # Run security checks
```

### Deterministic Builds
For CI-compatible builds:
```bash
make ci-build       # Run deterministic build and tests
```

## CI/CD

All pull requests automatically run through our CI pipeline:

1. **Dependency Review**: Security review of dependency changes (non-blocking if dependency graph is disabled)
2. **Tests**: Full test suite on Python 3.10, 3.11, and 3.12
3. **Linting**: Code quality checks (non-blocking, for feedback)
4. **Security Scan**: Dependency vulnerability scanning (non-blocking)

### Deterministic Builds
Our CI uses deterministic builds to ensure reproducibility:
- `PYTHONHASHSEED=0` for consistent hashing
- Pinned Python versions
- Cached dependencies

## Code Style

We use:
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking (optional)

Run `make format` before committing to auto-format your code.

## Commit Messages

Follow conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

Example:
```
feat: add batch classification support to ATHENA 875 classifier

- Implement batch_classify method
- Add progress tracking
- Update documentation
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit them
3. Run tests and linting locally: `make test lint`
4. Push to your branch: `git push origin feature/your-feature`
5. Open a pull request with a clear description
6. Wait for CI checks to pass
7. Address any review feedback

## Testing Requirements

- All new features must include tests
- Aim for 80%+ code coverage
- Tests should be deterministic and reproducible
- Use pytest fixtures for common setup

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions/classes
- Update docs/ for architectural changes
- Include usage examples for new features

## Security

- Never commit API keys or secrets
- Use environment variables for configuration
- Report security issues privately
- Run `make security` before submitting PRs

## Questions?

- Check existing issues and discussions
- Review documentation in `docs/`
- Ask questions in pull request comments

Thank you for contributing! 🚀
