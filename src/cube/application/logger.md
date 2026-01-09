# Logger System Documentation

## Overview

The `Logger` class provides centralized debug output control for the entire application.
All debug output should go through the logger to ensure consistent behavior.

## Architecture

```
                    Environment Variables
                    CUBE_QUIET_ALL / CUBE_DEBUG_ALL
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                         Logger                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ _quiet_all  │  │ _debug_all  │  │ is_debug(flag)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         Solvers         Reducers        Geometry
         (debug)         (debug)         (debug)
```

## How Debug Flags Flow

```
GUI / CLI
    └→ AbstractApp.create_non_default(debug_all=X, quiet_all=Y)
        └→ ApplicationAndViewState(config, debug_all, quiet_all)
            └→ Logger(debug_all, quiet_all)  # + env var override
                └→ _App uses vs.logger (shared instance)
                    └→ Cube(sp=_App)
                        └→ cube.sp.logger  ← Solvers/Reducers access this
```

**One shared Logger instance** flows through the entire application.

## Usage

### For Code That Outputs Debug Messages

**DO use:**
```python
# Check before building expensive message
logger = self.cube.sp.logger
if logger.is_debug(local_debug_flag):
    msg = expensive_computation()
    print("MyComponent:", msg)

# Or use debug() method directly
logger.debug(local_debug_flag, "Simple message")

# Or use lazy evaluation for expensive messages
logger.debug_lazy(local_debug_flag, lambda: expensive_computation())
```

**DON'T use:**
```python
# Don't check internal flags directly
if logger.quiet_all:  # BAD - internal implementation detail
    ...

if logger.is_debug_all:  # BAD - internal implementation detail
    ...
```

### Logic

```
is_debug(local_flag) returns:
    - False if quiet_all is True (suppresses everything)
    - True if debug_all is True OR local_flag is True
    - False otherwise
```

## Suppressing All Debug Output

### From Shell (Windows CMD)
```cmd
set CUBE_QUIET_ALL=1
python -m pytest tests/
```

### From PowerShell
```powershell
# For single command
$env:CUBE_QUIET_ALL="1"; python -m pytest tests/

# For session
$env:CUBE_QUIET_ALL = "1"
python -m pytest tests/

# Unset
Remove-Item Env:CUBE_QUIET_ALL
```

### From Bash / Linux / macOS
```bash
CUBE_QUIET_ALL=1 python -m pytest tests/

# Or export for session
export CUBE_QUIET_ALL=1
python -m pytest tests/
```

### From PyCharm

1. **Run Configuration** → Edit Configurations
2. Select your configuration (e.g., pytest)
3. **Environment variables** → Add:
   - Name: `CUBE_QUIET_ALL`
   - Value: `1`

Or in pytest.ini / pyproject.toml:
```toml
[tool.pytest.ini_options]
# Note: env vars in config require pytest-env plugin
```

### Programmatically
```python
# At runtime
app.vs.quiet_all = True

# At startup
app = AbstractApp.create_non_default(quiet_all=True)
```

## Enabling All Debug Output

### From Shell
```powershell
$env:CUBE_DEBUG_ALL="1"; python -m cube.main_pyglet
```

### Programmatically
```python
# At startup only (no runtime setter currently)
app = AbstractApp.create_non_default(debug_all=True)
```

## GUI Debug Toggle

The GUI has a debug toggle button (Ctrl+O) that controls `config.solver_debug`.
This is a **local flag** passed to `logger.is_debug(solver_debug)`.

The env var `CUBE_QUIET_ALL=1` will still suppress output even if the button is ON.

## Environment Variables

| Variable | Effect |
|----------|--------|
| `CUBE_QUIET_ALL=1` | Suppress ALL debug output (overrides everything) |
| `CUBE_DEBUG_ALL=1` | Enable ALL debug output (unless quiet_all is set) |

Values accepted: `1`, `true`, `yes` (case-insensitive)

## Files

| File | Purpose |
|------|---------|
| `src/cube/utils/logger_protocol.py` | `ILogger` protocol definition |
| `src/cube/application/Logger.py` | `Logger` implementation |
| `src/cube/application/state.py` | `ApplicationAndViewState` delegates to Logger |

---

## Known Issues / TODO

### Design Issue: GUI Changes Config Directly

Currently, the GUI debug toggle directly modifies `config.solver_debug`:

```python
# In ToggleDebugCommand.execute():
cfg.solver_debug = not cfg.solver_debug
```

This is problematic because:
1. Config should be immutable or have controlled mutation
2. The toggle bypasses the Logger abstraction
3. Inconsistent with how quiet_all/debug_all are handled

**Proposed improvement:**
- Add a unified debug control in Logger or ApplicationAndViewState
- GUI should toggle via `vs.solver_debug = not vs.solver_debug`
- Or introduce a `DebugController` that manages all debug flags

### Missing debug_all Setter

Currently `debug_all` can only be set at construction time or via env var.
There's no runtime setter like `quiet_all` has. This may be intentional
(debug_all is meant to be set once at startup).
