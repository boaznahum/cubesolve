# Cube Logger — Usage Guide

## Quick Start

```python
import logging
from cube.utils.logger import CubeLogger, setup_root_logger

# 1. Set up the root logger (done once at app startup)
root = setup_root_logger()

# 2. Get a child logger for your component
logger: CubeLogger = root.getChild("MyComponent")

# 3. Log messages — standard logging API
logger.debug("solving edge...")
logger.info("phase 1 complete")
logger.error("invalid state")

# 4. Indented sections (only custom extension)
with logger.tab("Processing slice 1"):
    logger.debug("nested message")
    with logger.tab("Source face"):
        logger.debug("deeper nested")

# Output:
# DEBUG: MyComponent: ── Processing slice 1 ──
# DEBUG: MyComponent:│  nested message
# DEBUG: MyComponent:│  ── Source face ──
# DEBUG: MyComponent:│  │  deeper nested
# DEBUG: MyComponent:│  ── end: Source face ──
# DEBUG: MyComponent: ── end: Processing slice 1 ──
```

## Controlling Debug Output

Debug output is controlled by **standard logging levels** — no custom flags.

### Per-solver debug via `solve()`

```python
solver.solve(debug=True)   # Logger set to DEBUG → debug messages visible
solver.solve(debug=False)  # Logger set to INFO  → debug messages hidden
solver.solve(debug=None)   # Logger inherits from root (default)
```

Inside `AbstractSolver.solve()`, the logger level is set and restored:
```python
saved_level = self.__logger.level
self.__logger.setLevel(logging.DEBUG)  # or INFO
try:
    self._solve_impl(what)
finally:
    self.__logger.setLevel(saved_level)
```

### Global debug via config

When `config.solver_debug` is `True` (toggled via Ctrl+O in GUI), the app
sets the root logger level to `DEBUG`, which propagates to all child loggers
that haven't set their own level.

## Non-Standard Constants

### `DEBUG_ALL_ONLY` (level 5)

A custom logging level **below** `DEBUG` (10). Messages logged at this level
are only visible when `debug_all` mode is enabled.

```python
from cube.utils.std_logging import DEBUG_ALL_ONLY

# Visible only with --debug-all or CUBE_DEBUG_ALL=1
logger.log(DEBUG_ALL_ONLY, "extra verbose info")

# Visible in normal debug mode
logger.debug("normal debug info")
```

**Where it's used:** `ApplicationAndViewState.debug(debug_on, *args)` — the
`debug_on` parameter maps directly:
- `debug_on=True` → `logger.debug(msg)` — level 10 (normal debug)
- `debug_on=False` → `logger.log(DEBUG_ALL_ONLY, msg)` — level 5 (extra verbose)

### `cube_level` (1-5 verbosity filter)

For fine-grained verbosity **within** DEBUG, some solvers use a 1–5 scale:

```python
# Set threshold on the logger
self._logger.set_cube_level(3)   # Only show messages with cube_level <= 3

# Log with a cube_level (via SolverHelper.debug())
self.debug("important info", level=1)   # Shown (1 <= 3)
self.debug("normal detail", level=3)    # Shown (3 <= 3)
self.debug("verbose trace", level=5)    # Hidden (5 > 3)
```

Implemented as a standard `logging.Filter` (`_CubeLevelFilter`) attached to
each `CubeLogger` instance. Only 5 solver classes use this:
`NxNCenters`, `NxNEdges`, `E2ECommutator`, `_LBLNxNEdges`, `_LBLL3Edges`.

## Environment Variables

| Variable | Values | Effect |
|----------|--------|--------|
| `CUBE_QUIET_ALL` | `1`, `true`, `yes` | Suppress ALL debug output (errors still pass) |
| `CUBE_DEBUG_ALL` | `1`, `true`, `yes` | Enable ALL debug output, including `DEBUG_ALL_ONLY` |

Read once at startup by `setup_root_logger()`. They override the
`quiet_all` / `debug_all` constructor parameters.

### How they work

Both flags are checked in `CubeLogger.isEnabledFor()`, which overrides the
standard method:

```python
def isEnabledFor(self, level):
    if root._quiet_all and level < logging.ERROR:
        return False    # Suppress everything below ERROR
    if root._debug_all:
        return True     # Allow everything
    return super().isEnabledFor(level)
```

This means:
- `quiet_all` wins over everything (even explicit `setLevel(DEBUG)` on a child)
- `debug_all` overrides all level settings (even explicit `setLevel(INFO)`)
- Errors (`logger.error(...)`) always pass, even with `quiet_all`

### Priority

```
quiet_all=True  →  suppress all (except errors)
quiet_all=False, debug_all=True  →  show everything
quiet_all=False, debug_all=False  →  use standard level filtering
```

## Lazy Argument Resolution

Solver `debug()` methods accept callables for lazy evaluation:

```python
# Lambda only called if debug is actually enabled
self.debug("Result:", lambda: expensive_computation())

# Multiple lazy args
self.debug("Face:", lambda: face.color, "Grade:", lambda: calculate_grade())
```

Implemented in `AbstractSolver.debug()` and `SolverHelper.debug()` — they
check `logger.isEnabledFor(DEBUG)` first, then resolve callables, then log.
The standard `CubeLogger.debug()` itself does NOT resolve callables — that's
the caller's responsibility.

## Solver Logger Hierarchy

```
logging.getLogger("cube")              ← root, created by setup_root_logger()
├── getChild("LBL")                    ← AbstractSolver (LayerByLayerNxNSolver)
│   ├── getChild("Beginner3x3")        ← AbstractSolver (BeginnerSolver3x3)
│   │   ├── getChild("L1Cross")        ← SolverHelper
│   │   ├── getChild("L1Corners")      ← SolverHelper
│   │   └── ...
│   ├── getChild("NxNCenters")         ← SolverHelper
│   └── getChild("NxNEdges")           ← SolverHelper
├── getChild("Reducer")                ← AbstractReducer
│   └── getChild("CommonOp")           ← SolverHelper
└── getChild("Cage")                   ← AbstractSolver (CageNxNSolver)
```

Logger names are dot-separated (`cube.LBL.Beginner3x3.L1Cross`).
`ColonPrefixFormatter` converts dots to colons for display:
`DEBUG: LBL:Beginner3x3:L1Cross: message`.

## Creating Loggers

### In a solver (AbstractSolver subclass)

```python
class MySolver(AbstractSolver):
    def __init__(self, op, parent_logger: CubeLogger):
        super().__init__(op, parent_logger, logger_prefix="MySolver")
        # self._logger is now cube.*.MySolver
```

### In a helper (SolverHelper subclass)

```python
class MyHelper(SolverHelper):
    def __init__(self, solver):
        super().__init__(solver, "MyHelper")
        # self._logger is now cube.*.MySolver.MyHelper
```

### In a reducer (AbstractReducer subclass)

```python
class MyReducer(AbstractReducer):
    def __init__(self, op):
        super().__init__(op, logger_prefix="MyReducer")
        # self._logger is now cube.MyReducer
```

## Stream Callbacks

For routing log output to buffers or WebSocket clients:

```python
# Register a callback to receive every formatted log line
logger.add_stream(my_buffer.append)

# Unregister
logger.remove_stream(my_buffer.append)
```

Internally wraps the callback in a standard `logging.Handler`. The root
`CubeLogger` also IS-A `logging.Logger`, so you can directly use
`addHandler()` / `removeHandler()` for full control.

## What's Standard vs Custom

| Feature | Standard `logging` | Custom on `CubeLogger` |
|---------|-------------------|----------------------|
| `debug()`, `info()`, `error()` | Yes | |
| `setLevel()`, `getChild()` | Yes | |
| `addHandler()`, `removeHandler()` | Yes | |
| `isEnabledFor()` | Yes (overridden) | quiet_all / debug_all check |
| `makeRecord()` | Yes (overridden) | auto-inject indent |
| `tab()` | | Yes |
| `set_cube_level()` | | Yes (via `logging.Filter`) |
| `add_stream()` / `remove_stream()` | | Yes (wraps `addHandler`) |
| `quiet_all` / `debug_all` properties | | Yes |

## Files

| File | Contents |
|------|----------|
| `src/cube/utils/logger.py` | `CubeLogger`, `setup_root_logger()`, `_CubeLevelFilter`, `LazyArg`, `_resolve_arg` |
| `src/cube/utils/std_logging.py` | `ColonPrefixFormatter`, `WebSocketLogHandler`, `DEBUG_ALL_ONLY`, `ROOT_LOGGER_NAME` |
| `src/cube/utils/logger_protocol.py` | `LazyArg` type alias (re-export) |
| `src/cube/application/Logger.py` | Re-exports `CubeLogger`, `setup_root_logger` |
