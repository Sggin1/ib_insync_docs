# Makefile for dedup project
# Daily workflow automation

.PHONY: help format check lint complexity type test all clean install

# Default target
help:
	@echo "Dedup Project - Daily Workflow Commands"
	@echo "========================================"
	@echo ""
	@echo "Development workflow:"
	@echo "  make all          - Run complete quality check (format + check)"
	@echo "  make format       - Format code with Black"
	@echo "  make check        - Run all checks (lint + complexity + type)"
	@echo ""
	@echo "Individual checks:"
	@echo "  make lint         - Run Flake8 linting"
	@echo "  make complexity   - Check cyclomatic complexity (CC < 6)"
	@echo "  make type         - Run mypy type checking"
	@echo "  make test         - Run tests with coverage"
	@echo ""
	@echo "Other commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make clean        - Remove generated files"
	@echo ""
	@echo "Target: All functions CC < 6, MI > 70"

# Complete workflow (run before commit)
all: format check test
	@echo "✓ All quality checks passed!"

# Format code with Black
format:
	@echo "Formatting code with Black..."
	@black src/ scripts/ tests/
	@echo "✓ Code formatted"

# Run all checks
check: lint complexity type
	@echo "✓ All checks passed"

# Lint with Flake8
lint:
	@echo "Linting with Flake8..."
	@flake8 src/ scripts/ tests/
	@echo "✓ Linting passed"

# Check complexity with Radon
complexity:
	@echo "Checking cyclomatic complexity..."
	@echo "Target: CC < 6 (A grade)"
	@radon cc src/ scripts/ -a -s --total-average
	@echo ""
	@echo "Checking maintainability index..."
	@echo "Target: MI > 70"
	@radon mi src/ scripts/ -s
	@echo "✓ Complexity check complete"

# Type check with mypy
type:
	@echo "Type checking with mypy..."
	@mypy src/
	@echo "✓ Type checking passed"

# Run tests with coverage
test:
	@echo "Running tests with coverage..."
	@pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "✓ Tests passed"
	@echo ""
	@echo "Coverage report: htmlcov/index.html"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "✓ Cleaned"

# Quick check (fast, for during development)
quick: format lint
	@echo "✓ Quick check passed"

# Git pre-commit hook
pre-commit: format check
	@echo "✓ Ready to commit"
