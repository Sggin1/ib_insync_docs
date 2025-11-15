# Coding Standards - ib_insync Deduplication Project

**Version:** 1.0
**Last Updated:** 2025-11-15

---

## Core Principles

### 1. KISS - Keep It Simple, Stupid
- Favor simplicity over cleverness
- Write code that's easy to understand
- Avoid unnecessary abstractions
- Clear > Concise

### 2. Low Complexity
- **CC < 6**: Cyclomatic Complexity under 6 per function
- **CC < 12**: Acceptable temporarily, but refactor soon
- **MI > 70**: Maintainability Index above 70
- Target: All blocks have complexity A (average 1.0)

### 3. Flat Structure
- Minimal nesting (max 3 levels)
- Direct access to modules
- No deep hierarchies
- Use PEP 420 Namespace Packages (no `__init__.py`)

### 4. Single Source of Truth
- No duplicate state
- Clear data ownership
- Single responsibility per module
- Delegate pattern for cross-module communication

### 5. UTF-8 Encoding
- All files use UTF-8 encoding
- Explicit encoding in file operations

---

## File Structure

### Standard File Header

```python
# File: module_name.py
# Location: dedup/src/module_name.py
# Purpose: Brief description of module purpose
# Dependencies: pydantic, anthropic

"""
Module-level docstring using Google style.

This module provides functionality for X, Y, and Z.
It follows the delegate pattern and maintains single source of truth.

Example:
    Basic usage example here
"""
```

### Size Limits (Soft)

- **200 lines per file** (soft limit)
- **3 nesting levels** (maximum)
- **25 lines per function** (target)

### Module Organization

```
dedup/
├── src/                    # Source code (PEP 420 namespace)
│   ├── models.py           # Data models only
│   ├── extractors.py       # Extraction logic only
│   ├── embeddings.py       # Embedding generation only
│   ├── clustering.py       # Clustering logic only
│   ├── ai_merger.py        # AI merging logic only
│   ├── builders.py         # Database building only
│   └── validators.py       # Validation logic only
│
├── scripts/                # Executable scripts
│   └── *.py                # Pipeline stages
│
└── tests/                  # Tests (PEP 420 namespace)
    └── test_*.py           # Test modules
```

---

## Code Style

### Formatting

**Tool:** Black (opinionated formatter)

```bash
# Format all files
black .

# Check without writing
black --check .
```

**Configuration:** Use defaults (88 char line length)

### Docstrings

**Style:** Google-style docstrings

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief one-line summary.

    Longer description if needed. Explain what the function does,
    not how it does it. Focus on the contract.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Type Hints

**Required** for all function signatures:

```python
# Good
def process_data(input: str, limit: int = 10) -> list[dict]:
    pass

# Bad
def process_data(input, limit=10):
    pass
```

---

## Complexity Management

### Cyclomatic Complexity (CC)

**Target: CC < 6** for every function

**Measure with Radon:**

```bash
# Check complexity
radon cc . -a -s

# Show only high complexity (B or worse)
radon cc . -nb
```

**Complexity Grades:**
- **A (1-5)**: Simple, good ✓
- **B (6-10)**: More complex, acceptable
- **C (11-20)**: Too complex, refactor
- **D (21-50)**: Way too complex, refactor immediately
- **F (>50)**: Unmaintainable

### Reducing Complexity

**Techniques:**

1. **Extract functions**
   ```python
   # Bad (CC = 8)
   def process(data):
       if condition1:
           if condition2:
               if condition3:
                   # nested logic

   # Good (CC = 2 per function)
   def process(data):
       if not should_process(data):
           return
       return do_process(data)

   def should_process(data):
       return condition1 and condition2 and condition3
   ```

2. **Use guard clauses**
   ```python
   # Bad
   def process(data):
       if data:
           if valid(data):
               return result

   # Good
   def process(data):
       if not data:
           return None
       if not valid(data):
           return None
       return result
   ```

3. **Replace conditionals with polymorphism/dispatch**
   ```python
   # Bad
   def process(type, data):
       if type == "A":
           # logic A
       elif type == "B":
           # logic B
       elif type == "C":
           # logic C

   # Good
   PROCESSORS = {
       "A": process_a,
       "B": process_b,
       "C": process_c,
   }

   def process(type, data):
       processor = PROCESSORS.get(type)
       if processor:
           return processor(data)
   ```

### Maintainability Index (MI)

**Target: MI > 70**

**Measure with Radon:**

```bash
# Check maintainability
radon mi . -s
```

**MI Grades:**
- **A (>= 80)**: Highly maintainable ✓
- **B (65-79)**: Maintainable
- **C (50-64)**: Moderately maintainable, improve
- **D (< 50)**: Hard to maintain, refactor

---

## Communication Patterns

### Delegate Pattern

**No direct imports between domain modules**

```python
# Bad (tight coupling)
from dedup.src.extractors import extract_code
from dedup.src.embeddings import generate_embedding

def process():
    code = extract_code(...)
    embedding = generate_embedding(code)

# Good (delegate pattern)
class Pipeline:
    def __init__(self, extractor, embedder):
        self.extractor = extractor
        self.embedder = embedder

    def process(self):
        code = self.extractor.extract(...)
        embedding = self.embedder.generate(code)

# Usage
pipeline = Pipeline(
    extractor=Extractor(),
    embedder=Embedder()
)
```

### Single Source of Truth

**Data flows one direction, no circular dependencies**

```
Source Files → Extractor → Embedder → Clusterer → Merger → Builder → Database
     ↓             ↓           ↓           ↓          ↓         ↓        ↓
   models.py   models.py   models.py   models.py  models.py models.py models.py
```

**Each module:**
- Owns its output
- Doesn't modify inputs
- Returns new data structures
- No shared mutable state

---

## Linting

### Tool: Flake8

```bash
# Lint all files
flake8 .

# Show statistics
flake8 --statistics .
```

### Configuration

Create `.flake8` in project root:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    outputs,
    logs,
    venv,
    .venv
```

**Key Rules:**
- Max line length: 88 (Black default)
- Ignore E203 (whitespace before ':' - conflicts with Black)
- Ignore W503 (line break before binary operator - outdated)

---

## Type Checking

### Tool: mypy

```bash
# Type check all files
mypy dedup/src

# Strict mode
mypy --strict dedup/src
```

### Configuration

Create `mypy.ini`:

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
```

---

## Daily Workflow

### Pre-commit Checklist

```bash
# 1. Format code
black .

# 2. Check complexity
radon cc . -a -s

# 3. Lint
flake8 .

# 4. Type check
mypy dedup/src

# 5. Run tests
pytest

# 6. Git commit
git add .
git commit -m "descriptive message"
```

### Complexity Review

**Before committing:**

1. Check all modified files have CC < 6
2. Refactor any B-grade or worse functions
3. Ensure MI > 70 for all modules

**Command:**
```bash
# Check only git-staged files
git diff --name-only --cached | grep '\.py$' | xargs radon cc -s
```

---

## Testing

### Test Organization

```python
# File: test_extractors.py
# Location: dedup/tests/test_extractors.py
# Purpose: Test extraction functionality
# Dependencies: pytest

"""
Tests for extractors module.

Tests cover:
- Code block extraction
- API method identification
- Source location tracking
"""

import pytest
from dedup.src import extractors


def test_extract_code_block():
    """Test basic code block extraction."""
    # Arrange
    markdown = "```python\nprint('hello')\n```"

    # Act
    result = extractors.extract_code_blocks(markdown)

    # Assert
    assert len(result) == 1
    assert result[0].code == "print('hello')"
```

### Test Coverage

**Target: >80% coverage**

```bash
# Run with coverage
pytest --cov=dedup/src --cov-report=html

# View report
open htmlcov/index.html
```

---

## Dependencies

### Core Dependencies

From `requirements.txt`:

```python
# Data models
from pydantic import BaseModel, Field

# Embeddings
from sentence_transformers import SentenceTransformer

# Clustering
from sklearn.cluster import DBSCAN

# AI integration
from anthropic import Anthropic
```

### Import Style

```python
# Good: Explicit imports
from pathlib import Path
from typing import Optional, List

# Bad: Star imports
from typing import *
```

### Import Order

1. Standard library
2. Third-party libraries
3. Local modules

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np
from pydantic import BaseModel

# Local
from dedup.src import models
```

---

## Error Handling

### Explicit Error Types

```python
# Good
def process_file(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    # ... process

# Bad
def process_file(path):
    if not path.exists():
        raise Exception("Error!")
```

### Fail Fast

```python
# Good
def process(data: dict) -> str:
    if not data:
        raise ValueError("Data cannot be empty")
    if "key" not in data:
        raise KeyError("Required key 'key' not found")

    return data["key"].upper()

# Bad
def process(data):
    try:
        return data["key"].upper()
    except:
        return None
```

---

## Performance

### Profile Before Optimizing

```bash
# Profile script
python -m cProfile -o output.prof scripts/01_extract.py

# View results
python -m pstats output.prof
```

### Complexity Targets for Performance

- File operations: O(n) acceptable
- Similarity matrix: O(n²) acceptable for n < 1000
- Clustering: O(n log n) preferred

---

## Documentation

### Module Documentation

Every module needs:
1. File header with metadata
2. Module-level docstring
3. Function docstrings (Google style)
4. Complex logic explained in comments

### Inline Comments

```python
# Good: Explain WHY
# Use cosine similarity because euclidean doesn't work well for high-dimensional sparse vectors
similarity = cosine_similarity(a, b)

# Bad: Explain WHAT (code already shows this)
# Calculate similarity
similarity = cosine_similarity(a, b)
```

---

## Git Practices

### Commit Messages

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- feat: New feature
- fix: Bug fix
- refactor: Code refactoring
- docs: Documentation
- test: Tests
- chore: Maintenance

**Example:**
```
feat: Add code block extraction

Implement markdown parsing to extract code blocks with
context. Supports Python, bash, and JavaScript.

Complexity: All functions CC < 4
Tests: 95% coverage
```

### Branch Naming

Follow the pattern: `claude/<descriptive-name>-<session-id>`

---

## Code Review Checklist

Before marking code as done:

- [ ] All functions have CC < 6
- [ ] Module has MI > 70
- [ ] Black formatting applied
- [ ] Flake8 passes with no errors
- [ ] mypy passes with no errors
- [ ] All functions have docstrings
- [ ] All public functions have type hints
- [ ] Tests written and passing
- [ ] No `# TODO` or `# FIXME` comments
- [ ] Documentation updated

---

## Tools Summary

| Tool | Purpose | Command |
|------|---------|---------|
| **black** | Code formatting | `black .` |
| **radon** | Complexity analysis | `radon cc . -a -s` |
| **flake8** | Linting | `flake8 .` |
| **mypy** | Type checking | `mypy dedup/src` |
| **pytest** | Testing | `pytest --cov` |

---

## References

- [PEP 420 - Namespace Packages](https://www.python.org/dev/peps/pep-0420/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Cyclomatic Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Radon Documentation](https://radon.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)

---

**Remember:** Simple code is better than clever code. If you can't explain it simply, refactor it.
