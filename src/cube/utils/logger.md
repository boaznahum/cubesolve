# Logger System Documentation

## Overview

The logging system uses Python's standard `logging` module with a thin
`CubeLogger(logging.Logger)` subclass.  Only two custom extensions exist:

- `tab()` — context manager for indented debug sections
- `makeRecord()` — auto-injects indentation into every log record

Everything else (levels, handlers, filters, hierarchy) is pure standard
`logging`.

## Architecture

```
logging.setLoggerClass(CubeLogger)

                    Environment Variables
                    CUBE_QUIET_ALL / CUBE_DEBUG_ALL
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CubeLogger (root, name="cube")                                      │
│  Created by setup_root_logger()                                       │
│  Owns: _quiet_all, _debug_all, console handler                       │
│  Level: DEBUG_ALL_ONLY (5) — passes everything to handlers           │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                          getChild("LBL")
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CubeLogger (name="cube.LBL")                                        │
│  Level: NOTSET → inherits from root                                   │
│  When solve(debug=True): setLevel(DEBUG)                              │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                          getChild("L1Cross")
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CubeLogger (name="cube.LBL.L1Cross")                                │
│  tab() → indented output                                              │
│  set_cube_level(3) → verbosity filter                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `CubeLogger` | `logging.Logger` subclass with `tab()` and `makeRecord()` |
| `ColonPrefixFormatter` | Converts `cube.LBL.L1Cross` → `DEBUG: LBL:L1Cross:` |
| `_CubeLevelFilter` | Filters by optional `cube_level` attribute (1-5) |

## Root Logger Setup

```python
from cube.utils.logger import setup_root_logger

root = setup_root_logger(debug_all=False, quiet_all=False)
# Returns CubeLogger named "cube" with console handler
```

## Debug Level Control

Debug is controlled by standard `logging` levels:

| State | Root level | Effect |
|-------|-----------|--------|
| Normal | INFO (20) | No debug output |
| `config.solver_debug = True` | Set by app | `DEBUG` messages visible |
| `quiet_all` | N/A | `isEnabledFor()` blocks everything below ERROR |
| `debug_all` | N/A | `isEnabledFor()` allows everything |

### Solver Debug via `solve()`

```python
# AbstractSolver.solve() sets logger level:
solve(debug=True)   # → self._logger.setLevel(DEBUG)
solve(debug=False)  # → self._logger.setLevel(INFO)
solve(debug=None)   # → inherit from root (NOTSET)
```

### DEBUG_ALL_ONLY Level

A custom level (5) below DEBUG (10) for messages that should only appear
with `--debug-all`:

```python
from cube.utils.std_logging import DEBUG_ALL_ONLY

# Application-level "verbose" debug:
logger.log(DEBUG_ALL_ONLY, "only visible with --debug-all")

# Normal debug:
logger.debug("visible when solver debug is on")
```

### Decision Table

| `quiet_all` | `debug_all` | Logger level | `logger.debug("msg")` | `logger.log(DEBUG_ALL_ONLY, "msg")` |
|-------------|-------------|-------------|------------------------|-------------------------------------|
| True | * | * | **Suppressed** | **Suppressed** |
| False | True | * | **Shown** | **Shown** |
| False | False | DEBUG | **Shown** | Suppressed |
| False | False | INFO | Suppressed | Suppressed |

## Cube-Level Filtering (1-5 Verbosity)

For fine-grained verbosity within DEBUG, use `set_cube_level()`:

```python
self._logger.set_cube_level(3)  # Only show cube_level <= 3

# In SolverHelper.debug():
self.debug("important", level=1)   # Shown (1 <= 3)
self.debug("normal", level=3)      # Shown (3 <= 3)
self.debug("verbose", level=5)     # Hidden (5 > 3)
```

Only 5 solver classes use this (NxNCenters, NxNEdges, E2ECommutator,
_LBLNxNEdges, _LBLL3Edges).

## Indented Sections

```python
with self._logger.tab("Processing slice 1"):
    self._logger.debug("nested message")
    with self._logger.tab("Source face"):
        self._logger.debug("deeper nested")

# Output:
# DEBUG: LBL:L1Cross: ── Processing slice 1 ──
# DEBUG: LBL:L1Cross:│  nested message
# DEBUG: LBL:L1Cross:│  ── Source face ──
# DEBUG: LBL:L1Cross:│  │  deeper nested
# DEBUG: LBL:L1Cross:│  ── end: Source face ──
# DEBUG: LBL:L1Cross: ── end: Processing slice 1 ──
```

## Solver Logger Hierarchy

### AbstractSolver

```python
class AbstractSolver(Solver, ABC):
    def __init__(self, op, parent_logger: CubeLogger, logger_prefix=None):
        prefix = logger_prefix or "Solver"
        self.__logger = parent_logger.getChild(prefix)

    def debug(self, *args):
        """Resolve lazy args and log at DEBUG level."""
        if not self.__logger.isEnabledFor(logging.DEBUG):
            return
        resolved = [_resolve_arg(a) for a in args]
        self.__logger.debug(" ".join(str(a) for a in resolved))
```

### SolverHelper

```python
class SolverHelper:
    def __init__(self, solver, debug_prefix):
        self.__logger = solver._logger.getChild(debug_prefix)

    def debug(self, *args, level=None):
        """Resolve lazy args with optional cube-level filtering."""
        ...
```

### Factory Pattern

```python
# Root solvers receive the root cube logger:
class Solvers:
    @staticmethod
    def lbl_big(op):
        parent_logger = op.cube.sp.logger  # Root CubeLogger
        return LayerByLayerNxNSolver(op, parent_logger)

# Child solvers receive parent's logger:
shadow_solver = Solvers3x3.beginner(dual_op, self._logger)
```

## Lazy Argument Resolution

```python
# Callables are resolved only when debug is enabled:
self.debug("Result:", lambda: expensive_computation())

# Implemented in AbstractSolver.debug() / SolverHelper.debug():
if not logger.isEnabledFor(DEBUG):
    return  # Lambda never called
resolved = [_resolve_arg(a) for a in args]
```

## Stream Callbacks

Legacy API for routing formatted log lines to callbacks:

```python
logger.add_stream(buffer.append)   # Register
logger.remove_stream(buffer.append) # Unregister
```

Internally wraps the callback as a `logging.Handler`.

## Environment Variables

| Variable | Effect |
|----------|--------|
| `CUBE_QUIET_ALL=1` | Suppress ALL debug output (errors still pass) |
| `CUBE_DEBUG_ALL=1` | Enable ALL debug output including DEBUG_ALL_ONLY |

## Files

| File | Purpose |
|------|---------|
| `src/cube/utils/logger.py` | `CubeLogger`, `setup_root_logger()`, `_CubeLevelFilter` |
| `src/cube/utils/logger_protocol.py` | `LazyArg` type alias |
| `src/cube/utils/std_logging.py` | `ColonPrefixFormatter`, `WebSocketLogHandler`, `DEBUG_ALL_ONLY` |
| `src/cube/application/Logger.py` | Re-export for backwards compatibility |
| `src/cube/application/state.py` | Calls `setup_root_logger()` |
