"""
Pyglet-based GUI entry point for the Cube Solver.

This module explicitly uses the pyglet backend for rendering.
"""
from cube.app.abstract_ap import AbstractApp
# Import pyglet backend to register it with BackendRegistry
import cube.gui.backends.pyglet  # noqa: F401 - registers backend
from cube.gui import BackendRegistry
from cube.main_window import Window


def main():
    """
    Main entry point for the pyglet-based GUI.

    Note: AnimationManager needs to know which window it works with to send GUI update operations.
    On the other hand, Window needs to know about the manager to request draw/update events
    and to know if animation is running.
    """
    # Get the pyglet backend
    backend = BackendRegistry.get_backend("pyglet")

    app = AbstractApp.create()

    # Set the event loop on the animation manager if it exists
    if app.am is not None:
        app.am.set_event_loop(backend.event_loop)

    win = Window(app, 720, 720, '"Cube"', backend=backend)

    win.set_mouse_visible(True)

    try:
        backend.event_loop.run()
    finally:
        win.viewer.cleanup()


if __name__ == '__main__':
    main()
