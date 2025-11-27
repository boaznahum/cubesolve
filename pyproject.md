# Project Setup with pyproject.toml

This project uses `pyproject.toml` (PEP 621) for all configuration - the modern Python standard.

## Installing

```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate it (Linux/Mac)
source .venv/bin/activate

# Install the package in editable mode
pip install -e .

# For development (includes pytest, mypy, pyright)
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest              # Run all tests (excludes slow and GUI by default)
pytest -v           # Verbose output
pytest -m ""        # Include slow tests
pytest tests/test_cube.py   # Specific file
```

## Type Checking

```bash
mypy cube
pyright
```

## Dependencies

### Runtime dependencies

| Dependency | Purpose |
|------------|---------|
| `pyglet>=1.5.0` | OpenGL-based 3D graphics and windowing for cube visualization |
| `numpy` | Efficient array operations for cube state manipulation |
| `PyYAML` | Configuration file parsing |

### Dev dependencies (`pip install -e ".[dev]"`)

| Dependency | Purpose |
|------------|---------|
| `pytest` | Test framework |
| `mypy` | Static type checker |
| `pyright` | Alternative type checker |
| `types-colorama` | Type stubs for colorama |
| `types-keyboard` | Type stubs for keyboard |

## Project Layout

This project uses the **flat layout** (package directly in root, no `src/` directory).
Both flat and src layouts are valid - see the Python Packaging Authority guide:
https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/

## Why pyproject.toml?

`pyproject.toml` is the modern Python standard (PEP 517/518/621) that consolidates:

| Old File | New Location in pyproject.toml |
|----------|-------------------------------|
| `setup.py` | `[build-system]` and `[project]` |
| `setup.cfg` | `[project]` |
| `requirements.txt` | `dependencies` and `optional-dependencies` |
| `pytest.ini` | `[tool.pytest.ini_options]` |
| `mypy.ini` | `[tool.mypy]` |

All configuration in one file!
