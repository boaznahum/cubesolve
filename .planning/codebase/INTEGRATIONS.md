# External Integrations

**Analysis Date:** 2026-01-28

## APIs & External Services

**Kociemba Cube Solver:**
- Service: Kociemba two-phase algorithm for 3x3 Rubik's cube solving
  - SDK/Client: `kociemba` Python package
  - Integration: `src/cube/domain/solver/_3x3/kociemba/Kociemba3x3.py`
  - Auth: None required (local package)
  - Protocol: Function call `kociemba.solve(cube_string)` with 54-character state string
  - Format: String-based cube representation (54 chars: U R F D L B face order)
  - Response: Move sequence string (e.g., "R U R' U'")
  - Performance: <1 second for any solvable position

## Data Storage

**Databases:**
- None - Fully in-memory application, no persistence layer

**File Storage:**
- Local filesystem only:
  - Cube face textures: `src/cube/resources/faces/` directory
    - Built-in sets: `set1/`, `numbers/`, `debug3x3/`
    - Custom textures supported in `config.py` via `TEXTURE_SETS` list
  - Algorithm files: `src/cube/resources/algs/*.txt` (bundled)
  - Test output: Temporary files via `tempfile` module
  - Recording data: In-memory pickle serialization only

**Caching:**
- In-memory caching:
  - Cube state caching (optional, controlled by `CUBE_DISABLE_CACHE` env var)
  - Part property caching (`colors_id`, `position_id` in `src/cube/domain/model/Part.py`)
  - Algorithm caching in solver instances
- No external cache service

## Authentication & Identity

**Auth Provider:**
- None - Single-user desktop/web application
- No user accounts, login, or identity management

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service
- Exceptions logged to console via custom Logger

**Logs:**
- Custom logging approach:
  - Console output via `print()` and `colorama`/`rich` for colored output
  - Debug output controlled by flags:
    - `--debug-all` CLI flag
    - `--quiet` CLI flag to suppress output
    - `CUBE_QUIET_ALL=1` environment variable for tests
  - Solver debug output toggle: `O` key (or `TOGGLE_DEBUG` command)
  - No persistent log files by default

## CI/CD & Deployment

**Hosting:**
- Desktop application (pyglet backend) - no hosting required
- Web backend can run locally on configurable port (default: 8765)
  - Serves static files from `src/cube/presentation/gui/backends/web/static/`
  - WebSocket communication for browser sync

**CI Pipeline:**
- None configured in repository
- Manual test commands available:
  - Non-GUI tests: `CUBE_QUIET_ALL=1 python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
  - GUI tests: `CUBE_QUIET_ALL=1 python -m pytest tests/gui -v --speed-up 5`
  - Type checking: `python -m mypy -p cube` and `python -m pyright src/cube`
  - Linting: `python -m ruff check src/cube`

## Environment Configuration

**Required env vars:**
- None required - application runs with defaults

**Optional env vars:**
- `CUBE_DISABLE_CACHE` - Disable cube state caching for debugging
- `CUBE_QUIET_ALL` - Suppress debug output (used in tests)
- Backend-specific configuration in `src/cube/application/_config.py`:
  - Animation settings, debug flags, solver defaults
  - Texture sets configuration (custom face images)
  - Marker display settings for annotations

**Secrets location:**
- No secrets management required - no credentials in application
- No API keys, database passwords, or authentication tokens

## Webhooks & Callbacks

**Incoming:**
- None configured
- Web backend receives WebSocket messages from browser client:
  - Message types: `connected`, `key`, `mouse_press`, `mouse_drag`, `resize`
  - Handler: `WebEventLoop._handle_message()` in `src/cube/presentation/gui/backends/web/WebEventLoop.py`

**Outgoing:**
- WebSocket broadcasts to all connected clients:
  - Cube render state updates via `broadcast()` method
  - No external webhooks or callbacks

## Data Communication Protocols

**Internal:**
- Command pattern for keyboard/mouse input:
  - Files: `src/cube/presentation/gui/KeyEvent.py`, `Keys.py`, `Command.py`
  - Event handlers convert native input to abstract `Command` enum
  - Commands execute via `command.execute(ctx)`

**External (Web Backend):**
- WebSocket (via aiohttp):
  - Port: 8765 (default, customizable)
  - Protocol: JSON messages from browser to server
  - Message format: `{"type": "key", "code": <keycode>, "modifiers": <flags>, "key": "<char>"}`
  - Browser opens automatically (unless `gui_test_mode=True`)

---

*Integration audit: 2026-01-28*
