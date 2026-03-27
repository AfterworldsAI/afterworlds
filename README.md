# Afterworlds

Afterworlds is an interactive storytelling platform built on the Sojourn Story State Machine. It lets users inhabit and continue narrative worlds across three modes: RPG, Branching, and Writing. The target users are called Sojourners. This is a solo-developer project operated under AfterworldsAI, LLC.

## Local Development Setup

**Requirements:** Python 3.12, pip, virtualenv

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install the package and all dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/

# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Dependency audit
pip-audit
```

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```
