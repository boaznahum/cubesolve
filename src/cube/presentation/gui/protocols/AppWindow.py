"""
AppWindow protocol definition.

This protocol defines the high-level application window interface that
combines GUI window functionality with application logic. All backends
(pyglet, tkinter, console, headless) implement this protocol to enable
a unified entry point (main_any_backend.py).
"""

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.presentation.viewer.GCubeViewer import GCubeViewer
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.presentation.gui.Command import Command


@runtime_checkable
class AppWindow(Protocol):
    """Protocol for application window - works with any backend.

    This is the high-level window interface that combines:
    - GUI window (rendering, events)
    - Application logic (cube, operator, solver)
    - Animation integration

    All backends implement this to enable main_any_backend.py.
    """

    @property
    def app(self) -> "AbstractApp":
        """Access the application instance.

        Provides access to cube, operator, solver, animation manager.
        """
        ...

    @property
    def viewer(self) -> "GCubeViewer":
        """Access the cube viewer.

        Used for rendering and cleanup.
        """
        ...

    @property
    def renderer(self) -> "Renderer":
        """Access the renderer.

        Backend-specific renderer implementation.
        """
        ...

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running.

        Returns:
            True if an animation is in progress, False otherwise.
        """
        ...

    def run(self) -> None:
        """Run the main event loop.

        This blocks until the window is closed or close() is called.
        """
        ...

    def close(self) -> None:
        """Close the window and stop the event loop.

        Triggers cleanup and exits run().
        """
        ...

    def cleanup(self) -> None:
        """Clean up resources when shutting down.

        Called after run() exits to release resources (textures, display lists, etc.).
        Each backend handles its own cleanup (viewer cleanup if applicable).
        """
        ...

    def update_gui_elements(self) -> None:
        """Update all GUI elements.

        Called after state changes to refresh:
        - Status text
        - Animation text
        - Cube display
        """
        ...

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press.

        Used for testing and automation.

        Args:
            key: Key code (from Keys enum)
            modifiers: Modifier flags (from Modifiers)
        """
        ...

    def inject_command(self, command: "Command") -> None:
        """Inject a command directly.

        Preferred method for testing and automation - bypasses key handling
        and directly dispatches the command.

        Args:
            command: Command enum value to execute

        Example:
            window.inject_command(Command.SCRAMBLE_1)
            window.inject_command(Command.SOLVE_ALL)
            window.inject_command(Command.QUIT)
        """
        ...

    def set_mouse_visible(self, visible: bool) -> None:
        """Show or hide the mouse cursor.

        Args:
            visible: True to show, False to hide
        """
        ...

    def get_opengl_info(self) -> str:
        """Get OpenGL version and renderer information.

        Returns:
            Formatted string with OpenGL info, or empty string if not applicable.
            For OpenGL backends (pyglet, pyglet2): version, GLSL, renderer, vendor.
            For non-OpenGL backends (tkinter, console, headless): empty string.
        """
        ...

    def adjust_brightness(self, delta: float) -> float | None:
        """Adjust ambient light brightness (if supported by backend).

        Only implemented by backends with lighting support (pyglet2).
        Other backends return None (no-op).

        Args:
            delta: Amount to adjust (positive = brighter, negative = darker)

        Returns:
            New brightness level (0.0-1.0) if supported, None otherwise.
        """
        ...

    def get_brightness(self) -> float | None:
        """Get current brightness level (if supported by backend).

        Only implemented by backends with lighting support (pyglet2).
        Other backends return None.

        Returns:
            Current brightness level (0.0-1.0) if supported, None otherwise.
        """
        ...

    def adjust_background(self, delta: float) -> float | None:
        """Adjust background gray level (if supported by backend).

        Only implemented by backends with background control (pyglet2).
        Other backends return None (no-op).

        Args:
            delta: Amount to adjust (positive = lighter, negative = darker)

        Returns:
            New background level (0.0-0.5) if supported, None otherwise.
        """
        ...

    def get_background(self) -> float | None:
        """Get current background gray level (if supported by backend).

        Only implemented by backends with background control (pyglet2).
        Other backends return None.

        Returns:
            Current background level (0.0-0.5) if supported, None otherwise.
        """
        ...

    def toggle_texture_mode(self) -> bool | None:
        """Toggle texture rendering mode on/off (if supported by backend).

        Only implemented by backends with texture support (pyglet2).
        Other backends return None (no-op).

        Returns:
            New texture mode state (True=enabled, False=disabled) if supported, None otherwise.
        """
        ...

    def load_texture_set(self, directory: str) -> int:
        """Load all face textures from a directory (if supported by backend).

        Expects files named F.png, B.png, R.png, L.png, U.png, D.png.
        Only implemented by backends with texture support (pyglet2).
        Other backends return 0 (no textures loaded).

        Args:
            directory: Path to directory containing face texture images

        Returns:
            Number of textures successfully loaded (0-6).
        """
        ...
