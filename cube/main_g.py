import traceback
from typing import MutableSequence, Sequence

import glooey  # type: ignore
# import pygame
import pyglet  # type: ignore
from pyglet import gl
from pyglet.window import key  # type: ignore

from cube.animation.animation_manager import AnimationWindow
from cube.app.abstract_ap import AbstractApp

from . import config
from . import main_g_keyboard_input
from . import main_g_mouse
from .algs import Algs, Alg
from .animation.animation_manager import AnimationManager
from .app_exceptions import AppExit, RunStop, OpAborted
from cube.app.app_state import ApplicationAndViewState
from .main_g_abstract import AbstractWindow
from .viewer.viewer_g import GCubeViewer
# pyglet.options["debug_graphics_batch"] = True
from .viewer.viewer_g_ext import GViewerExt


# noinspection PyAbstractClass
class Window(AbstractWindow, AnimationWindow):
    #     # Cube 3D start rotation
    xRotation = yRotation = 30

    def __init__(self, app: AbstractApp,
                 width, height, title=''):
        super(Window, self).__init__(width, height, title, resizable=True)

        self._animation_manager = app.am

        self._vs = app.vs

        # still don't know how to get rid of this patch !!!
        if self._animation_manager:
            self._animation_manager.set_window(self)

        # from cube3d
        gl.glClearColor(0, 0, 0, 1)

        # see Z-Buffer in
        #  https://learnopengl.com/Getting-started/Coordinate-Systems  #Z-buffer
        gl.glEnable(gl.GL_DEPTH_TEST)

        self.batch = pyglet.graphics.Batch()
        # self.create_layout()

        self._app: AbstractApp = app
        self._viewer: GCubeViewer = GCubeViewer(self.batch, app.cube, app.vs)
        self.text: MutableSequence[pyglet.text.Label] = []
        self.animation_text: MutableSequence[pyglet.text.Label] = []

        # self._animation: Animation | None = None

        self._last_edge_solve_count = 0

        # todo: still don't know what to do without this patch
        # self.app.op._animation_hook = lambda op, alg: main_g_animation.op_and_play_animation(self, op, False, alg)

        self.update_gui_elements()

    @property
    def app(self) -> AbstractApp:
        return self._app

    @property
    def viewer(self) -> GCubeViewer:
        return self._viewer

    # def set_animation(self, an: Animation | None):
    #     self._animation = an

    @property
    def animation_running(self):
        """
        Return non None if animation is running
        :return: True value indicated that animation manager started animation
        """
        return self._animation_manager and self._animation_manager.animation_running()

    def update_gui_elements(self):

        # so they can be used by draw method

        self.viewer.update()

        if self._animation_manager:
            self._animation_manager.update_gui_elements()

        self.update_animation_text()

        if self.animation_running:
            return  # don't update text while animation

        self.update_text()

    def update_text(self):

        cube = self.app.cube

        vs: ApplicationAndViewState = self.app.vs
        op = self.app.op

        def _b(b: bool):
            return "On" if b else "Off"

        y = 10

        self.text.clear()
        self.text.append(pyglet.text.Label("Status:" + self.app.slv.status,
                                           x=10, y=y, font_size=10))
        y += 20

        # self.text.append(pyglet.text.Label("Edges: #" + str(self._last_edge_solve_count),
        #                                    x=10, y=y, font_size=10))
        # y += 20

        h = Algs.simplify(*op.history(remove_scramble=True))
        sh = str(h)[-120:]
        self.text.append(pyglet.text.Label("History(simplified): #" + str(h.count()) + "  " + sh,
                                           x=10, y=y, font_size=10))
        y += 20

        h = op.history()
        sh = str(h)[-70:]
        self.text.append(pyglet.text.Label("History: #" + str(Algs.count(*h)) + "  " + sh,
                                           x=10, y=y, font_size=10))
        y += 20

        is_recording = op.is_recording
        s = "Recording: " + _b(is_recording)
        recording: Sequence[Alg] | None = vs.last_recording
        if recording is not None:
            sh = str(recording)[-70:]
            s = s + ", #" + str(Algs.count(*recording)) + "  " + sh
        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=10))
        y += 20

        err = "R L U S/Z/F B D  M/X/R E/Y/U (SHIFT-INv), ?-Solve, Clear, Q " + "0-9 scramble1, <undo, Test"
        self.text.append(pyglet.text.Label(err,
                                           x=10, y=y, font_size=10))
        y += 20

        # solution = self.app.slv.solution().simplify()
        # s = "Solution:(" + str(solution.count()) + ") " + str(solution)
        # self.text.append(pyglet.text.Label(s,
        #                                    x=10, y=90, font_size=10))

        s = f"Sanity:{cube.is_sanity(force_check=True)}"

        if self.app.error:
            s += f", Error:{self.app.error}"

        self.text.append(pyglet.text.Label(s,
                                           x=10, y=y, font_size=10, color=(255, 0, 0, 255), bold=True))
        y += 20

        # ---------------------------------------

        s = f"Animation:{_b(op.animation_enabled)}"
        s += ", [" + str(vs.get_speed_index) + "] " + vs.get_speed.get_speed()
        s += ", Sanity check:" + _b(config.CHECK_CUBE_SANITY)
        s += ", Debug=" + _b(self.app.slv.is_debug_config_mode)
        s += ", SS Mode:" + _b(vs.single_step_mode)

        self.text.append(pyglet.text.Label(s,
                                           x=10, y=y, font_size=10, color=(255, 255, 0, 255), bold=True))
        y += 20

        # ----------------------------

        s = f"S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"

        s += ", Slices"
        s += "  [" + str(vs.slice_start) + ", " + str(vs.slice_stop) + "]"

        s += ", " + str(vs.slice_alg(cube, Algs.R))
        s += ", " + str(vs.slice_alg(cube, Algs.M))

        self.text.append(pyglet.text.Label(s,
                                           x=10, y=y, font_size=10, color=(0, 255, 0, 255), bold=True))
        y += 20

        s = ""
        # print(f"@@@@@ {vs.paused_on_single_step_mode=}")

        if vs.paused_on_single_step_mode:
            s = f"PAUSED: {vs.paused_on_single_step_mode}. press space"

        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=15, color=(0, 255, 0, 255), bold=True))
        y += 20

    def update_animation_text(self):

        vs: ApplicationAndViewState = self.app.vs

        self.animation_text.clear()
        # Animation text
        at = vs.animation_text
        for i in range(3):
            #  # x, y from top, size, color, bold
            prop: tuple[int, int, int, tuple[int, int, int, int], bool] = config.ANIMATION_TEXT[i]
            h = at.get_line(i)
            if h:
                x = prop[0]
                y = self.height - prop[1]
                size = prop[2]
                color: tuple[int, int, int, int] = prop[3]
                bold: bool = prop[4]
                self.animation_text.append(pyglet.text.Label(h,
                                                             x=x, y=y, font_size=size, color=color, bold=bold))

    def on_draw(self):

        if self._vs.skip_next_on_draw:
            self._vs.skip_next_on_draw = False
            if config.VIEWER_TRACE_DRAW_UPDATE:
                print("Skipping draw due to ", self._vs.skip_next_on_draw)
            return

        # print("Updating")
        # need to understand which buffers it clear, see
        #  https://learnopengl.com/Getting-started/Coordinate-Systems  #Z-buffer
        self.clear()

        self.draw_axis()

        self.viewer.draw()
        # self.batch.draw()
        self.draw_text()

        self.draw_animation()

    def on_resize(self, width, height):
        # https://hub.packtpub.com/creating-amazing-3d-guis-pyglet/
        # set the Viewport

        # https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glViewport.xhtml
        # xw(x)=(xnd+1)(width/2)+x
        # yw(y)=(ynd+1)(height/2)+y
        gl.glViewport(0, 0, width, height)

        self.app.vs.set_projection(width, height)

    def on_key_press(self, symbol, modifiers):
        try:
            return main_g_keyboard_input.handle_keyboard_input(self, symbol, modifiers)

        except (AppExit, RunStop, OpAborted):
            self.app.set_error("Asked to stop")
            self.update_gui_elements()  # to create error label

        except Exception as e:
            traceback.print_exc()

            m = str(e)
            s = "Some error occurred:"
            if m:
                s += m

            self.app.set_error(s)
            self.update_gui_elements()  # to create error label

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return main_g_mouse.on_mouse_drag(self, x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        return main_g_mouse.on_mouse_press(self, self.app.vs, x, y, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        return main_g_mouse.on_mouse_release()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return main_g_mouse.on_mouse_scroll(self, scroll_y)

    def draw_axis(self):
        GViewerExt.draw_axis(self.app.vs)

    def create_layout(self):
        window = self
        batch = self.batch
        gui = glooey.Gui(window, batch=batch)

        grid = glooey.Grid()

        ph = glooey.Placeholder()
        grid.add(0, 0, ph)

        ph = glooey.Placeholder()
        grid.add(0, 1, ph)

        h_box1 = glooey.HBox()
        #        h_box1.hide()
        grid.add(0, 1, h_box1)
        h_box2 = glooey.HBox()
        grid.add(1, 0, h_box2)

        h_box3 = glooey.HBox()
        grid.add(1, 0, h_box2)

        grid.add(1, 1, h_box3)

        gui.add(grid)
        #
        # s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)

    #        s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)

    # document = pyglet.text.decode_text('Hello, world.')
    # layout = pyglet.text.layout.TextLayout(document, 100, 20, batch=batch)

    def draw_text(self):
        window = self

        gl.glPushAttrib(gl.GL_MATRIX_MODE)

        # using Projection mode
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        w = window.width
        h = window.height
        gl.glOrtho(0, w, 0, h, -1.0, 1.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        gl.glPopAttrib()  # matrix mode

        for t in self.text:
            t.draw()

        for t in self.animation_text:
            t.draw()

        # restore state

        gl.glPushAttrib(gl.GL_MATRIX_MODE)

        # using Projection mode
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()

        gl.glPopAttrib()  # matrix mode

    def draw_animation(self):

        if self._animation_manager:
            self._animation_manager.draw()


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

    app = AbstractApp.create()
    win = Window(app, 720, 720, '"Cube"')

    win.set_mouse_visible(True)

    try:
        pyglet.app.run()
    finally:
        win.viewer.cleanup()


if __name__ == '__main__':
    main()
