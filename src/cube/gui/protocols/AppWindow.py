"""
AppWindow protocol definition.

This protocol defines the high-level application window interface that
combines GUI window functionality with application logic. All backends
(pyglet, tkinter, console, headless) implement this protocol to enable
a unified entry point (main_any_backend.py).
"""

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.app.AbstractApp import AbstractApp
    from cube.viewer.GCubeViewer import GCubeViewer
    from cube.gui.protocols.Renderer import Renderer
    from cube.gui.Command import Command


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
