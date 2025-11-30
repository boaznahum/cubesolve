"""
Unified entry point for the Cube Solver application.

This module provides a single entry point that can run with any registered
GUI backend: pyglet, tkinter, console, or headless.

Usage:
    python -m cube.main_any_backend                    # Default (pyglet)
    python -m cube.main_any_backend --backend=tkinter  # Tkinter backend
    python -m cube.main_any_backend --backend=console  # Console mode
    python -m cube.main_any_backend --backend=headless # Headless testing
    python -m cube.main_any_backend --backend=headless --key-sequence="1?Q"

Available backends:
    - pyglet:   OpenGL-based 3D rendering (requires pyglet)
    - tkinter:  2D canvas-based rendering (built-in)
    - console:  Text-based console output (built-in)
    - headless: No output, for testing (built-in)
"""

import argparse
import sys
from typing import TYPE_CHECKING

from cube.app.AbstractApp import AbstractApp
from cube.gui import BackendRegistry

if TYPE_CHECKING:
    from cube.gui.protocols import AppWindow


def _import_backend(backend_name: str) -> None:
    """Import the backend module to register it.

    Args:
        backend_name: Name of the backend to import.

    Raises:
        ImportError: If the backend module cannot be imported.
    """
    backend_modules = {
        "pyglet": "cube.gui.backends.pyglet",
        "tkinter": "cube.gui.backends.tkinter",
        "console": "cube.gui.backends.console",
        "headless": "cube.gui.backends.headless",
    }

    module_name = backend_modules.get(backend_name)
    if module_name:
        __import__(module_name)


def create_app_window(
    app: AbstractApp,
    backend_name: str = "pyglet",
    width: int = 720,
    height: int = 720,
    title: str = "Cube Solver",
) -> "AppWindow":
    """Create an AppWindow with the specified backend.

    This is the main factory function for creating application windows.
    Delegates to GUIBackend.create_app_window() which handles animation manager wiring.

    Args:
        app: Application instance with cube, operator, solver.
        backend_name: Backend to use ("pyglet", "tkinter", "console", "headless").
        width: Window width in pixels (ignored for console/headless).
        height: Window height in pixels (ignored for console/headless).
        title: Window title.

    Returns:
        An AppWindow instance for the specified backend.

    Raises:
        ImportError: If the backend is not available.
        ValueError: If the backend is not recognized.

    Example:
        >>> app = AbstractApp.create()
        >>> window = create_app_window(app, "tkinter")
        >>> window.run()
    """
    # Import backend to register it
    _import_backend(backend_name)

    # Get backend from registry and create window
    # GUIBackend.create_app_window() handles animation manager wiring
    backend = BackendRegistry.get_backend(backend_name)
    return backend.create_app_window(app, width, height, title)


def run_with_backend(
    backend_name: str = "pyglet",
    *,
    width: int = 720,
    height: int = 720,
    title: str = "Cube Solver",
    cube_size: int | None = None,
    animation: bool = True,
    key_sequence: str | None = None,
) -> int:
    """Run the application with the specified backend.

    This is the preferred programmatic entry point. Use this instead of
    manipulating sys.argv.

    Args:
        backend_name: Backend to use ("pyglet", "tkinter", "console", "headless").
        width: Window width in pixels (ignored for console/headless).
        height: Window height in pixels (ignored for console/headless).
        title: Window title.
        cube_size: Cube size (default: 3).
        animation: Enable animation (default: True).
        key_sequence: Key sequence to inject (for testing).

    Returns:
        Exit code (0 for success, 1 for error).

    Example:
        >>> from cube.main_any_backend import run_with_backend
        >>> run_with_backend("tkinter")  # Run with tkinter
        >>> run_with_backend("headless", key_sequence="1?Q")  # Test sequence
    """
    # Create application
    app = AbstractApp.create_non_default(
        cube_size=cube_size,
        animation=animation
    )

    window = None
    try:
        # Create window with specified backend
        window = create_app_window(
            app,
            backend_name=backend_name,
            width=width,
            height=height,
            title=title,
        )

        window.set_mouse_visible(True)

        # Inject key sequence if provided
        if key_sequence:
            window.inject_key_sequence(key_sequence)

        # Run the event loop
        window.run()

    except ImportError as e:
        print(f"Error: Backend '{backend_name}' is not available: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 0

    finally:
        # Cleanup
        if window is not None and window.viewer:
            window.viewer.cleanup()

    return 0


def main(args: list[str] | None = None) -> int:
    """Main entry point for command-line usage.

    Parses command-line arguments and delegates to run_with_backend().

    Args:
        args: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        description="Rubik's Cube Solver with multiple backend support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--backend", "-b",
        choices=["pyglet", "tkinter", "console", "headless"],
        default="pyglet",
        help="GUI backend to use (default: pyglet)"
    )
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=720,
        help="Window width in pixels (default: 720)"
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=720,
        help="Window height in pixels (default: 720)"
    )
    parser.add_argument(
        "--title", "-t",
        default="Cube Solver",
        help="Window title"
    )
    parser.add_argument(
        "--cube-size", "-s",
        type=int,
        default=None,
        help="Cube size (default: 3)"
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable animation"
    )
    parser.add_argument(
        "--key-sequence", "-k",
        default=None,
        help="Key sequence to inject (for testing). Example: '1?Q' = scramble, solve, quit"
    )

    parsed = parser.parse_args(args)

    return run_with_backend(
        backend_name=parsed.backend,
        width=parsed.width,
        height=parsed.height,
        title=parsed.title,
        cube_size=parsed.cube_size,
        animation=not parsed.no_animation,
        key_sequence=parsed.key_sequence,
    )


if __name__ == "__main__":
    sys.exit(main())
