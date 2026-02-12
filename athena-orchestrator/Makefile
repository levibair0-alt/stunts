.PHONY: help install install-dev test lint format clean build ci-build

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build project (compile Python files)"
	@echo "  make ci-build     - Deterministic build for CI"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=xml --cov-report=term

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	black --check .
	isort --check-only .

format:
	black .
	isort .

security:
	safety check --file requirements.txt
	bandit -r . -ll

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage coverage.xml htmlcov/

build:
	@echo "Compiling Python files..."
	python -m py_compile agents/*.py 2>/dev/null || true
	python -m py_compile config/*.py 2>/dev/null || true
	python -m py_compile runner/*.py 2>/dev/null || true
	python -m py_compile cto/*.py 2>/dev/null || true
	python -m py_compile git/*.py 2>/dev/null || true
	python -m py_compile notion/*.py 2>/dev/null || true
	@echo "Build complete!"

ci-build: clean
	@echo "Running deterministic CI build..."
	PYTHONHASHSEED=0 $(MAKE) build
	PYTHONHASHSEED=0 $(MAKE) test
	@echo "CI build complete!"
