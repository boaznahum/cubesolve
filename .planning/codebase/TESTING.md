# Testing Patterns

**Analysis Date:** 2026-01-28

## Test Framework

**Runner:**
- Framework: pytest
- Version: Latest from pyproject.toml dev dependencies
- Config file: `pyproject.toml` under `[tool.pytest.ini_options]`
- Auto-discovery: `python_files = ["test_*.py", "bug_*.py"]`

**Assertion Library:**
- Built-in pytest assertions
- Usage: `assert` statements for all test assertions

**Run Commands:**

```bash
# Run all non-GUI tests (fastest, use for CI/pre-commit)
CUBE_QUIET_ALL=1 python -m pytest tests/ -v --ignore=tests/gui -m "not slow"

# Run GUI tests only
CUBE_QUIET_ALL=1 python -m pytest tests/gui -v --speed-up 5

# Run all tests (GUI + non-GUI)
CUBE_QUIET_ALL=1 python -m pytest tests/ -v --speed-up 5

# Run specific test
python -m pytest tests/algs/test_boy.py::test_scramble1_preserves_boy_large_cube -v

# Run with multiple workers (default behavior)
pytest tests/ -v --ignore=tests/gui

# Run specific test class
pytest tests/backends/test_cube_integration.py::TestCubeRotations -v
```

## Test File Organization

**Location:**
- Co-located with source in parallel `tests/` directory
- Mirror source directory structure: `src/cube/domain/` → `tests/domain/`
- GUI tests separate: `tests/gui/` for GUI-specific tests
- Backend tests: `tests/backends/` for GUI backend integration

**Naming:**
- Test files: `test_<module>.py` or `bug_<issue>.py`
- Test functions: `test_<scenario>()`
- Test classes: `Test<Feature>` (e.g., `TestCubeRotations`, `TestCubeSolving`)
- Fixtures: lowercase with leading underscore for private: `_test_sp`, `enable_animation`

**Structure:**

```
tests/
├── algs/                           # Algorithm tests
│   ├── test_boy.py                # BOY orientation tests
│   ├── test_cube.py               # Cube model tests
│   └── test_scramble_repeatable.py
├── backends/                       # GUI backend integration tests
│   ├── conftest.py                # Backend fixtures (CubeTestDriver)
│   ├── test_cube_integration.py    # Cube operations via GUI
│   ├── test_animation_protocol.py  # Animation backend protocol
│   └── test_window_protocol.py     # Window backend protocol
├── gui/                            # GUI-specific tests (slower)
│   ├── conftest.py                # GUI fixtures (fixtures & parametrization)
│   ├── test_gui.py                # GUITestRunner-based tests
│   └── test_checkmark_markers.py
├── geometry/                       # Geometric/spatial tests
│   ├── test_bring_face_to.py
│   └── test_cube_walking.py
├── solvers/                        # Solver-specific tests
│   ├── conftest.py                # Solver fixtures & parametrization
│   ├── test_beginners.py          # Beginner solver tests
│   └── wip/                        # Work-in-progress solvers
└── test_utils.py                   # Shared utilities (TestServiceProvider)
```

## Test Structure

**Suite Organization:**

```python
# tests/backends/test_cube_integration.py
import pytest
from cube.domain.algs import Algs
from cube.domain.solver.SolverName import SolverName
from tests.backends.conftest import CubeTestDriver

# Mark all tests in module as GUI tests
pytestmark = pytest.mark.gui

class TestCubeRotations:
    """Test basic cube rotations via key sequences."""

    def test_single_rotation(self, cube_driver: CubeTestDriver, backend_name: str):
        """Single rotation should change cube state."""
        assert cube_driver.solved
        cube_driver.execute("R")
        assert not cube_driver.solved
        assert cube_driver.history == ["R"]

    def test_multiple_rotations(self, cube_driver: CubeTestDriver, backend_name: str):
        """Multiple rotations via sequence."""
        cube_driver.execute("RLU")
        assert not cube_driver.solved
```

**Patterns:**

- **Setup (Fixtures):**
  - Pytest fixtures provide test dependencies
  - Fixtures in `conftest.py` files at module/package level
  - Fixture scopes: `function` (default), `class`, `module`, `session`
  - Example: `@pytest.fixture def cube_driver(...) -> Iterator[CubeTestDriver]`

- **Teardown:**
  - Use `yield` for resource cleanup (replaces setUp/tearDown)
  - Example from `tests/backends/conftest.py`:
  ```python
  @pytest.fixture
  def renderer(backend_name: str) -> Iterator[Renderer]:
      backend = BackendRegistry.get_backend(backend_name)
      r = backend.renderer
      r.setup()
      yield r  # Test runs here
      r.cleanup()
  ```

- **Assertion Pattern:**
  - Use bare `assert` statements
  - Pytest rewrites them for better error messages
  - Example: `assert cube_driver.solved`, `assert len(history) == 6`
  - Use `== False` rarely; prefer `assert not condition`

## Mocking

**Framework:** Manual fixtures (no pytest-mock used)

**Patterns:**

```python
# tests/backends/conftest.py - CubeTestDriver provides test doubles

@dataclass
class CubeTestDriver:
    """Abstracts key-to-algorithm conversion for testing."""
    cube: Cube
    operator: Operator
    window: Window
    renderer: Renderer
    event_loop: EventLoop
    animation: AnimationBackend | None = None

    def execute(self, sequence: str) -> "CubeTestDriver":
        """Execute move sequence (e.g., 'RLU', 'R'')."""
        events = []
        # Parse and convert to key events
        self.window.queue_key_events(events)
        self.window.process_queued_key_events()
        return self

    def solve(self) -> "CubeTestDriver":
        """Solve cube using solver."""
        self.solver.solve()
        return self
```

**What to Mock:**
- Use `CubeTestDriver` for GUI backend testing (avoids direct key handling)
- Create test doubles via fixtures when full integration not needed
- Use `TestServiceProvider` for dependency injection in domain tests

**What NOT to Mock:**
- Core domain logic (Cube, Part, Solver) - test real implementations
- Backend implementations - use actual backend (headless for speed)
- Algorithms (Algs) - test actual algorithm execution
- Only mock when testing *integration* between layers (GUI ↔ domain)

## Fixtures and Factories

**Test Data:**

```python
# tests/test_utils.py - Shared test service provider
class TestServiceProvider(IServiceProvider):
    """Service provider for tests that create Cube directly."""

    def __init__(self) -> None:
        self._config = AppConfig()
        self._marker_factory = MarkerFactory()
        self._marker_manager = MarkerManager()
        self._logger = Logger()

_test_sp = TestServiceProvider()

# Usage in tests:
def test_scramble1_preserves_boy_large_cube() -> None:
    cube = Cube(size=7, sp=_test_sp)
    # ... test ...
```

**Factory Fixtures:**

```python
# tests/backends/conftest.py
@pytest.fixture
def cube_driver_factory(...) -> Callable[[int, SolverName | None], CubeTestDriver]:
    """Factory to create CubeTestDriver with custom size/solver."""

    def create_driver(cube_size: int = 3, solver_name: SolverName | None = None) -> CubeTestDriver:
        cube = Cube(cube_size, sp=_test_sp)
        config = AppConfig()
        app_state = ApplicationAndViewState(config)
        operator = Operator(cube, app_state)
        return CubeTestDriver(cube=cube, operator=operator, ...)

    return create_driver

# Usage:
def test_large_cube(cube_driver_factory):
    driver = cube_driver_factory(5)  # 5x5 cube
    driver.scramble().solve()
    assert driver.solved
```

**Location:**
- Fixtures in `conftest.py` at each test package level
- Shared fixtures: `tests/conftest.py` (none exists currently)
- Backend fixtures: `tests/backends/conftest.py`
- GUI fixtures: `tests/gui/conftest.py`
- Solver fixtures: `tests/solvers/conftest.py`

## Coverage

**Requirements:** No explicit coverage target enforced
- Coverage optional but encouraged
- View with: `pytest tests/ --cov=src/cube`
- Target: Aim for >80% on core domain logic

## Test Types

**Unit Tests:**
- Scope: Single function/method in isolation
- Example: `test_scramble1_preserves_boy_large_cube()` tests Cube rotation
- Fixtures: Use `_test_sp` for Cube creation
- Location: `tests/algs/`, `tests/domain/`, `tests/geometry/`

**Integration Tests:**
- Scope: Multiple components working together
- Example: `TestCubeIntegration` tests cube + GUI backend + solver
- Fixtures: Use `CubeTestDriver` to coordinate
- Location: `tests/backends/test_cube_integration.py`
- Run with: `pytest tests/backends/ -v --backend=headless` (fast) or `--backend=all` (all backends)

**GUI Tests:**
- Scope: Full GUI application including rendering
- Framework: Custom `GUITestRunner` (not pytest-based)
- Example: `test_scramble_and_solve()` injects commands into full app
- Location: `tests/gui/test_gui.py`
- Run with: `pytest tests/gui -v --speed-up 5`
- Marked with: `@pytest.mark.gui`
- Parametrized: `backend` parameter for multi-backend testing

## Parametrization

**Markers:**

```python
# pytest.ini_options in pyproject.toml
markers = [
    "slow: marks tests as slow",
    "benchmark: marks tests as benchmarks",
    "gui: marks tests as GUI tests",
    "console: marks tests as console tests",
]
```

**Usage:**

```python
# Skip slow tests
pytest tests/ -m "not slow"

# Run only GUI tests
pytest tests/ -m "gui"

# Run only slow tests
pytest tests/ -m "slow"
```

**Parametrization Examples:**

```python
# Multiple solver names
@pytest.mark.parametrize("solver_name", ALL_SOLVERS)
def test_scramble_and_solve(cube_driver, solver_name: SolverName):
    skip_if_not_supported(solver_name, 3)
    cube_driver.scramble(seed=42).solve()
    assert cube_driver.solved

# Multiple seeds
@pytest.mark.parametrize("seed", [1, 2, 3, 42, 123])
def test_reproducible_scramble(cube_driver, seed: int):
    cube_driver.scramble(seed=seed)
    # Test ...

# Backend parametrization (from conftest)
def test_cube_integration(cube_driver: CubeTestDriver, backend_name: str):
    # backend_name comes from pytest_generate_tests in conftest.py
    # Runs test once per backend (pyglet2, headless, console, ...)
```

## Common Patterns

**Async Testing:**
- Not used (no async code in this codebase)
- Tests are synchronous

**Error Testing:**

```python
# Expect exception
def test_invalid_cube_size():
    with pytest.raises(ValueError):
        Cube(size=1)  # Too small

# Check exception message
def test_exception_message():
    with pytest.raises(InternalSWError) as exc_info:
        # Code that raises ...
    assert "expected message" in str(exc_info.value)
```

**Skipping Tests:**

```python
# Skip all test instances for a solver if not supported
def skip_if_not_supported(solver_name: SolverName, cube_size: int) -> None:
    """Skip test if solver doesn't support this cube size."""
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(skip_reason)

# Usage:
@pytest.mark.parametrize("solver_name", ALL_SOLVERS)
def test_solve(cube_driver, solver_name: SolverName):
    skip_if_not_supported(solver_name, 3)  # Skips if not supported
    # ... test ...
```

**Test Discovery:**

```bash
# Pytest auto-discovers:
# - test_*.py files
# - bug_*.py files (for regression tests)
# - test_*() functions
# - Test*() classes with test_*() methods
```

## GUI Test Specifics

**Testing Framework:** Custom `GUITestRunner` + pytest

**File Location:** `src/cube/presentation/gui/testing/` (implementation)

**Test Pattern:**

```python
# tests/gui/test_gui.py
@pytest.mark.parametrize("cube_size", [3])
def test_scramble_and_solve(cube_size: int, enable_animation: bool,
                            speed_up_count: int, backend: str):
    result = GUITestRunner.run_test(
        commands=Commands.SPEED_UP * speed_up_count +
                 Commands.SCRAMBLE_1 + Commands.SOLVE_ALL + Commands.QUIT,
        cube_size=cube_size,
        timeout_sec=60.0,
        enable_animation=enable_animation,
        backend=backend,
        debug=True
    )
    assert result.success, f"GUI test failed: {result.message}. Error: {result.error}"
```

**Test Commands:**
- `Commands.SPEED_UP` - Speed up animation
- `Commands.SCRAMBLE_1`, `SCRAMBLE_2`, etc. - Scramble with seed
- `Commands.SOLVE_ALL` - Solve cube
- `Commands.ROTATE_R`, `ROTATE_L`, etc. - Rotate individual faces
- `Commands.QUIT` - Exit application

**Fixtures:**

```python
# From conftest.py
@pytest.fixture
def enable_animation(request) -> bool:
    """Returns True if --animate flag passed."""
    return request.config.getoption("--animate")

@pytest.fixture
def speed_up_count(request) -> int:
    """Returns number of speed-ups (default: 3)."""
    return request.config.getoption("--speed-up")

# Parametrized automatically by pytest_generate_tests()
def test_name(backend: str):
    # backend = "pyglet2", "headless", or "console" (auto-parametrized)
```

**CLI Options:**

```bash
# --animate (default: True)
pytest tests/gui -v --animate

# --speed-up N (default: 3)
pytest tests/gui -v --speed-up 5

# --backend NAME (default: "all")
pytest tests/gui -v --backend=pyglet2
pytest tests/gui -v --backend=all  # Test all available backends
```

---

*Testing analysis: 2026-01-28*
