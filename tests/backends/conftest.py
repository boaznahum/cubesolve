"""
Pytest configuration for backend tests.

Provides fixtures and hooks for parameterized backend testing.
Includes CubeTestDriver for abstract key sequence testing.
"""

import pytest
from typing import Iterator, Callable
from dataclasses import dataclass, field

from cube.presentation.gui.factory import BackendRegistry
from cube.presentation.gui.protocols import Renderer, Window, EventLoop, AnimationBackend
from cube.presentation.gui.types import KeyEvent, Keys, Modifiers, parse_key_string, make_key_sequence
from cube.domain.model.Cube import Cube
from cube.application.commands.Operator import Operator
from cube.domain.algs import Algs
from cube.domain.solver import Solvers


# Standard key-to-algorithm mapping for cube operations
DEFAULT_KEY_MAPPING: dict[int, Algs] = {
    Keys.R: Algs.R,
    Keys.L: Algs.L,
    Keys.U: Algs.U,
    Keys.D: Algs.D,
    Keys.F: Algs.F,
    Keys.B: Algs.B,
    Keys.M: Algs.M,
    Keys.E: Algs.E,
    Keys.S: Algs.S,
    Keys.X: Algs.X,
    Keys.Y: Algs.Y,
    Keys.Z: Algs.Z,
}

# Shift modifier for inverse moves (using .prime attribute)
SHIFT_KEY_MAPPING: dict[int, Algs] = {
    Keys.R: Algs.R.prime,
    Keys.L: Algs.L.prime,
    Keys.U: Algs.U.prime,
    Keys.D: Algs.D.prime,
    Keys.F: Algs.F.prime,
    Keys.B: Algs.B.prime,
}


@dataclass
class CubeTestDriver:
    """Abstract test driver for cube operations with any GUI backend.

    Provides a clean interface for testing cube operations without
    manually handling key-to-algorithm conversion in each test.

    Usage:
        def test_rotation(cube_driver):
            cube_driver.execute("RLU")  # Execute R, L, U moves
            assert not cube_driver.cube.solved

            cube_driver.execute("R'")   # R inverse (with shift)
            cube_driver.undo()          # Undo last move
            cube_driver.solve()         # Solve the cube

    The driver handles:
    - Key-to-algorithm mapping
    - Sequence injection into backend
    - Cube state management
    - Solver integration
    """

    cube: Cube
    operator: Operator
    window: Window
    renderer: Renderer
    event_loop: EventLoop
    animation: AnimationBackend | None = None
    _solver: Solvers | None = field(default=None, init=False)
    _key_mapping: dict[int, Algs] = field(default_factory=lambda: DEFAULT_KEY_MAPPING.copy())
    _shift_mapping: dict[int, Algs] = field(default_factory=lambda: SHIFT_KEY_MAPPING.copy())
    _custom_handlers: dict[int, Callable[[KeyEvent], None]] = field(default_factory=dict)
    _history: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Setup key handler on window."""
        self.window.set_key_press_handler(self._handle_key)

    def _handle_key(self, event: KeyEvent) -> None:
        """Internal key handler that maps keys to operations."""
        # Check custom handlers first
        if event.symbol in self._custom_handlers:
            self._custom_handlers[event.symbol](event)
            return

        # Check for shift modifier (inverse moves)
        if event.modifiers & Modifiers.SHIFT:
            if event.symbol in self._shift_mapping:
                alg = self._shift_mapping[event.symbol]
                self.operator.play(alg)
                self._history.append(f"{chr(event.symbol)}'")
                return

        # Normal moves
        if event.symbol in self._key_mapping:
            alg = self._key_mapping[event.symbol]
            self.operator.play(alg)
            self._history.append(chr(event.symbol))

    @property
    def solver(self) -> Solvers:
        """Get or create solver."""
        if self._solver is None:
            self._solver = Solvers.default(self.operator)
        return self._solver

    @property
    def solved(self) -> bool:
        """Check if cube is solved."""
        return self.cube.solved

    @property
    def history(self) -> list[str]:
        """Get history of executed moves."""
        return self._history.copy()

    def execute(self, sequence: str) -> "CubeTestDriver":
        """Execute a sequence of moves.

        Args:
            sequence: Move notation string. Examples:
                - "RLU" - R, L, U moves
                - "R'L'U'" - R', L', U' (inverse) moves
                - "RLUDFB" - All face moves

        Returns:
            self for chaining
        """
        if not hasattr(self.window, 'queue_key_events'):
            raise RuntimeError("Backend doesn't support sequence injection")

        # Parse the sequence - handle prime notation
        events = []
        i = 0
        while i < len(sequence):
            char = sequence[i]
            # Check for prime (') modifier
            if i + 1 < len(sequence) and sequence[i + 1] == "'":
                events.extend(parse_key_string(char.upper()))
                # Add shift modifier to last event
                if events:
                    last = events[-1]
                    events[-1] = KeyEvent(
                        symbol=last.symbol,
                        modifiers=Modifiers.SHIFT,
                        char=last.char
                    )
                i += 2
            else:
                events.extend(parse_key_string(char))
                i += 1

        self.window.queue_key_events(events)
        self.window.process_queued_key_events()
        return self

    def execute_keys(self, *keys: int | tuple[int, int]) -> "CubeTestDriver":
        """Execute a sequence of key codes.

        Args:
            *keys: Key codes or (key, modifiers) tuples

        Returns:
            self for chaining
        """
        if not hasattr(self.window, 'queue_key_events'):
            raise RuntimeError("Backend doesn't support sequence injection")

        events = make_key_sequence(*keys)
        self.window.queue_key_events(events)
        self.window.process_queued_key_events()
        return self

    def execute_alg(self, alg: Algs) -> "CubeTestDriver":
        """Execute an algorithm directly.

        Args:
            alg: Algorithm to execute

        Returns:
            self for chaining
        """
        self.operator.play(alg)
        return self

    def scramble(self, seed: int = 42) -> "CubeTestDriver":
        """Scramble the cube.

        Args:
            seed: Random seed for reproducible scramble

        Returns:
            self for chaining
        """
        scramble_alg = Algs.scramble(self.cube.size, seed=seed)
        self.operator.play(scramble_alg)
        return self

    def solve(self) -> "CubeTestDriver":
        """Solve the cube.

        Returns:
            self for chaining
        """
        self.solver.solve()
        return self

    def undo(self, count: int = 1) -> "CubeTestDriver":
        """Undo moves.

        Args:
            count: Number of moves to undo

        Returns:
            self for chaining
        """
        for _ in range(count):
            self.operator.undo()
        return self

    def reset(self) -> "CubeTestDriver":
        """Reset cube to solved state.

        Returns:
            self for chaining
        """
        self.operator.reset()
        self._history.clear()
        return self

    def render_frame(self) -> "CubeTestDriver":
        """Render a single frame.

        Returns:
            self for chaining
        """
        self.renderer.begin_frame()
        self.renderer.clear()
        self.renderer.end_frame()
        return self

    def register_key(
        self,
        key: int,
        handler: Callable[[KeyEvent], None]
    ) -> "CubeTestDriver":
        """Register a custom key handler.

        Args:
            key: Key code
            handler: Handler function

        Returns:
            self for chaining
        """
        self._custom_handlers[key] = handler
        return self

    def set_key_mapping(self, key: int, alg: Algs) -> "CubeTestDriver":
        """Set or override a key-to-algorithm mapping.

        Args:
            key: Key code
            alg: Algorithm to execute

        Returns:
            self for chaining
        """
        self._key_mapping[key] = alg
        return self


def get_available_backends() -> list[str]:
    """Get list of available backends for testing.

    Imports backends to trigger registration, then returns available ones.
    """
    available = []

    # Always try headless first (no dependencies)
    try:
        from cube.presentation.gui.backends import headless  # noqa: F401
        available.append("headless")
    except ImportError:
        pass

    # Try pyglet (requires pyglet + display)
    try:
        from cube.presentation.gui.backends import pyglet  # noqa: F401
        available.append("pyglet")
    except ImportError:
        pass

    # Try tkinter (requires tk)
    try:
        from cube.presentation.gui.backends import tkinter  # noqa: F401
        available.append("tkinter")
    except ImportError:
        pass

    return available


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --backend option to pytest."""
    parser.addoption(
        "--backend",
        action="store",
        default="headless",
        help="Backend to test: headless, pyglet, tkinter, or 'all' for all available",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "backend(name): mark test to run only with specific backend"
    )
    config.addinivalue_line(
        "markers", "requires_display: mark test as requiring a display (skip in CI)"
    )
    config.addinivalue_line(
        "markers", "requires_animation: mark test as requiring animation support"
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test variants for each backend."""
    if "backend_name" in metafunc.fixturenames:
        backend_option = metafunc.config.getoption("--backend")

        if backend_option == "all":
            backends = get_available_backends()
        else:
            backends = [backend_option]

        # Filter to only available backends
        available = get_available_backends()
        backends = [b for b in backends if b in available]

        if not backends:
            backends = ["headless"]  # Fallback

        metafunc.parametrize("backend_name", backends)


@pytest.fixture
def backend_name(request: pytest.FixtureRequest) -> str:
    """Fixture providing the backend name being tested."""
    return request.param


@pytest.fixture
def renderer(backend_name: str) -> Iterator[Renderer]:
    """Create a renderer for the specified backend."""
    backend = BackendRegistry.get_backend(backend_name)
    r = backend.renderer
    r.setup()
    yield r
    r.cleanup()


@pytest.fixture
def window(backend_name: str) -> Iterator[Window]:
    """Create a window for the specified backend."""
    backend = BackendRegistry.get_backend(backend_name)
    w = backend.create_window(640, 480, "Test Window")
    yield w
    if hasattr(w, 'close'):
        w.close()


@pytest.fixture
def event_loop(backend_name: str) -> Iterator[EventLoop]:
    """Create an event loop for the specified backend."""
    backend = BackendRegistry.get_backend(backend_name)
    loop = backend.create_event_loop()
    yield loop
    if hasattr(loop, 'clear_callbacks'):
        loop.clear_callbacks()


@pytest.fixture
def animation(backend_name: str) -> AnimationBackend | None:
    """Create an animation backend (may be None if not supported)."""
    backend = BackendRegistry.get_backend(backend_name)
    return backend.create_animation()


@pytest.fixture
def gui_components(backend_name: str) -> Iterator[tuple[Renderer, Window, EventLoop, AnimationBackend | None]]:
    """Create all GUI components for the specified backend."""
    backend = BackendRegistry.get_backend(backend_name)

    renderer = backend.renderer
    window = backend.create_window()
    event_loop = backend.create_event_loop()
    animation = backend.create_animation()
    renderer.setup()

    yield renderer, window, event_loop, animation

    renderer.cleanup()
    if hasattr(window, 'close'):
        window.close()


@pytest.fixture
def cube_driver(
    gui_components: tuple[Renderer, Window, EventLoop, AnimationBackend | None],
    backend_name: str,
) -> Iterator[CubeTestDriver]:
    """Create a CubeTestDriver for testing cube operations.

    This fixture provides a high-level interface for cube tests:

        def test_rotation(cube_driver):
            cube_driver.execute("RLU")
            assert not cube_driver.solved

            cube_driver.scramble(seed=42).solve()
            assert cube_driver.solved
    """
    renderer, window, event_loop, animation = gui_components

    cube = Cube(3)
    operator = Operator(cube)

    driver = CubeTestDriver(
        cube=cube,
        operator=operator,
        window=window,
        renderer=renderer,
        event_loop=event_loop,
        animation=animation,
    )

    yield driver


@pytest.fixture
def cube_driver_factory(
    gui_components: tuple[Renderer, Window, EventLoop, AnimationBackend | None],
    backend_name: str,
) -> Callable[[int], CubeTestDriver]:
    """Factory fixture to create CubeTestDriver with custom cube size.

    Usage:
        def test_large_cube(cube_driver_factory):
            driver = cube_driver_factory(5)  # 5x5 cube
            driver.scramble().solve()
            assert driver.solved
    """
    renderer, window, event_loop, animation = gui_components

    def create_driver(cube_size: int = 3) -> CubeTestDriver:
        cube = Cube(cube_size)
        operator = Operator(cube)
        return CubeTestDriver(
            cube=cube,
            operator=operator,
            window=window,
            renderer=renderer,
            event_loop=event_loop,
            animation=animation,
        )

    return create_driver
