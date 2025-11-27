"""
Pyglet-based GUI entry point for the Cube Solver.

This module explicitly uses the pyglet backend for rendering.
"""
import pyglet  # type: ignore

from cube.app.abstract_ap import AbstractApp
# Import pyglet backend to register it with BackendRegistry
import cube.gui.backends.pyglet  # noqa: F401 - registers backend
from cube.gui import BackendRegistry
from cube.main_window import Window


# pyglet.options["debug_graphics_batch"] = True


def main():
    """
    Main entry point for the pyglet-based GUI.

    Note: AnimationManager needs to know which window it works with to send GUI update operations.
    On the other hand, Window needs to know about the manager to request draw/update events
    and to know if animation is running.
    """
    # Create renderer explicitly using pyglet backend
    renderer = BackendRegistry.create_renderer(backend="pyglet")

    app = AbstractApp.create()
    win = Window(app, 720, 720, '"Cube"', renderer=renderer)

    win.set_mouse_visible(True)

    try:
        pyglet.app.run()
    finally:
        win.viewer.cleanup()


if __name__ == '__main__':
    main()
