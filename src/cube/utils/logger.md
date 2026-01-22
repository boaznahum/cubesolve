# Logger System Documentation

## Overview

The logging system provides centralized debug output control with prefix chaining.
All debug output flows through `Logger` instances created via `with_prefix()`.

## Architecture

```
                    Environment Variables
                    CUBE_QUIET_ALL / CUBE_DEBUG_ALL
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Logger (root)                                │
│  delegate=None → owns _quiet_all and _debug_all                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ with_prefix(prefix, debug_flag) → returns child Logger          ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │
              with_prefix("Solver:LBL", lambda: self._is_debug_enabled)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Logger (child)                                   │
│  delegate=parent, _root=parent._root (shares root's flags)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ _prefix     │  │ _debug_flag │  │ _level (filtering)          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    with_prefix("L1Cross")
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Logger (chained child)                           │
│  prefix = "Solver:LBL:L1Cross"                                       │
│  debug_flag inherited from parent                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `ILogger` | Protocol for all loggers |
| `IPrefixLogger` | Protocol extending ILogger with `set_prefix()` and `tab()` |
| `Logger` | Unified implementation (root and child loggers) |

## Logger Class

The unified `Logger` class handles both root and child roles:

```python
# Root logger (delegate=None)
root = Logger()  # owns _quiet_all, _debug_all

# Child logger (delegate=parent)
child = root.with_prefix("Solver")  # shares root's flags via _root reference

# Or create child directly
child = Logger(delegate=parent, prefix="Solver", debug_flag=lambda: True)
```

### Features

- **Prefix chaining**: `root.with_prefix("A").with_prefix("B")` → `"A:B:"`
- **Mutable prefix**: `logger.set_prefix("NewPrefix")` changes prefix dynamically
- **Debug flag callback**: Evaluated on each `debug()` call
- **Level filtering**: `set_level(N)`, messages with `level > N` are hidden
- **Indented sections**: `tab()` context manager for visual nesting

## Level-Based Debug

All debug methods support an optional `level` parameter for verbosity filtering:

| Method | Signature |
|--------|-----------|
| `set_level(level)` | Set threshold (messages with level <= threshold are shown) |
| `debug(..., level=N)` | Debug with optional level check (supports lazy args) |
| `is_debug(..., level=N)` | Check if debug at level would output |

### Level Inheritance

Levels inherit from parent logger if not set locally:
- `set_level(3)` - Use level 3 for this logger
- `set_level(None)` - Inherit from parent (default)

### Example Usage

```python
# Set up logger with level
logger = parent.with_prefix("NxNCenters")
logger.set_level(3)  # Only show level 1, 2, 3

# Use level-based debug (level is keyword-only parameter)
logger.debug(None, "important message", level=1)   # shown (1 <= 3)
logger.debug(None, "normal message", level=3)      # shown (3 <= 3)
logger.debug(None, "verbose detail", level=5)      # hidden (5 > 3)

# Guard expensive computations
if logger.is_debug(None, level=5):
    logger.debug(None, expensive_computation(), level=5)
```

### Migration from D_LEVEL Pattern

**Before (deprecated):**
```python
class NxNCenters(SolverHelper):
    D_LEVEL = 3

    def debug(self, *args, level=3):
        if level <= NxNCenters.D_LEVEL:
            super().debug("NxX Centers:", args)

    # Usage:
    self.debug("message", level=2)
```

**After (preferred):**
```python
class NxNCenters(SolverHelper):
    D_LEVEL = 3

    def __init__(self, slv):
        super().__init__(slv)
        self._logger.set_level(NxNCenters.D_LEVEL)

    # Usage (no custom debug() override needed):
    self._logger.debug(None, "message", level=2)
```

## How Prefix Chaining Works

```python
# Root logger (from ApplicationAndViewState)
root_logger = cube.sp.logger

# Solver creates prefixed logger with debug_flag
solver_logger = root_logger.with_prefix(
    "Solver:LBL",
    debug_flag=lambda: self._is_debug_enabled  # evaluated on each debug() call
)

# SolverHelper chains further
element_logger = solver_logger.with_prefix("L1Cross")  # inherits debug_flag

# Usage - pass None to use the logger's debug_flag
element_logger.debug(None, "solving...")
# Output: "DEBUG: Solver:LBL:L1Cross: solving..."
```

## Solver Logger Hierarchy

All solvers follow a **consistent parent-child logger pattern**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Root: cube.sp.logger                                                    │
│  (from ApplicationAndViewState, accessed via factory)                    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
             Solvers.lbl_big(op) passes op.cube.sp.logger
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LayerByLayerNxNSolver (prefix: "LBL")                                   │
│  self._logger = parent_logger.with_prefix("LBL", debug_flag=...)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
             shadow_solver = Solvers3x3.beginner(dual_op, self._logger)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  BeginnerSolver3x3 (prefix: "Beginner3x3")                               │
│  self._logger = parent_logger.with_prefix("Beginner3x3", debug_flag=...) │
│  Output: "LBL:Beginner3x3: message"                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Rules:
1. **`parent_logger` is REQUIRED** - never optional/None
2. **Root solvers** receive `op.cube.sp.logger` from factory
3. **Child solvers** receive `parent._logger`
4. Each solver creates its own logger with its own `debug_flag`

## AbstractSolver / AbstractReducer Pattern

Both **REQUIRE** `parent_logger` parameter in constructor:

```python
class AbstractSolver(Solver, ABC):
    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: ILogger,           # REQUIRED - never None
        logger_prefix: str | None = None,
    ) -> None:
        prefix = logger_prefix or "Solver"
        self.__logger = parent_logger.with_prefix(
            prefix,
            debug_flag=lambda: self._is_debug_enabled  # Each solver controls its own debug
        )

    @property
    def _logger(self) -> ILogger:
        return self.__logger

    def debug(self, *args) -> None:
        """DEPRECATED: Use self._logger.debug(None, ...) instead."""
        self._logger.debug(None, *args)
```

### Factory Pattern (Root Solvers)

Root solvers receive `op.cube.sp.logger` from the factory:

```python
# Solvers.py (factory)
class Solvers:
    @staticmethod
    def lbl_big(op: OperatorProtocol) -> Solver:
        parent_logger = op.cube.sp.logger  # Root logger
        return LayerByLayerNxNSolver(op, parent_logger)
```

### Child Solver Pattern

Child solvers receive `parent._logger`:

```python
# LayerByLayerNxNSolver.py
class LayerByLayerNxNSolver(AbstractSolver):
    def __init__(self, op: OperatorProtocol, parent_logger: ILogger) -> None:
        super().__init__(op, parent_logger, logger_prefix="LBL")

    def _solve_layer1_with_shadow(self, ...):
        # Child solver receives self._logger as parent
        shadow_solver = Solvers3x3.beginner(dual_op, self._logger)
        shadow_solver.solve_3x3()  # Debug output: "LBL:Beginner3x3: ..."
```

## SolverHelper Pattern

Uses `Logger` with mutable prefix (prefix is set dynamically):

```python
class SolverHelper(CubeSupplier):
    def __init__(self, solver: SolverElementsProvider) -> None:
        # Logger: prefix can be set later via _set_debug_prefix (uses set_prefix())
        self._logger: Logger = Logger(solver._logger)

    def _set_debug_prefix(self, prefix: str) -> None:
        """Set the debug prefix for this element's logger."""
        self._logger.set_prefix(prefix)

    def debug(self, *args) -> None:
        """DEPRECATED: Use self._logger.debug(None, ...) instead."""
        self._logger.debug(None, *args)
```

## Debug Flag Types

```python
DebugFlagType = bool | Callable[[], bool] | None
```

- `bool`: Static True/False
- `Callable[[], bool]`: Dynamic evaluation (e.g., `lambda: self._is_debug_enabled`)
- `None`: Inherit from parent or treat as False

## The `debug_on` Parameter

The first parameter to `debug()` is `debug_on`, which allows per-call control:

```python
# Signature:
def debug(self, debug_on: DebugFlagType, *args, level: int = 3) -> None

# Usage:
logger.debug(True, "always show this")   # Override: always show
logger.debug(False, "verbose detail")     # Override: only if debug_all
logger.debug(None, "normal message")      # Use logger's debug_flag (common case)
```

### `debug_on` Values:

| Value | Behavior |
|-------|----------|
| `True` | **Always show** (unless `quiet_all`) - for important messages |
| `False` | **Only if `debug_all`** - for verbose details |
| `None` | **Use logger's `debug_flag`** - the common case |

### Use Cases:

```python
# Important progress message - always show
logger.debug(True, "Phase 1 complete, starting phase 2")

# Verbose loop details - only in full debug mode
for i, item in enumerate(items):
    logger.debug(False, f"Processing item {i}: {item}")

# Normal debug message - uses inherited flag
logger.debug(None, "Checking orientation...")
```

## Debug Control Flow

Complete flow when `logger.debug(debug_on, *args)` is called:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ logger.debug(debug_on, "message")                                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 1: Check `quiet_all` (environment: CUBE_QUIET_ALL)                  │
│         If True → SUPPRESS (no output)                                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ quiet_all is False
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 2: Resolve `debug_on` parameter                                     │
│         debug_on=True  → effective_flag = True                           │
│         debug_on=False → effective_flag = _debug_all (env var)           │
│         debug_on=None  → effective_flag = evaluate logger's _debug_flag  │
│                          (typically lambda: self._is_debug_enabled)      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 3: Check effective_flag                                             │
│         If False → SUPPRESS (no output)                                  │
│         If True  → CHECK LEVEL                                           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ effective_flag is True
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 4: Check level (if provided)                                        │
│         message level > logger level → SUPPRESS                          │
│         message level <= logger level → OUTPUT                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Where `_is_debug_enabled` Comes From (Solvers):

```python
# AbstractSolver
@property
def _is_debug_enabled(self) -> bool:
    if self._debug_override is not None:
        return self._debug_override     # Temporary override during solve
    return self._cube.config.solver_debug  # GUI toggle (Ctrl+O)
```

This callback is captured when creating the logger:
```python
self.__logger = parent_logger.with_prefix(
    prefix,
    debug_flag=lambda: self._is_debug_enabled  # Evaluated on each debug() call
)
```

## Two Debug Control Systems

### 1. Logger Flags (`quiet_all` / `debug_all`)

Global on/off switches owned by root Logger:
- Set at startup or via environment variables
- `quiet_all` suppresses ALL debug output
- `debug_all` enables ALL debug output

### 2. Config Flag (`solver_debug`)

Per-feature toggle in `_config.py`:
- Toggled via Ctrl+O in GUI
- Passed via `debug_flag` callback to Logger

### How They Interact

The `debug_flag` callback (e.g., `lambda: self._is_debug_enabled`) reads from config:

```python
# AbstractSolver
@property
def _is_debug_enabled(self) -> bool:
    if self._debug_override is None:
        return self._cube.config.solver_debug  # GUI toggle (Ctrl+O)
    return self._debug_override
```

### Decision Table

| `quiet_all` | `debug_all` | `debug_flag()` | Output? |
|-------------|-------------|----------------|---------|
| True | * | * | **No** (quiet_all wins) |
| False | True | * | **Yes** (debug_all enables all) |
| False | False | True | **Yes** (debug_flag enables) |
| False | False | False | **No** |

## Indented Sections

Use `tab()` for visually nested debug output:

```python
logger = Logger(parent)
logger.set_prefix("MyComponent")

with logger.tab(lambda: "Processing slice 1"):
    logger.debug(None, "nested message")
    with logger.tab(lambda: "Source face"):
        logger.debug(None, "deeper nested")

# Output:
# DEBUG: MyComponent: ── Processing slice 1 ──
# DEBUG: MyComponent:│  nested message
# DEBUG: MyComponent:│  ── Source face ──
# DEBUG: MyComponent:│  │  deeper nested
# DEBUG: MyComponent:│  ── end: Source face ──
# DEBUG: MyComponent: ── end: Processing slice 1 ──
```

## Usage

### For Solver Components

```python
# Use self._logger directly (preferred)
self._logger.debug(None, "message")  # Uses logger's debug_flag

# Or use deprecated helper (for backward compatibility)
self.debug("message")
```

### For Lazy Evaluation

```python
# Only evaluates expensive_computation() if debug is enabled
# debug() accepts callables that are resolved only when debug is enabled
self._logger.debug(None, lambda: expensive_computation())
self._logger.debug(None, "Result:", lambda: expensive_computation())
```

## Environment Variables

| Variable | Effect |
|----------|--------|
| `CUBE_QUIET_ALL=1` | Suppress ALL debug output (overrides everything) |
| `CUBE_DEBUG_ALL=1` | Enable ALL debug output (unless quiet_all is set) |

Values accepted: `1`, `true`, `yes` (case-insensitive)

## Files

| File | Purpose |
|------|---------|
| `src/cube/utils/logger_protocol.py` | `ILogger`, `IPrefixLogger`, `DebugFlagType` |
| `src/cube/utils/prefixed_logger.py` | Unified `Logger` implementation |
| `src/cube/application/Logger.py` | Re-export for backwards compatibility |
| `src/cube/application/state.py` | `ApplicationAndViewState` creates root Logger |

## Migration Guide

### Before (deprecated)
```python
self.debug("message")  # Calls internal debug() method
```

### After (preferred)
```python
self._logger.debug(None, "message")  # Direct logger call
```

The `debug()` methods are kept for backward compatibility but marked as DEPRECATED.
