"""
Tkinter-based GUI entry point for the Cube Solver.

This module uses the tkinter backend for 2D isometric rendering.
This is a simplified version that demonstrates basic cube rendering
without animation support.
"""
import tkinter as tk

from cube.model.cube import Cube
from cube.viewer.viewer_g import GCubeViewer
from cube.app.app_state import ApplicationAndViewState

# Import tkinter backend to register it
import cube.gui.backends.tkinter  # noqa: F401
from cube.gui import BackendRegistry
from cube.gui.backends.tkinter.window import TkinterWindow
from cube.gui.backends.tkinter.renderer import TkinterRenderer
from cube.gui.backends.tkinter.event_loop import TkinterEventLoop


class TkinterCubeApp:
    """Simple Tkinter application for displaying a Rubik's cube."""

    def __init__(self, cube_size: int = 3):
        # Create cube and view state
        self.cube = Cube(cube_size)
        self.vs = ApplicationAndViewState()

        # Get the tkinter backend
        self.backend = BackendRegistry.get_backend("tkinter")

        # Create window (this creates the Tk root)
        self.window = TkinterWindow(720, 720, "Cube - Tkinter Backend")

        # Get renderer and set the canvas
        self.renderer: TkinterRenderer = self.backend.renderer  # type: ignore
        self.renderer.set_canvas(self.window.canvas)

        # Set up the event loop with the root window
        self.event_loop: TkinterEventLoop = self.backend.event_loop  # type: ignore
        self.event_loop.set_root(self.window.root)

        # Initialize renderer
        self.renderer.setup()

        # Set projection for canvas size
        self.renderer.view.set_projection(720, 720)

        # Create viewer
        self.viewer = GCubeViewer(self.cube, self.vs, renderer=self.renderer)

        # Set up event handlers
        self._setup_handlers()

        # Initial draw
        self._draw()

    def _setup_handlers(self) -> None:
        """Set up window event handlers."""
        self.window.set_draw_handler(self._draw)
        self.window.set_resize_handler(self._on_resize)
        self.window.set_mouse_drag_handler(self._on_mouse_drag)
        self.window.set_key_press_handler(self._on_key_press)
        self.window.set_close_handler(self._on_close)

    def _draw(self) -> None:
        """Draw the cube."""
        if self.window.closed:
            return

        # Clear canvas
        self.renderer.clear((200, 200, 200, 255))

        # Reset view matrix - viewer.draw() will set up its own transformation
        # via ApplicationAndViewState.prepare_objects_view()
        self.renderer.view.load_identity()

        # Draw the cube (this calls _prepare_view_state internally)
        self.viewer.draw()

        # Draw status text
        self.window.text.draw_label(
            f"Tkinter Backend - Cube {self.cube.size}x{self.cube.size}",
            10, 20,
            font_size=14,
            color=(0, 0, 0, 255),
            anchor_x="left",
            anchor_y="top"
        )
        self.window.text.draw_label(
            "Drag to rotate | R/L/U/D/F/B to turn faces | Q to quit",
            10, 40,
            font_size=12,
            color=(50, 50, 50, 255),
            anchor_x="left",
            anchor_y="top"
        )

        # End frame
        self.renderer.end_frame()

    def _on_resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.renderer.view.set_projection(width, height)
        self._draw()

    def _on_mouse_drag(self, event) -> None:
        """Handle mouse drag for rotation."""
        # Update view state rotation (this is what prepare_objects_view uses)
        import math
        # Convert pixel drag to radians (sensitivity factor)
        sensitivity = 0.01
        self.vs.alpha_y += event.dx * sensitivity
        self.vs.alpha_x -= event.dy * sensitivity

        self._draw()

    def _on_key_press(self, event) -> None:
        """Handle key press for cube operations."""
        from cube.gui.types import Keys
        from cube.algs import Algs

        key = event.symbol

        # Quit
        if key == Keys.Q or key == Keys.ESCAPE:
            self.window.close()
            return

        # Face rotations
        alg = None
        if key == Keys.R:
            alg = Algs.R
        elif key == Keys.L:
            alg = Algs.L
        elif key == Keys.U:
            alg = Algs.U
        elif key == Keys.D:
            alg = Algs.D
        elif key == Keys.F:
            alg = Algs.F
        elif key == Keys.B:
            alg = Algs.B

        # Apply rotation
        if alg:
            alg.play(self.cube)
            self.viewer.update()
            self._draw()

    def _on_close(self) -> bool:
        """Handle window close."""
        return True  # Allow close

    def run(self) -> None:
        """Run the application."""
        try:
            self.event_loop.run()
        except Exception as e:
            print(f"Event loop error: {e}")
        finally:
            self.viewer.cleanup()


def main():
    """Main entry point."""
    print("Starting Tkinter Cube Viewer...")
    print("Controls:")
    print("  - Drag mouse to rotate view")
    print("  - R/L/U/D/F/B keys to rotate faces")
    print("  - Q or Escape to quit")
    print()

    app = TkinterCubeApp(cube_size=3)
    app.run()


if __name__ == "__main__":
    main()
