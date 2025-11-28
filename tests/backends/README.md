# Backend Tests

This directory contains parameterized tests for GUI backends. Tests can run with any backend implementation by specifying the `--backend` option.

## Available Backends

| Backend | Description | Requirements |
|---------|-------------|--------------|
| `headless` | No-op backend for testing (default) | None |
| `pyglet` | Full OpenGL rendering | `pip install pyglet` |
| `tkinter` | Tkinter-based rendering | Python tk (usually included) |

## Running Tests

### Command Line

```bash
# Run with headless backend (default)
pytest tests/backends/ -v

# Run with specific backend
pytest tests/backends/ -v --backend=headless
pytest tests/backends/ -v --backend=pyglet
pytest tests/backends/ -v --backend=tkinter

# Run with all available backends
pytest tests/backends/ -v --backend=all
```

### Pyglet Backend

The pyglet backend provides full OpenGL rendering. It requires a display (won't work in headless CI environments).

```bash
# Install pyglet
pip install pyglet

# Run tests with pyglet
pytest tests/backends/ -v --backend=pyglet

# Run only pyglet with real window tests (creates visible windows)
pytest tests/backends/test_renderer_protocol.py -v --backend=pyglet
```

**Note:** Pyglet tests create real windows briefly during testing. Some headless-specific tests (event simulation) are skipped for pyglet.

### PyCharm

1. Right-click on test file or test function
2. Select "Modify Run Configuration"
3. In "Additional Arguments" field, add:
   ```
   --backend=headless
   ```

Alternatively, add to `pyproject.toml` for default behavior:
```toml
[tool.pytest.ini_options]
addopts = "--backend=headless"
```

## Test Structure

```
tests/backends/
├── README.md                      # This file
├── __init__.py                    # Package docstring
├── conftest.py                    # Fixtures and CubeTestDriver
├── test_renderer_protocol.py      # Renderer protocol tests
├── test_window_protocol.py        # Window protocol tests
├── test_event_loop_protocol.py    # EventLoop protocol tests
├── test_animation_protocol.py     # AnimationBackend protocol tests
└── test_cube_integration.py       # Cube operations with backends
```

## How Backend Selection Works

### 1. pytest_addoption (conftest.py:314-321)

Adds the `--backend` CLI option:

```python
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--backend",
        action="store",
        default="headless",   # Default if not specified
        help="Backend to test: headless, pyglet, tkinter, or 'all'",
    )
```

### 2. pytest_generate_tests (conftest.py:337-356)

Dynamically parametrizes tests with the selected backend:

```python
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "backend_name" in metafunc.fixturenames:
        backend_option = metafunc.config.getoption("--backend")
        # ... parametrizes backend_name with selected backend(s)
```

### 3. Fixture Chain

When a test requests `cube_driver`, this fixture chain executes:

```
backend_name              ← from pytest_generate_tests ("headless")
       ↓
ensure_backend_registered ← imports backend module, registers in BackendRegistry
       ↓
gui_components            ← creates Renderer, Window, EventLoop, Animation
       ↓
cube_driver               ← creates CubeTestDriver with all components
```

## Test Execution Flow

Example: Running `test_execute_chain`

```
pytest --backend=headless
         │
         ▼
┌─────────────────────────────────────┐
│  pytest_generate_tests              │
│  parametrize: backend_name=headless │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  ensure_backend_registered          │
│  → import headless backend          │
│  → registers in BackendRegistry     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  gui_components fixture             │
│  → BackendRegistry.create_*()      │
│  → HeadlessRenderer                 │
│  → HeadlessWindow                   │
│  → HeadlessEventLoop                │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  cube_driver fixture                │
│  → Cube(3), Operator(cube)          │
│  → CubeTestDriver(...)              │
│  → window.set_key_press_handler()   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  test_execute_chain runs            │
│  cube_driver.execute("R")           │
│    → parse_key_string("R")          │
│    → window.queue_key_events([...]) │
│    → window.process_queued_key_events│
│    → _handle_key(event)             │
│    → operator.play(Algs.R)          │
│    → history.append("R")            │
└─────────────────────────────────────┘
```

## CubeTestDriver

The `CubeTestDriver` provides an abstract interface for testing cube operations without manually handling key-to-algorithm conversion.

### Available Methods

| Method | Description |
|--------|-------------|
| `execute("RLU")` | Execute moves via key sequence |
| `execute("R'L'")` | Execute inverse moves (prime notation) |
| `execute_keys(Keys.R, Keys.L)` | Execute by key codes |
| `execute_alg(Algs.R)` | Execute algorithm directly |
| `scramble(seed=42)` | Scramble with reproducible seed |
| `solve()` | Solve the cube |
| `undo(count=1)` | Undo moves |
| `reset()` | Reset to solved state |
| `render_frame()` | Render a frame |
| `register_key(key, handler)` | Add custom key handler |
| `set_key_mapping(key, alg)` | Override key-to-algorithm mapping |

### Properties

| Property | Description |
|----------|-------------|
| `cube` | The Cube instance |
| `operator` | The Operator instance |
| `solved` | Whether cube is solved |
| `history` | List of executed move names |
| `solver` | Solver instance (lazy-created) |

### Example Test

```python
def test_scramble_and_solve(cube_driver: CubeTestDriver, backend_name: str):
    # Fluent interface with method chaining
    cube_driver.scramble(seed=42)
    assert not cube_driver.solved

    cube_driver.solve()
    assert cube_driver.solved

def test_rotation_sequence(cube_driver: CubeTestDriver, backend_name: str):
    # Execute moves via string notation
    cube_driver.execute("RLU")
    assert cube_driver.history == ["R", "L", "U"]

    # Inverse moves with prime notation
    cube_driver.execute("U'L'R'")
    assert cube_driver.solved

def test_chaining(cube_driver: CubeTestDriver, backend_name: str):
    # Method chaining
    cube_driver.scramble(seed=1).render_frame().solve().render_frame()
    assert cube_driver.solved
```

### Factory Fixture for Custom Cube Sizes

```python
def test_large_cube(cube_driver_factory, backend_name: str):
    driver = cube_driver_factory(5)  # 5x5 cube
    driver.scramble(seed=42).solve()
    assert driver.solved
```

## Key Mapping

Default key-to-algorithm mapping:

| Key | Algorithm | Shift+Key | Algorithm |
|-----|-----------|-----------|-----------|
| R | Algs.R | Shift+R | Algs.R' (inverse) |
| L | Algs.L | Shift+L | Algs.L' |
| U | Algs.U | Shift+U | Algs.U' |
| D | Algs.D | Shift+D | Algs.D' |
| F | Algs.F | Shift+F | Algs.F' |
| B | Algs.B | Shift+B | Algs.B' |
| M | Algs.M | | |
| E | Algs.E | | |
| S | Algs.S | | |
| X | Algs.X | | |
| Y | Algs.Y | | |
| Z | Algs.Z | | |

## Adding a New Backend

To add tests for a new backend:

1. Implement the backend in `src/cube/gui/backends/<name>/`
2. Register it in `BackendRegistry`
3. Add import in `conftest.py:get_available_backends()`
4. Run tests: `pytest tests/backends/ --backend=<name>`

All existing tests will automatically run against the new backend.
