# Session: Migrate Logger to Standard logging.Logger

**Date**: 2026-03-25
**Branch**: `claude/migrate-logging-system-Xu6AK`

## Goal

Replace custom `Logger(ILogger)` wrapper with `CubeLogger(logging.Logger)` subclass — pure standard logging with minimal custom extensions.

## Design Decisions (agreed with user)

### 1. `debug_flag` callback — REMOVED
- **Old**: Each solver registered `debug_flag=lambda: self._is_debug_enabled` on logger creation.
- **New**: Solver sets `logger.setLevel(DEBUG)` or `setLevel(NOTSET)` in `solve()`. No callback.

### 2. `debug_on` parameter — REPLACED with standard levels
- `debug_on=True/None` → `logger.debug("msg")` — standard DEBUG (10)
- `debug_on=False` → `logger.log(DEBUG_ALL_ONLY, "msg")` — custom level 5, only visible with `debug_all`
- `debug_all` sets root logger to level 5 (below DEBUG=10)
- `quiet_all` → filter on root blocks everything below ERROR

### 3. `set_prefix()` — DELETED (dead code, no external callers)

### 4. `with_prefix()` → `logging.getLogger("cube.Parent.Child")` / `getChild()`
- Standard logger hierarchy, names map to colon-separated prefixes via `ColonPrefixFormatter`

### 5. `level=1..5` verbosity — kept as `logging.Filter`
- `_CubeLevelFilter` checks `cube_level` attribute on records
- `set_cube_level(3)` = show messages with `cube_level <= 3`
- Only 5 call sites use this

### 6. `tab()` indentation — kept as custom method on CubeLogger
- `CubeLogger(logging.Logger)` subclass with `tab()` + `makeRecord()` override
- `makeRecord()` injects `indent` into every record automatically
- This is the ONLY custom extension on the logger class

### 7. `LazyArg` resolution — moved to `SolverHelper.debug()` / `AbstractSolver.debug()`
- These methods resolve callables, join args, then call `self._logger.debug(message)`
- Standard `logging.Logger.debug()` on the CubeLogger itself

### 8. `quiet_all` / `debug_all` — override `isEnabledFor()` on CubeLogger
- `CubeLogger.isEnabledFor()` checks root's `_quiet_all` and `_debug_all` flags
- `quiet_all`: blocks everything below ERROR
- `debug_all`: allows everything (overrides individual solver levels)

## Architecture

```
CubeLogger(logging.Logger)
├── tab() — context manager for indentation
├── makeRecord() — injects indent extra field
├── isEnabledFor() — checks root quiet_all/debug_all
├── set_cube_level(n) — sets _CubeLevelFilter threshold
└── Standard: debug(), info(), warning(), error(), setLevel(), getChild(), etc.

Root setup:
  logging.setLoggerClass(CubeLogger)
  root = logging.getLogger("cube")  # returns CubeLogger
  root.addHandler(console_handler)
  root.propagate = False
```

## Key Files to Modify

| File | Change |
|------|--------|
| `src/cube/utils/logger.py` | Replace `Logger(ILogger)` with `CubeLogger(logging.Logger)` |
| `src/cube/utils/logger_protocol.py` | Update `ILogger` protocol |
| `src/cube/utils/std_logging.py` | Add `DEBUG_ALL_ONLY` level constant |
| `src/cube/application/Logger.py` | Update re-export |
| `src/cube/application/state.py` | Root logger creation, debug/quiet_all via CubeLogger |
| `src/cube/domain/solver/common/AbstractSolver.py` | Logger creation via getChild, debug method, solve() level mgmt |
| `src/cube/domain/solver/common/SolverHelper.py` | Logger creation via getChild, debug method |
| `src/cube/domain/solver/reducers/AbstractReducer.py` | Same pattern as AbstractSolver |
| `src/cube/domain/solver/direct/lbl/_LBLNxNEdges.py` | set_level → set_cube_level |
| `src/cube/domain/solver/direct/lbl/_LBLL3Edges.py` | set_level → set_cube_level |
| `src/cube/domain/solver/common/big_cube/NxNCenters.py` | set_level → set_cube_level |
| `src/cube/domain/solver/common/big_cube/NxNEdges.py` | set_level → set_cube_level |
| `src/cube/domain/solver/common/big_cube/commutator/E2ECommutator.py` | set_level → set_cube_level |
| `src/cube/application/commands/Operator.py` | debug(True,...) → debug(...) |
| `src/cube/presentation/gui/commands/concrete.py` | debug(False,...) → log(DEBUG_ALL_ONLY,...) |
| `src/cube/presentation/gui/backends/webgl/ClientSession.py` | add_stream/remove_stream → addHandler/removeHandler |
| `src/cube/domain/solver/_3x3/beginner/BeginnerSolver3x3.py` | _logger.debug(None,...) → _logger.debug(...) |

## Migration Status

- [x] Planning and design decisions
- [ ] Implement CubeLogger class
- [ ] Update protocol
- [ ] Update all callers
- [ ] Update docs
- [ ] Run tests
