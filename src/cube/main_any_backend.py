"""
Unified entry point for the Cube Solver application.

This module provides a single entry point that can run with any registered
GUI backend: pyglet, tkinter, console, or headless.

Usage:
    python -m cube.main_any_backend                    # Default (pyglet)
    python -m cube.main_any_backend --backend=tkinter  # Tkinter backend
    python -m cube.main_any_backend --backend=console  # Console mode
    python -m cube.main_any_backend --backend=headless # Headless testing
    python -m cube.main_any_backend --commands="SCRAMBLE_1,SOLVE_ALL,QUIT"

Available backends:
    - pyglet:   OpenGL-based 3D rendering (requires pyglet)
    - tkinter:  2D canvas-based rendering (built-in)
    - console:  Text-based console output (built-in)
    - headless: No output, for testing (built-in)
"""

import argparse
import re
import sys
from typing import TYPE_CHECKING

from cube.application.AbstractApp import AbstractApp
from cube.presentation.gui import BackendRegistry
from cube.presentation.gui.Command import Command

if TYPE_CHECKING:
    from cube.presentation.gui.protocols import AppWindow


def _inject_commands(window: "AppWindow", commands_str: str) -> None:
    """Parse and inject commands from a string.

    Args:
        window: The application window to inject commands into.
        commands_str: Comma or + separated command names.
            Example: "SCRAMBLE_1,SOLVE_ALL,QUIT" or "SPEED_UP+SPEED_UP+SCRAMBLE_1"

    Raises:
        ValueError: If a command name is invalid.
    """
    # Split by comma or +
    command_names = re.split(r'[,+]', commands_str)

    for name in command_names:
        name = name.strip()
        if not name:
            continue

        try:
            cmd = Command[name]
            window.inject_command(cmd)
        except KeyError:
            raise ValueError(f"Unknown command: {name}. Use --list-commands to see available commands.")


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
    # Get backend from registry and create window
    # GUIBackendFactory.create_app_window() handles animation manager wiring
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
    commands: str | None = None,
    debug_all: bool = False,
    quiet_all: bool = False,
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
        commands: Command sequence to inject (comma or + separated).
            Example: "SCRAMBLE_1,SOLVE_ALL,QUIT" or "SPEED_UP+SPEED_UP+SCRAMBLE_1"
        debug_all: Enable debug_all mode for verbose logging (default: False).
        quiet_all: Suppress all debug output (default: False).

    Returns:
        Exit code (0 for success, 1 for error).

    Note:
        Celebration effects are configured via config.py:
        - CELEBRATION_EFFECT: Effect name ("confetti", "victory_spin", etc.)
        - CELEBRATION_ENABLED: Whether effects are enabled
        - CELEBRATION_DURATION: Effect duration in seconds

    Example:
        >>> from cube.main_any_backend import run_with_backend
        >>> run_with_backend("tkinter")  # Run with tkinter
        >>> run_with_backend("headless", commands="SCRAMBLE_1,SOLVE_ALL,QUIT")
    """
    # Create application
    app = AbstractApp.create_non_default(
        cube_size=cube_size,
        animation=animation,
        debug_all=debug_all,
        quiet_all=quiet_all,
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

        # Inject commands if provided
        if commands:
            _inject_commands(window, commands)

        # Debug: dump state before main loop (backend/OpenGL info always shown)
        app.vs.debug_dump(
            app.cube,
            "Before Main Loop",
            opengl_info=window.get_opengl_info(),
            backend_name=backend_name,
        )

        # Run the event loop
        window.run()

        # Debug: dump state after main loop
        app.vs.debug_dump(app.cube, "After Main Loop", backend_name=backend_name)

    except ImportError as e:
        print(f"Error: Backend '{backend_name}' is not available: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 0

    finally:
        # Cleanup
        if window is not None:
            window.cleanup()

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
        choices=["pyglet", "pyglet2", "tkinter", "console", "headless"],
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
        "--commands", "-c",
        default=None,
        help="Commands to inject (comma or + separated). Example: 'SCRAMBLE_1,SOLVE_ALL,QUIT'"
    )
    parser.add_argument(
        "--debug-all",
        action="store_true",
        help="Enable debug_all mode for verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all debug output"
    )

    parsed = parser.parse_args(args)

    return run_with_backend(
        backend_name=parsed.backend,
        width=parsed.width,
        height=parsed.height,
        title=parsed.title,
        cube_size=parsed.cube_size,
        animation=not parsed.no_animation,
        commands=parsed.commands,
        debug_all=parsed.debug_all,
        quiet_all=parsed.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
