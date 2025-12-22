"""
AbstractAppWindow - Abstract base class for AppWindow protocol.

This module provides the common logic that all backend AppWindow implementations
share. Backend-specific implementations (PygletAppWindow, TkinterAppWindow, etc.)
inherit from this class and implement the abstract rendering methods.

Key Handling Architecture:
- All backends call handle_key() after converting native keys to abstract Keys
- handle_key() uses lookup_command() to find the Command for the key
- Command.execute() performs the action
"""

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from cube.application.exceptions.app_exceptions import AppExit
from cube.domain.algs import Alg, Algs
from cube.presentation.gui.commands import Command, CommandContext
from cube.presentation.gui.key_bindings import lookup_command
from cube.presentation.gui.types import Color4

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.application.protocols import AnimatableViewer
    from cube.presentation.gui.factory import GUIBackend
    from cube.presentation.gui.protocols import Renderer


@dataclass
class TextLabel:
    """Backend-agnostic text label definition.

    Backends convert these to their native text rendering format.
    """
    text: str
    x: int
    y: int
    font_size: int = 10
    color: Color4 = (255, 255, 255, 255)
    bold: bool = False


class AppWindowBase(ABC):
    """Base class for application windows.

    Provides shared logic for:
    - Keyboard input handling (uses lookup_command + command.execute)
    - Mouse input handling (delegates to main_g_mouse)
    - Key sequence injection
    - GUI element coordination
    - Text label building

    Subclasses must implement abstract methods for:
    - run() - Main event loop
    - close() - Close window
    - _render_text() - Render text labels
    - _request_redraw() - Request window redraw
    """

    # Pyglet cursor constant (for compatibility with keyboard handler)
    CURSOR_WAIT = "wait"

    def __init__(self, app: "AbstractApp", backend: "GUIBackend"):
        """Initialize the base window.

        Args:
            app: Application instance providing cube, operator, solver
            backend: GUI backend for rendering and events
        """
        self._app = app
        self._backend = backend
        self._viewer: "AnimatableViewer | None" = None
        self._animation_manager = app.am

        # Keyboard handler state
        self._last_edge_solve_count: int = 0

        # Connect animation manager to this window
        if self._animation_manager:
            self._animation_manager.set_window(self)  # type: ignore[arg-type]

        # Text labels built by update_text()
        self._status_labels: list[TextLabel] = []
        self._animation_labels: list[TextLabel] = []

    @property
    def app(self) -> "AbstractApp":
        """Access the application instance."""
        return self._app

    @property
    def viewer(self) -> "AnimatableViewer":
        """Access the cube viewer (AnimatableViewer protocol)."""
        if self._viewer is None:
            raise RuntimeError("Viewer not initialized")
        return self._viewer

    @property
    def renderer(self) -> "Renderer":
        """Access the renderer."""
        return self._backend.renderer

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running."""
        return bool(self._animation_manager and self._animation_manager.animation_running())

    def cleanup(self) -> None:
        """Clean up resources when shutting down.

        Handles viewer cleanup if viewer exists. Subclasses can override
        to add additional cleanup, but should call super().cleanup().
        """
        if self._viewer is not None:
            self._viewer.cleanup()

    @abstractmethod
    def run(self) -> None:
        """Run the main event loop. Blocks until close() is called."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the window and stop the event loop."""
        ...

    @abstractmethod
    def _request_redraw(self) -> None:
        """Request window redraw on next frame."""
        ...

    @abstractmethod
    def set_mouse_visible(self, visible: bool) -> None:
        """Show or hide the mouse cursor."""
        ...

    def get_system_mouse_cursor(self, cursor_type: str) -> None:
        """Get a system mouse cursor. Returns None for non-pyglet backends."""
        return None

    def set_mouse_cursor(self, cursor: object) -> None:
        """Set the mouse cursor. No-op for non-pyglet backends."""
        pass

    def update_gui_elements(self) -> None:
        """Update all GUI elements after state changes.

        Coordinates viewer update, animation manager update, and text updates.
        """
        if self._viewer:
            self._viewer.update()

        if self._animation_manager:
            self._animation_manager.update_gui_elements()

        self._update_animation_text()

        if not self.animation_running:
            self._update_status_text()

        self._request_redraw()

    def handle_key(self, symbol: int, modifiers: int) -> None:
        """Handle a key press event - PROTOCOL METHOD.

        This is the protocol method that ALL backends call after converting
        native keys to abstract Keys. Subclasses can override to add
        backend-specific behavior (e.g., redraw after key press).

        Flow:
            Native Event → Backend native handler → convert → handle_key(symbol, modifiers)
                         → lookup_command() → command.execute()

        Args:
            symbol: Key code (from Keys enum) - must be abstract, not native
            modifiers: Modifier flags (from Modifiers)
        """
        cmd = lookup_command(symbol, modifiers, self.animation_running)
        if cmd:
            self.inject_command(cmd)

    def handle_mouse_drag(self, x: int, y: int, dx: int, dy: int,
                          buttons: int, modifiers: int) -> None:
        """Handle mouse drag event.

        Args:
            x, y: Current mouse position
            dx, dy: Movement delta
            buttons: Mouse button flags
            modifiers: Modifier flags
        """
        # Lazy import to avoid circular dependency
        from cube.presentation.gui.backends.pyglet2 import main_g_mouse
        main_g_mouse.on_mouse_drag(self, x, y, dx, dy, buttons, modifiers)  # type: ignore[arg-type]

    def handle_mouse_press(self, x: int, y: int, modifiers: int) -> None:
        """Handle mouse press event.

        Args:
            x, y: Mouse position
            modifiers: Modifier flags
        """
        # Lazy import to avoid circular dependency
        from cube.presentation.gui.backends.pyglet2 import main_g_mouse
        main_g_mouse.on_mouse_press(self, self._app.vs, x, y, modifiers)  # type: ignore[arg-type]

    def handle_mouse_release(self) -> None:
        """Handle mouse release event."""
        # Lazy import to avoid circular dependency
        from cube.presentation.gui.backends.pyglet2 import main_g_mouse
        main_g_mouse.on_mouse_release()

    def handle_mouse_scroll(self, scroll_y: float) -> None:
        """Handle mouse scroll event.

        Args:
            scroll_y: Vertical scroll amount
        """
        # Lazy import to avoid circular dependency
        from cube.presentation.gui.backends.pyglet2 import main_g_mouse
        main_g_mouse.on_mouse_scroll(self, scroll_y)  # type: ignore[arg-type]

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press.

        Args:
            key: Key code (from Keys enum)
            modifiers: Modifier flags
        """
        self.handle_key(key, modifiers)

    def inject_command(self, command: Command) -> None:
        """Inject a command directly.

        Preferred method for testing and automation - bypasses key handling
        and directly executes the command. Type-safe with IDE autocomplete.

        Args:
            command: Command instance to execute

        Example:
            window.inject_command(Commands.SCRAMBLE_1)
            window.inject_command(Commands.SOLVE_ALL)
            window.inject_command(Commands.QUIT)
        """
        try:
            ctx = CommandContext.from_window(self)  # type: ignore[arg-type]
            result = command.execute(ctx)
            if not result.no_gui_update:
                self.update_gui_elements()
        except AppExit:
            if self._app.config.gui_test_mode:
                self.close()
                raise
            else:
                self._app.set_error("Asked to stop")
                self.update_gui_elements()
        except Exception as e:
            cfg = self._app.config
            if cfg.gui_test_mode and cfg.quit_on_error_in_test_mode:
                self.close()
                raise
            else:
                traceback.print_exc()
                msg = str(e)
                error_text = "Some error occurred:"
                if msg:
                    error_text += msg
                self._app.set_error(error_text)
                self.update_gui_elements()

    def _update_status_text(self) -> None:
        """Build status text labels.

        Updates self._status_labels with TextLabel objects that backends render.
        """
        app = self._app
        slv = app.slv
        cube = app.cube
        vs = app.vs
        op = app.op

        def _b(b: bool) -> str:
            return "On" if b else "Off"

        self._status_labels.clear()
        y = 10

        # Status line
        self._status_labels.append(TextLabel(
            f"Status:{slv.status}", x=10, y=y, font_size=10
        ))
        y += 20

        # History (simplified)
        h = Algs.simplify(*op.history(remove_scramble=True))
        sh = str(h)[-120:]
        self._status_labels.append(TextLabel(
            f"History(simplified): #{h.count()}  {sh}", x=10, y=y, font_size=10
        ))
        y += 20

        # History (full)
        hist = op.history()
        sh = str(h)[-70:]
        self._status_labels.append(TextLabel(
            f"History: #{Algs.count(*hist)}  {sh}", x=10, y=y, font_size=10
        ))
        y += 20

        # Recording state
        is_recording = op.is_recording
        s = f"Recording: {_b(is_recording)}"
        recording: Sequence[Alg] | None = vs.last_recording
        if recording is not None:
            sh = str(recording)[-70:]
            s += f", #{Algs.count(*recording)}  {sh}"
        self._status_labels.append(TextLabel(s, x=10, y=y, font_size=10))
        y += 20

        # Help line
        help_text = "R L U S/Z/F B D  M/X/R E/Y/U (SHIFT-INv), ?-Solve, Clear, Q 0-9 scramble1, <undo, Test"
        self._status_labels.append(TextLabel(help_text, x=10, y=y, font_size=10))
        y += 20

        # Sanity and error
        s = f"Sanity:{cube.is_sanity(force_check=True)}"
        if app.error:
            s += f", Error:{app.error}"
        self._status_labels.append(TextLabel(
            s, x=10, y=y, font_size=10, color=(255, 0, 0, 255), bold=True
        ))
        y += 20

        # Animation settings
        s = f"Animation:{_b(op.animation_enabled)}"
        s += f", [{vs.get_speed_index}] {vs.get_speed.get_speed()}"
        s += f", Sanity check:{_b(app.config.check_cube_sanity)}"
        s += f", Debug={_b(slv.is_debug_config_mode)}"
        s += f", SS Mode:{_b(vs.single_step_mode)}"
        # Add lighting info if backend supports it
        brightness = self.get_brightness()
        if brightness is not None:
            s += f", Light:{brightness:.0%}"
        background = self.get_background()
        if background is not None and background > 0:
            s += f", BG:{background:.0%}"
        self._status_labels.append(TextLabel(
            s, x=10, y=y, font_size=10, color=(255, 255, 0, 255), bold=True
        ))
        y += 20

        # Solver info
        s = f"Solver:{slv.name},"
        s += f"S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"
        s += f", Slices  [{vs.slice_start}, {vs.slice_stop}]"
        s += f", {vs.slice_alg(cube, Algs.L)}"
        s += f", {vs.slice_alg(cube, Algs.M)}"
        self._status_labels.append(TextLabel(
            s, x=10, y=y, font_size=10, color=(0, 255, 0, 255), bold=True
        ))
        y += 20

        # Pause message
        if vs.paused_on_single_step_mode:
            self._status_labels.append(TextLabel(
                f"PAUSED: {vs.paused_on_single_step_mode}. press space",
                x=10, y=y, font_size=15, color=(0, 255, 0, 255), bold=True
            ))

    def _update_animation_text(self) -> None:
        """Build animation text labels.

        Updates self._animation_labels with TextLabel objects.
        """
        vs = self._app.vs
        self._animation_labels.clear()

        animation_text_props = self._app.config.animation_text
        at = vs.animation_text
        for i in range(3):
            prop = animation_text_props[i]
            line = at.get_line(i)
            if line:
                x = prop[0]
                # Note: y needs window height - backends handle this
                y_from_top = prop[1]
                size = prop[2]
                color: Color4 = prop[3]
                bold: bool = prop[4]
                self._animation_labels.append(TextLabel(
                    line, x=x, y=y_from_top, font_size=size, color=color, bold=bold
                ))

    @property
    def status_labels(self) -> list[TextLabel]:
        """Get current status text labels."""
        return self._status_labels

    @property
    def animation_labels(self) -> list[TextLabel]:
        """Get current animation text labels."""
        return self._animation_labels

    def adjust_brightness(self, delta: float) -> float | None:
        """Adjust ambient light brightness (if supported by backend).

        Default implementation returns None (not supported).
        Override in backends with lighting support (e.g., pyglet2).

        Args:
            delta: Amount to adjust (positive = brighter, negative = darker)

        Returns:
            New brightness level (0.0-1.0) if supported, None otherwise.
        """
        return None

    def get_brightness(self) -> float | None:
        """Get current brightness level (if supported by backend).

        Default implementation returns None (not supported).
        Override in backends with lighting support (e.g., pyglet2).

        Returns:
            Current brightness level (0.0-1.0) if supported, None otherwise.
        """
        return None

    def adjust_background(self, delta: float) -> float | None:
        """Adjust background gray level (if supported by backend).

        Default implementation returns None (not supported).
        Override in backends with background control (e.g., pyglet2).

        Args:
            delta: Amount to adjust (positive = lighter, negative = darker)

        Returns:
            New background level (0.0-0.5) if supported, None otherwise.
        """
        return None

    def get_background(self) -> float | None:
        """Get current background gray level (if supported by backend).

        Default implementation returns None (not supported).
        Override in backends with background control (e.g., pyglet2).

        Returns:
            Current background level (0.0-0.5) if supported, None otherwise.
        """
        return None

    def next_texture_set(self) -> str | None:
        """Cycle to the next texture set (if supported by backend).

        Default implementation returns None (not supported).
        Override in backends with texture support (e.g., pyglet2).

        Returns:
            Name of new texture set, "solid" if None, or None if not supported.
        """
        return None

    def prev_texture_set(self) -> str | None:
        """Cycle to the previous texture set (if supported by backend).

        Default implementation returns None (not supported).
        Override in backends with texture support (e.g., pyglet2).

        Returns:
            Name of new texture set, "solid" if None, or None if not supported.
        """
        return None

    def toggle_texture(self) -> bool:
        """Toggle texture mode on/off (if supported by backend).

        Default implementation returns False (not supported).
        Override in backends with texture support (e.g., pyglet2).

        Returns:
            True if textures are now enabled, False otherwise.
        """
        return False

    def load_texture_set(self, directory: str) -> int:
        """Load all face textures from a directory (if supported by backend).

        Default implementation returns 0 (not supported).
        Override in backends with texture support (e.g., pyglet2).

        Args:
            directory: Path to directory containing face texture images

        Returns:
            Number of textures successfully loaded (0-6).
        """
        return 0
