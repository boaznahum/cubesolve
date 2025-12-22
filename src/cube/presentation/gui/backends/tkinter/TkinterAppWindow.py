"""
Tkinter AppWindow implementation.

Provides the Tkinter-specific AppWindow that uses TkinterWindow
and AppWindowBase for shared logic.
"""

from cube.application.AbstractApp import AbstractApp
from cube.application.animation.AnimationManager import AnimationWindow
from cube.presentation.gui.factory import GUIBackend
from cube.presentation.gui.protocols import AppWindow
from cube.presentation.gui.protocols.AppWindowBase import AppWindowBase
from cube.presentation.viewer.GCubeViewer import GCubeViewer

from cube.presentation.gui.backends.tkinter.TkinterWindow import TkinterWindow
from cube.presentation.gui.backends.tkinter.TkinterRenderer import TkinterRenderer
from cube.presentation.gui.backends.tkinter.TkinterEventLoop import TkinterEventLoop


class TkinterAppWindow(AppWindowBase, AnimationWindow, AppWindow):
    """Tkinter-specific AppWindow implementation.

    Inherits from AppWindow protocol for PyCharm visibility.
    Uses TkinterWindow for display and AbstractAppWindow for shared logic.
    """

    def __init__(
        self,
        app: AbstractApp,
        width: int,
        height: int,
        title: str,
        backend: GUIBackend,
    ):
        """Initialize the Tkinter AppWindow.

        Args:
            app: Application instance (cube, operator, solver)
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
            backend: GUI backend for rendering
        """
        # Initialize base class
        super().__init__(app, backend)

        # Create Tkinter window
        self._tk_window = TkinterWindow(width, height, title)

        # Get and configure renderer
        self._renderer: TkinterRenderer = backend.renderer  # type: ignore
        self._renderer.set_canvas(self._tk_window.canvas)

        # Configure event loop with root window
        self._event_loop: TkinterEventLoop = backend.event_loop  # type: ignore
        self._event_loop.set_root(self._tk_window.root)

        # Initialize renderer
        self._renderer.setup()
        self._renderer.view.set_projection(width, height)

        # Create viewer
        self._viewer = GCubeViewer(app.cube, app.vs, renderer=self._renderer)

        # Set up event handlers
        self._setup_handlers()

        # Initial draw
        self._draw()

    def _setup_handlers(self) -> None:
        """Set up Tkinter event handlers."""
        self._tk_window.set_draw_handler(self._draw)
        self._tk_window.set_resize_handler(self._on_resize)
        self._tk_window.set_mouse_drag_handler(self._on_mouse_drag)
        self._tk_window.set_key_press_handler(self._on_tk_key_event)
        self._tk_window.set_close_handler(self._on_close)

    @property
    def width(self) -> int:
        """Window width in pixels."""
        return self._tk_window.width

    @property
    def height(self) -> int:
        """Window height in pixels."""
        return self._tk_window.height

    @property
    def viewer(self) -> GCubeViewer:
        """Access the cube viewer."""
        # _viewer is always initialized in __init__, so this is never None
        return self._viewer  # type: ignore[return-value]

    def run(self) -> None:
        """Run the main event loop."""
        try:
            self._event_loop.run()
        except Exception as e:
            print(f"Event loop error: {e}")

    def close(self) -> None:
        """Close the window and stop the event loop."""
        self._event_loop.stop()
        self._tk_window.close()

    def _request_redraw(self) -> None:
        """Request window redraw."""
        self._tk_window.request_redraw()

    def set_mouse_visible(self, visible: bool) -> None:
        """Show or hide the mouse cursor."""
        # Tkinter handles cursor visibility automatically
        pass

    # === Event Handlers ===

    def _draw(self) -> None:
        """Draw callback for TkinterWindow."""
        if self._tk_window.closed:
            return

        # Clear canvas
        self._renderer.clear((200, 200, 200, 255))

        # Reset view matrix
        self._renderer.view.load_identity()

        # Draw the cube
        if self._viewer is not None:
            self._viewer.draw()

        # Draw status text
        self._draw_status_text()

        # End frame
        self._renderer.end_frame()

    def _draw_status_text(self) -> None:
        """Draw status text on the window."""
        # Build status text if not animation running
        if not self.animation_running:
            self._update_status_text()

        # Draw labels using window's text renderer
        y = 20
        for label in self._status_labels:
            self._tk_window.text.draw_label(
                label.text,
                label.x,
                y,
                font_size=label.font_size,
                color=label.color,
                anchor_x="left",
                anchor_y="top"
            )
            y += 18

    def _on_resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self._renderer.view.set_projection(width, height)
        self._draw()

    def _on_mouse_drag(self, event) -> None:
        """Handle mouse drag for rotation."""
        # Update view state rotation
        sensitivity = 0.01
        self._app.vs.alpha_y += event.dx * sensitivity
        self._app.vs.alpha_x -= event.dy * sensitivity
        self._draw()

    def _on_tk_key_event(self, event) -> None:
        """Native key event handler from TkinterWindow.

        Receives KeyEvent with already-converted abstract keys.
        Calls handle_key() - the protocol method.
        """
        self.handle_key(event.symbol, event.modifiers)

    def handle_key(self, symbol: int, modifiers: int) -> None:
        """Protocol method - handle abstract key press.

        Overrides AppWindowBase.handle_key() to add redraw after key press.

        Args:
            symbol: Key code (from Keys enum) - already converted to abstract
            modifiers: Modifier flags (from Modifiers)
        """
        super().handle_key(symbol, modifiers)
        self._draw()

    def _on_close(self) -> bool:
        """Handle window close."""
        return True  # Allow close

    # === Key Injection ===

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a single key press (already abstract keys)."""
        self.handle_key(key, modifiers)

    # === Text Building (from AppWindowBase) ===

    def _update_status_text(self) -> None:
        """Build status text labels using AppWindowBase method."""
        # Call parent's method to build _status_labels
        super()._update_status_text()

    def _update_animation_text(self) -> None:
        """Build animation text labels using AppWindowBase method."""
        super()._update_animation_text()

    def get_opengl_info(self) -> str:
        """Get OpenGL version information (not applicable for tkinter).

        Returns:
            Empty string (tkinter backend uses 2D canvas, no OpenGL).
        """
        return ""

    # adjust_brightness() and get_brightness() inherited from AppWindowBase (return None)
