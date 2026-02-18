"""
AppWindow protocol definition.

This protocol defines the high-level application window interface that
combines GUI window functionality with application logic. All backends
(pyglet, tkinter, console, headless) implement this protocol to enable
a unified entry point (main_any_backend.py).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.application.protocols.AnimatableViewer import AnimatableViewer
    from cube.presentation.gui.commands import Command, CommandSequence
    from cube.presentation.gui.protocols.Renderer import Renderer


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
    def width(self) -> int:
        """Window width in pixels."""
        ...

    @property
    def height(self) -> int:
        """Window height in pixels."""
        ...

    @property
    def app(self) -> "AbstractApp":
        """Access the application instance.

        Provides access to cube, operator, solver, animation manager.
        """
        ...

    @property
    def viewer(self) -> "AnimatableViewer":
        """Access the cube viewer.

        Returns AnimatableViewer protocol - implemented by both
        GCubeViewer (legacy OpenGL) and ModernGLCubeViewer (modern OpenGL).
        """
        ...

    @property
    def renderer(self) -> "Renderer":
        """Access the renderer.

        Backend-specific renderer implementation.
        """
        ...

    # State for edge solve tracking (used by SOLVE_EDGES command)
    _last_edge_solve_count: int

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
            command: Command instance to execute

        Example:
            window.inject_command(Commands.SCRAMBLE_1)
            window.inject_command(Commands.SOLVE_ALL)
            window.inject_command(Commands.QUIT)
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

    def next_texture_set(self) -> str | None:
        """Cycle to the next texture set (if supported by backend).

        Cycles through TEXTURE_SETS from config (can include None for solid colors).
        Only implemented by backends with texture support (pyglet2).
        Other backends return None (no-op).

        Returns:
            Name of new texture set, "solid" if None/disabled, or None if not supported.
        """
        ...

    def prev_texture_set(self) -> str | None:
        """Cycle to the previous texture set (if supported by backend).

        Cycles backwards through TEXTURE_SETS from config.
        Only implemented by backends with texture support (pyglet2).
        Other backends return None (no-op).

        Returns:
            Name of new texture set, "solid" if None/disabled, or None if not supported.
        """
        ...

    def toggle_texture(self) -> bool:
        """Toggle texture mode on/off (if supported by backend).

        Only implemented by backends with texture support (pyglet2).
        Other backends return False (no-op).

        Returns:
            True if textures are now enabled, False otherwise.
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

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run after a delay (non-blocking).

        The GUI remains responsive during the wait. The callback receives
        the actual elapsed time as its argument.

        Args:
            callback: Function to call after delay, receives dt (elapsed time)
            delay: Time in seconds to wait before calling

        Example:
            def on_timeout(dt: float) -> None:
                print(f"Waited {dt} seconds")
                window.inject_command(Commands.QUIT)

            window.schedule_once(on_timeout, 3.0)  # Quit after 3 seconds
        """
        ...

    def inject_command_sequence(
        self,
        commands: "CommandSequence | list[Command]",
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        """Inject a sequence of commands, handling delays from SleepCommand.

        Commands are executed in order. If a command returns delay_next_command > 0,
        the remaining commands are scheduled to run after that delay.
        The GUI remains responsive during delays.

        Args:
            commands: Sequence of commands to execute
            on_complete: Optional callback when all commands complete

        Example:
            from cube.presentation.gui.commands import Commands
            window.inject_command_sequence(
                Commands.Sleep(3) + Commands.SCRAMBLE_1 + Commands.QUIT
            )
        """
        ...

    def show_popup(self, title: str, lines: list[str],
                   line_colors: list[tuple[int, int, int, int]] | None = None) -> None:
        """Show a modal text popup overlay.

        Displays a scrollable text panel on top of the 3D view.
        While visible, keyboard/mouse events are intercepted by the popup.
        Close with Escape or OK button.

        Args:
            title: Title text displayed at top of panel
            lines: Text lines to display (scrollable)
            line_colors: Optional per-line RGBA color tuples
        """
        ...
