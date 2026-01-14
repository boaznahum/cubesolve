# Logger System Documentation

## Overview

The logging system provides centralized debug output control with prefix chaining.
All debug output flows through `ILogger` instances created via `with_prefix()`.

## Architecture

```
                    Environment Variables
                    CUBE_QUIET_ALL / CUBE_DEBUG_ALL
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Logger (root)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ _quiet_all  │  │ _debug_all  │  │ with_prefix(prefix, flag)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
              with_prefix("Solver:LBL", lambda: self._is_debug_enabled)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PrefixedLogger                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ _delegate   │  │ _prefix     │  │ _debug_flag (callable)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    with_prefix("L1Cross")
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PrefixedLogger (chained)                         │
│  prefix = "Solver:LBL:L1Cross"                                       │
│  debug_flag inherited from parent                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `ILogger` | Protocol for all loggers |
| `IPrefixLogger` | Protocol extending ILogger with `set_prefix()` |
| `Logger` | Root logger implementation |
| `PrefixedLogger` | Wrapper that adds prefix and optional debug_flag |
| `MutablePrefixLogger` | Wrapper with prefix that can be set later |

## Level-Based Debug

All debug methods support an optional `level` parameter for verbosity filtering:

| Method | Signature |
|--------|-----------|
| `set_level(level)` | Set threshold (messages with level <= threshold are shown) |
| `debug(..., level=N)` | Debug with optional level check |
| `debug_lazy(..., level=N)` | Lazy debug with optional level check |
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
class NxNCenters(SolverElement):
    D_LEVEL = 3

    def debug(self, *args, level=3):
        if level <= NxNCenters.D_LEVEL:
            super().debug("NxX Centers:", args)

    # Usage:
    self.debug("message", level=2)
```

**After (preferred):**
```python
class NxNCenters(SolverElement):
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

# SolverElement chains further
element_logger = solver_logger.with_prefix("L1Cross")  # inherits debug_flag

# Usage - pass None to use the logger's debug_flag
element_logger.debug(None, "solving...")
# Output: "DEBUG: Solver:LBL:L1Cross: solving..."
```

## AbstractSolver / AbstractReducer Pattern

Both accept `logger_prefix: str | None` in constructor:

```python
class AbstractSolver(Solver, ABC):
    def __init__(self, op: OperatorProtocol, logger_prefix: str | None = None) -> None:
        prefix = logger_prefix or "Solver"
        self.__logger = self._cube.sp.logger.with_prefix(
            prefix,
            debug_flag=lambda: self._is_debug_enabled
        )

    @property
    def _logger(self) -> ILogger:
        return self.__logger

    def debug(self, *args) -> None:
        """DEPRECATED: Use self._logger.debug(None, ...) instead."""
        self._logger.debug(None, *args)
```

Subclass passes prefix explicitly:
```python
class NxNSolverOrchestrator(AbstractSolver):
    def __init__(self, op, reducer, solver_3x3, solver_name):
        super().__init__(op, logger_prefix=f"Solver:{solver_name.display_name}")
```

## SolverElement Pattern

Uses `MutablePrefixLogger` because prefix is set dynamically:

```python
class SolverElement(CubeSupplier):
    def __init__(self, solver: SolverElementsProvider) -> None:
        # MutablePrefixLogger: prefix can be set later via _set_debug_prefix
        self._logger: MutablePrefixLogger = MutablePrefixLogger(solver._logger)

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

## Two Debug Control Systems

### 1. Logger Flags (`quiet_all` / `debug_all`)

Global on/off switches in `Logger`:
- Set at startup or via environment variables
- `quiet_all` suppresses ALL debug output
- `debug_all` enables ALL debug output

### 2. Config Flag (`solver_debug`)

Per-feature toggle in `_config.py`:
- Toggled via Ctrl+O in GUI
- Passed via `debug_flag` callback to PrefixedLogger

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
self._logger.debug_lazy(None, lambda: expensive_computation())
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
| `src/cube/utils/prefixed_logger.py` | `PrefixedLogger`, `MutablePrefixLogger` |
| `src/cube/application/Logger.py` | Root `Logger` implementation |
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
