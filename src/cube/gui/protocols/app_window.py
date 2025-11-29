"""
AppWindow protocol definition.

This protocol defines the high-level application window interface that
combines GUI window functionality with application logic. All backends
(pyglet, tkinter, console, headless) implement this protocol to enable
a unified entry point (main_any_backend.py).
"""

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.app.abstract_ap import AbstractApp
    from cube.viewer.viewer_g import GCubeViewer
    from cube.gui.protocols.renderer import Renderer


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

    def inject_key_sequence(self, sequence: str) -> None:
        """Inject a sequence of key presses.

        Used for testing and automation.
        Common sequences:
        - "RURU" - Manual moves
        - "1" - Scramble preset 1
        - "?" - Solve
        - "Q" - Quit

        Args:
            sequence: String of key characters to inject
        """
        ...

    def set_mouse_visible(self, visible: bool) -> None:
        """Show or hide the mouse cursor.

        Args:
            visible: True to show, False to hide
        """
        ...
