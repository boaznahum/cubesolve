"""
Pytest configuration for GUI tests.

Provides command-line options for GUI test configuration:
- --animate: Enable animations during testing
- --speed-up: Number of times to increase animation speed (default: 3)
- --backend: Backend to use for tests (pyglet, headless, console, or 'all')
"""

import pytest


def _is_tkinter_available() -> bool:
    """Check if tkinter is properly installed and usable."""
    try:
        import tkinter as tk
        # Try to create a Tk instance to verify Tcl/Tk is properly installed
        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


# Cache the result at module load time
_TKINTER_AVAILABLE = _is_tkinter_available()


def pytest_addoption(parser):
    """Add custom command-line options for GUI tests."""
    parser.addoption(
        "--animate",
        action="store_true",
        default=True,
        help="Enable animations during GUI tests (default: on)"
    )
    parser.addoption(
        "--speed-up",
        action="store",
        type=int,
        default=3,
        help="Number of times to increase animation speed (default: 3)"
    )
    # Check if option already exists (may be added by tests/backends/conftest.py)
    try:
        parser.addoption(
            "--backend",
            action="store",
            default="all",
            help="Backend to use: pyglet2, headless, console, or 'all' (default: all)"
        )
    except ValueError:
        pass  # Option already added by another conftest


@pytest.fixture
def enable_animation(request) -> bool:
    """Fixture that returns True if --animate flag is passed (default: True)."""
    return request.config.getoption("--animate")


@pytest.fixture
def speed_up_count(request) -> int:
    """Fixture that returns the number of speed-up key presses."""
    return request.config.getoption("--speed-up")


def pytest_generate_tests(metafunc):
    """Generate test variants for different backends.

    If --backend=all, parametrize tests with all available backends.
    If specific backend is given, use only that backend.
    """
    if "backend" in metafunc.fixturenames:
        backend_option = metafunc.config.getoption("--backend")

        if backend_option == "all":
            # Run with all available backends
            # Note: pyglet (legacy GL) removed - doesn't work with pyglet 2.0
            # Use pyglet2 backend instead which uses modern OpenGL
            backends = ["pyglet2", "headless", "console", "web"]
            # Only include tkinter if it's properly installed
            if _TKINTER_AVAILABLE:
                backends.append("tkinter")
        else:
            # Single backend specified
            backends = [backend_option]

        metafunc.parametrize("backend", backends)
