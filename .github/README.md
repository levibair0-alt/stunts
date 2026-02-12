# CI/CD Configuration

This directory contains GitHub Actions workflows for automated testing, security scanning, and compliance checks.

## Workflows

### security-compliance.yml
Runs security and compliance checks on pull requests and main branch:
- **Dependency Review**: Reviews dependency changes for security issues (continue-on-error enabled for repositories without dependency graph)
- **Test**: Runs pytest test suite
- **Lint**: Checks code quality with flake8, black, and isort (non-blocking)
- **Security Scan**: Scans dependencies for known vulnerabilities using safety (non-blocking)

### ci.yml
Runs comprehensive CI builds across multiple Python versions:
- **Build & Test**: Tests on Python 3.10, 3.11, and 3.12
- **Deterministic Build**: Uses PYTHONHASHSEED=0 for reproducible builds
- **Coverage**: Generates code coverage reports and uploads to Codecov

## Key Features

### Continue-on-Error Configuration
The dependency review step includes `continue-on-error: true` because:
- Repository may not have dependency graph enabled
- Prevents CI from blocking on configuration issues
- Still provides security insights when available

### Deterministic Builds
All builds use:
- `PYTHONHASHSEED=0` environment variable for reproducible Python hashing
- Pip caching for faster, consistent dependency installation
- Pinned Python versions in matrix strategy

### Non-Blocking Linters
Linting and security scans use `continue-on-error: true` to:
- Provide feedback without blocking merges
- Allow gradual code quality improvements
- Focus on critical errors first

## Local Development

To run the same checks locally:

```bash
cd athena-orchestrator

# Install development dependencies
make install-dev

# Run tests
make test

# Run linters
make lint

# Run security scan
make security

# Run deterministic CI build
make ci-build
```

## Configuration Files

- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies
- `Makefile`: Convenient commands for local development
