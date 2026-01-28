# Coding Conventions

**Analysis Date:** 2026-01-28

## Naming Patterns

**Files:**
- PascalCase for classes and modules: `Cube.py`, `Operator.py`, `Part.py`, `PygletRenderer.py`
- snake_case for utility/helper modules: `op_annotation.py`, `config_impl.py`, `test_utils.py`
- Private/internal modules prefixed with underscore: `_part.py`, `_elements.py`
- Directory names in snake_case: `presentation/`, `application/`, `domain/`

**Functions:**
- snake_case for all function/method names: `get_all_parts()`, `play()`, `execute_keys()`, `skip_if_not_supported()`
- Private methods prefixed with single underscore: `_play()`, `_handle_key()`, `_reset()`
- Properties use lowercase without underscores: `@property def solved(self)`

**Variables:**
- snake_case for local variables: `all_slices`, `cube_size`, `scramble_alg`, `event_loop`
- Private attributes use single leading underscore: `_cube`, `_history`, `_animation_manager`
- Constants in UPPER_SNAKE_CASE: `DEFAULT_KEY_MAPPING`, `GUI_SCRAMBLE_SEEDS`, `CUBE_SIZES`
- Loop variables: `s`, `i`, `part` (short names acceptable in tight loops)

**Types:**
- PascalCase for classes: `Cube`, `Part`, `Edge`, `Corner`, `Center`
- PascalCase for Enum classes: `SolverName`, `FaceName`, `Color`, `Keys`
- TypeVar names use `T` prefix: `TPartType`, `_TPartType`
- Protocol classes explicitly inherit from `Protocol` and use PascalCase: `CubeSupplier`, `OperatorProtocol`

## Code Style

**Formatting:**
- No explicit formatter configured (ruff check used without format config in pyproject.toml)
- Line length: No explicit limit, but keep reasonable (80-120 chars typical)
- Indentation: 4 spaces (standard Python)

**Linting:**
- Tool: `ruff` (no custom config in pyproject.toml)
- Run with: `python -m ruff check src/cube`
- Auto-fix with: `ruff check --fix`
- Enforce with pre-commit checks before git

**Type Checking:**
- Tool: `mypy` and `pyright` (both required to pass)
- mypy config in pyproject.toml: strict mode enabled
- pyright mode: `standard` (strict type checking)
- All files must use complete type annotations

## Import Organization

**Order:**
1. Future imports: `from __future__ import annotations` (at top of most files)
2. Standard library: `import sys`, `from collections.abc import ...`
3. Third-party: `import pytest`, `from pyglet import ...`
4. Local application: `from cube.domain.model.Cube import Cube`
5. Relative imports: `from ...utils.service_provider import IServiceProvider`

**Path Aliases:**
- No import path aliases configured
- Use full absolute imports: `from cube.application.commands.Operator import Operator`
- Avoid relative imports for cross-module imports (use for intra-package)

**Re-exports and __all__:**
- Many modules define `__all__` to control public API: `__all__ = ['Operator', 'DualOperator']`
- Backward compatibility re-exports: See `app_exceptions.py` which re-exports domain exceptions
- Check existing `__all__` definitions before adding new exports

## Error Handling

**Patterns:**
- Raise domain-specific exceptions: `InternalSWError`, `OpAborted`, `EvenCubeCornerSwapException`
- Exceptions organized by layer:
  - Domain: `cube.domain.exceptions.*` (no dependencies on other layers)
  - Application: `cube.application.exceptions.*` (re-exports domain exceptions)
- Do NOT use generic `Exception` or bare `raise` - use specific exception types

**Exception Classes:**
- File: `src/cube/domain/exceptions/` and `src/cube/application/exceptions/`
- Naming: PascalCase with `Exception` suffix: `InternalSWError`, `OpAborted`
- Example: `src/cube/domain/exceptions/InternalSWError.py` (one class per file)
- Always provide context in exception messages

**Error Detection:**
- Type checking catches errors at write time (mypy/pyright)
- Example: `PartSlice` vs `Part` confusion caught by type annotations (no `position_id` on slices)

## Logging

**Framework:** No `logging` module used
- Use `print()` for simple output: `print(f"Backend: {backend_name}")`
- Use application-level `Logger` from `cube.application.Logger`
- Log files optional, configured via app state: `_log_path`

**Patterns:**
- Debug output routed through `cube_state.debug()` calls
- Silent mode via environment variable: `CUBE_QUIET_ALL=1`
- Print statements acceptable for one-off debug in main entry points
- Operation logging goes to optional file via `Operator.log()`

## Comments

**When to Comment:**
- Class docstrings: Always (multi-line format with Args/Returns for complex classes)
- Method docstrings: For public methods and anything non-obvious
- Inline comments: Explain the "why", not the "what" (code should be readable)
- TODO/FIXME: Use with issue numbers when possible: `# TODO [#9]: Move single step mode`

**JSDoc/TSDoc:**
- Use Google-style docstrings for classes and methods
- Example from `Cube.py`:
```python
class Cube(CubeSupplier):
    """
    Virtual Rubik's Cube supporting NxN sizes (3x3, 4x4, 5x5, etc.).

    Parameters
    ----------
    size : int
        The cube size (3 for 3x3, 4 for 4x4, etc.). Must be >= 2.

    Attributes
    ----------
    front, back, left, right, up, down : Face
        The six faces of the cube.
    """
```

- Dataclass docstring example from `CubeTestDriver`:
```python
@dataclass
class CubeTestDriver:
    """Abstract test driver for cube operations with any GUI backend.

    Provides a clean interface for testing cube operations without
    manually handling key-to-algorithm conversion in each test.

    Usage:
        def test_rotation(cube_driver):
            cube_driver.execute("RLU")
            assert not cube_driver.cube.solved
    """
```

## Function Design

**Size:**
- Aim for 10-40 lines for most functions
- Larger functions OK if well-structured (see `Operator._play()` ~150 lines with clear sections)
- Private methods can be more concise

**Parameters:**
- Use type hints on all parameters
- Order: required first, then optional
- Default values for optional parameters
- Use dataclasses for parameter objects (see `CubeTestDriver`)

**Return Values:**
- All functions must have return type annotation
- Use `-> None` for void functions
- Use `Optional[T]` or `T | None` for nullable returns (Python 3.10+)
- Use `Iterator[T]` for generators: `def all_slices(self) -> Iterator[PartSlice]`

**Chaining Pattern:**
- Methods returning `self` for fluent interface:
```python
def execute(self, sequence: str) -> "CubeTestDriver":
    # ... code ...
    return self

# Usage:
cube_driver.execute("R").execute("L").solve()
```

## Module Design

**Exports:**
- Explicitly define `__all__` for public APIs: `__all__ = ['Cube', 'Face', 'Part']`
- Private classes/functions: Start with underscore, don't add to `__all__`
- Re-export pattern: Use for backward compatibility (see `app_exceptions.py`)

**Barrel Files:**
- `__init__.py` files use barrel pattern to re-export:
```python
# cube/domain/exceptions/__init__.py
from cube.domain.exceptions.InternalSWError import InternalSWError
__all__ = ['InternalSWError', 'OpAborted', ...]
```

**Lazy Imports:**
- Use `TYPE_CHECKING` for circular import prevention:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cube.application.commands.op_annotation import OpAnnotation
    from ..animation.AnimationManager import AnimationManager
```

## Special Conventions

**Abstract Base Classes:**
- Use `ABC` and `@abstractmethod` for contracts
- Example: `class Part(ABC, CubeElement)` with `@abstractmethod def all_slices()`

**Protocols:**
- Use `Protocol` for structural typing (duck typing)
- Example: `class CubeSupplier(Protocol)` with `def cube(self) -> Cube`
- Good for testing and backends

**Generics:**
- Use `Generic[T]` for type parameters
- Example: `class PartSlice(ABC, Generic[_TPartType], Hashable)`
- Type variables: `TPartType = TypeVar("TPartType", bound="Part")`

**Slots:**
- Use `__slots__` in domain classes for memory efficiency
- Example: `__slots__ = ["_cube", "_fixed_id", "_colors_id_by_pos"]`
- Improves performance for frequently-instantiated classes

**Dataclasses:**
- Use `@dataclass` for value objects and test fixtures
- Example: `@dataclass class CubeTestDriver` with field initialization
- Use `field(default_factory=...)` for mutable defaults

**Deprecated Methods:**
- Mark with `@deprecated("Use X instead")` from `typing_extensions`
- Example: `@deprecated("Use play() instead") def op(self, ...)`
- Still implement the method (don't remove)
- Emit `DeprecationWarning` when called

---

*Convention analysis: 2026-01-28*
