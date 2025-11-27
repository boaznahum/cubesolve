# import pygame
import pyglet  # type: ignore
from pyglet.window import key  # type: ignore

from cube.app.abstract_ap import AbstractApp
from cube.gui import BackendRegistry
from cube.main_window import Window


# pyglet.options["debug_graphics_batch"] = True


# noinspection PyAbstractClass


# noinspection PyPep8Naming


def main():
    """"
    todo: We have a problem here see win-animation.puml

    AnimationManager need to know on which window it works - to send him gui update operations
    On the other hand, Window need to know about the manager,
    to request it draw/update events and to know if animation is running
    """

    # g_texture_list = gl.glGenLists(1)
    # #
    # gl.glNewList(g_texture_list, gl.GL_COMPILE)
    #
    # loadTexture2("cubie.bmp")
    #
    # gl.glEndList()
    # #
    # config.g_texture_list = g_texture_list

    # config.cubic_texture_data = TextureData.load()

    # Create renderer from the GUI abstraction layer
    renderer = BackendRegistry.create_renderer()

    app = AbstractApp.create()
    win = Window(app, 720, 720, '"Cube"', renderer=renderer)

    win.set_mouse_visible(True)

    try:
        pyglet.app.run()
    finally:
        win.viewer.cleanup()


if __name__ == '__main__':
    main()
