
# Pytest Cheat Sheet

All commands use `uv run` — no need to activate a venv.
Set `CUBE_QUIET_ALL=1` to suppress solver debug output.

## Environment Variables (PowerShell)

```powershell
# Suppress all debug output (for current session)
$env:CUBE_QUIET_ALL = "1"

# Enable all debug output
$env:CUBE_DEBUG_ALL = "1"

# Clear (unset) them
Remove-Item Env:CUBE_QUIET_ALL
Remove-Item Env:CUBE_DEBUG_ALL

# One-liner: set + run + unset
$env:CUBE_QUIET_ALL="1"; uv run pytest tests/ -v -m "not gui and not slow"; Remove-Item Env:CUBE_QUIET_ALL
```

In **bash** the inline syntax works directly:

```bash
CUBE_QUIET_ALL=1 uv run pytest tests/ -v -m "not gui and not slow"
CUBE_DEBUG_ALL=1 uv run pytest tests/ -v -k "scramble"
```

## Basic Usage

```bash
# Run all tests (default: -n auto for parallel)
uv run pytest

# Verbose
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Stop after N failures
uv run pytest --maxfail=3

# Show print output (not captured)
uv run pytest -s

# Combine: verbose + prints + stop-on-first
uv run pytest -vsx
```

## Collect Only (dry run, no execution)

```bash
# List all collected tests (full details)
uv run pytest --collect-only

# Short form (just test IDs)
uv run pytest --collect-only -q

# Collect with keyword filter
uv run pytest --collect-only -k "scramble"

# Collect specific directory
uv run pytest tests/algs --collect-only -q

# Count tests without running
uv run pytest --collect-only -q | tail -1
```

## Parallel vs Sequential

Default `addopts` in `pyproject.toml` is `-n auto` (parallel via pytest-xdist).

```bash
# Parallel (default) — uses all CPU cores
uv run pytest

# Explicit parallel with N workers
uv run pytest -n 4

# Sequential (disable xdist)
uv run pytest -n0

# Sequential is REQUIRED for:
#   - GUI tests (window conflicts)
#   - WebGL tests (browser/server conflicts)
#   - Debugging with -s or --pdb
#   - When test order matters
```

### xdist plugin

```bash
# pytest-xdist is in dev dependencies, installed via:
uv sync --group dev

# Without xdist installed, -n flag errors:
#   error: unrecognized arguments: -n
```

## Filtering Tests

```bash
# By keyword (-k)
uv run pytest -k "scramble"
uv run pytest -k "boy or cube"
uv run pytest -k "not slow"
uv run pytest -k "scramble and not slow"

# By marker (-m)
uv run pytest -m slow
uv run pytest -m "not slow"
uv run pytest -m "not gui and not slow"
uv run pytest -m benchmark

# By path
uv run pytest tests/algs/
uv run pytest tests/algs/test_cube.py
uv run pytest tests/algs/test_cube.py::test_scramble_and_solve
uv run pytest tests/algs/test_simplify.py::TestFlatten::test_flatten_slice_move
```

## Non-GUI Tests

```bash
# Standard run (exclude gui + slow)
CUBE_QUIET_ALL=1 uv run pytest tests/ -v -m "not gui and not slow"

# Quick (minimal output)
CUBE_QUIET_ALL=1 uv run pytest tests/ -m "not gui and not slow" -q

# Including slow tests
CUBE_QUIET_ALL=1 uv run pytest tests/ -m "not gui"
```

## GUI Tests

```bash
# Fast mode (no animation visible)
CUBE_QUIET_ALL=1 uv run pytest tests/gui -v -n0

# With animation speed-up
CUBE_QUIET_ALL=1 uv run pytest tests/gui -v -n0 --speed-up 5

# With visible animation (slow)
CUBE_QUIET_ALL=1 uv run pytest tests/gui -v -n0 --animate --speed-up 0

# Single GUI test
CUBE_QUIET_ALL=1 uv run pytest tests/gui/test_gui.py::test_face_rotations -v -n0
```

## WebGL E2E Tests (Playwright)

```bash
# Headless (CI)
CUBE_QUIET_ALL=1 uv run pytest tests/webgl/ -v -n0

# Headed (see browser)
CUBE_QUIET_ALL=1 uv run pytest tests/webgl/ -v -n0 --headed

# Specific browser
CUBE_QUIET_ALL=1 uv run pytest tests/webgl/ -v -n0 --browser-type=firefox
```

## Output & Debugging

```bash
# Shorter tracebacks
uv run pytest --tb=short

# One-line per failure
uv run pytest --tb=line

# No traceback
uv run pytest --tb=no

# Show local variables in tracebacks
uv run pytest -l

# Drop into debugger on failure (must be sequential)
uv run pytest --pdb -n0

# Show N slowest tests
uv run pytest --durations=10

# Project-specific debug flags
uv run pytest --quiet-debug    # suppress all solver debug output
uv run pytest --debug-all      # enable all solver debug output
```

## All Checks (pre-commit)

```bash
# 1. Ruff (fastest)
uv run ruff check src/cube

# 2. Mypy
uv run mypy -p cube

# 3. Pyright
uv run pyright src/cube

# 4. Non-GUI tests
CUBE_QUIET_ALL=1 uv run pytest tests/ -v -m "not gui and not slow"

# 5. GUI tests
CUBE_QUIET_ALL=1 uv run pytest tests/gui -v -n0 --speed-up 5
```

## Markers Reference

| Marker | Meaning |
|--------|---------|
| `slow` | Long-running tests (excluded by default in CI) |
| `benchmark` | Performance benchmarks |
| `gui` | Auto-applied to `tests/gui/`, `tests/webgl/` |
| `console` | Console interface tests |
| `webgl` | WebGL browser E2E tests |

## Viewing Full Test Failure Output in PyCharm

When tests fail with long assertion messages (e.g., failure tables), PyCharm may truncate the output.

### Option 1: Click on the failed test
- In the "Run" panel, click on the failed test name
- The full assertion message (including tables) shows in the right panel

### Option 2: Add pytest flags
- Go to: Run > Edit Configurations > your pytest config
- Add to "Additional Arguments": `-s --tb=short`
  - `-s` shows print output (disables capture)
  - `--tb=short` reduces traceback noise

### Option 3: "Click to see difference"
- PyCharm shows a link "Click to see difference" for failed assertions
- Click it to see the full assertion message in a popup

### Option 4: Scroll in output
- Simply scroll up in the Run panel output area
- The full pytest output including tables appears above the traceback

### Option 5: Double-click failed test
- Double-click on the failed test in the test tree
- This often expands to show the full assertion message

## Tips

- `-n auto` is default — always add `-n0` for GUI/WebGL/debug
- `--collect-only -q` to quickly see what would run before committing to a full run
- `-k` and `-m` can be combined: `-m "not slow" -k "scramble"`
- `CUBE_QUIET_ALL=1` prevents solver debug spam in output
