import math
import traceback
from typing import MutableSequence

import glooey  # type: ignore
import pyglet  # type: ignore
from pyglet import gl
from pyglet.window import key  # type: ignore

import config
import main_g_animation
import main_g_keyboard_input
import main_g_mouse_click
from algs.algs import Algs
from app_exceptions import AppExit, RunStop, OpAborted
from app_state import AppState
from main_g_abstract import AbstractWindow
from main_g_animation import Animation
from main_g_app import App
from viewer.viewer_g import GCubeViewer
# pyglet.options["debug_graphics_batch"] = True
from viewer.viewer_g_ext import GViewerExt


# noinspection PyAbstractClass
class Window(AbstractWindow):
    #     # Cube 3D start rotation
    xRotation = yRotation = 30

    def __init__(self, app: App, width, height, title=''):
        super(Window, self).__init__(width, height, title, resizable=True)
        # from cube3d
        gl.glClearColor(0, 0, 0, 1)

        # see Z-Buffer in
        #  https://learnopengl.com/Getting-started/Coordinate-Systems  #Z-buffer
        gl.glEnable(gl.GL_DEPTH_TEST)

        # https://stackoverflow.com/questions/3512456/how-to-draw-smooth-line-in-opengl-with-antialiasing
        # gl.glEnable(gl.GL_BLEND)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        # gl.glEnable(gl.GL_LINE_SMOOTH)
        # gl.glEnable(gl.GL_POLYGON_SMOOTH)
        # gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        # gl.glHint(gl.GL_POLYGON_SMOOTH_HINT, gl.GL_NICEST)

        self.batch = pyglet.graphics.Batch()
        # self.create_layout()

        self._app: App = app
        self.viewer: GCubeViewer = GCubeViewer(self.batch, app.cube, app.vs)
        self.text: MutableSequence[pyglet.text.Label] = []

        self._animation: Animation | None = None

        self._last_edge_solve_count = 0

        # todo: still don't know what to do without this patch
        self.app.op._animation_hook = lambda op, alg: main_g_animation.op_and_play_animation(self, op, False, alg)

        self.update_gui_elements()

    @property
    def app(self) -> App:
        return self._app

    def set_animation(self, an: Animation | None):
        self._animation = an

    def update_gui_elements(self):

        # so they can be used by draw method

        self.viewer.update()

        if self._animation:
            self._animation.update_gui_elements()

        if self.animation_running:
            return  # don't update text while animation

        self.update_text()

    def update_text(self):

        cube = self.app.cube

        vs: AppState = self.app.vs

        y = 10

        self.text.clear()
        self.text.append(pyglet.text.Label("Status:" + self.app.slv.status,
                                           x=10, y=y, font_size=10))
        y += 20

        # self.text.append(pyglet.text.Label("Edges: #" + str(self._last_edge_solve_count),
        #                                    x=10, y=y, font_size=10))
        # y += 20

        h = Algs.simplify(*self.app.op.history)
        sh = str(h)[-120:]
        self.text.append(pyglet.text.Label("History(simplified): #" + str(h.count()) + "  " + sh,
                                           x=10, y=y, font_size=10))
        y += 20

        h = self.app.op.history
        sh = str(h)[-70:]
        self.text.append(pyglet.text.Label("History: #" + str(Algs.count(*h)) + "  " + sh,
                                           x=10, y=y, font_size=10))
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

        def _b(b: bool):
            return "On" if b else "Off"

        s = f"Animation:{_b(self.app.op.animation_enabled)}"
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
        if vs.paused_on_single_step_mode:
            s = f"PAUSED: {vs.paused_on_single_step_mode}. press space"

        self.text.append(pyglet.text.Label(s, x=10, y=y, font_size=15, color=(0, 255, 0, 255), bold=True))
        y += 20

    def on_draw(self):
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

        gl.glPushAttrib(gl.GL_MATRIX_MODE)
        # using Projection mode
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        aspect_ratio = width / height
        gl.gluPerspective(35, aspect_ratio, 1, 1000)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -400)

        gl.glPopAttrib()

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
        # print(f"{dx=}, {dy=}")
        # https://stackoverflow.com/questions/59823131/how-to-rotate-a-cube-using-mouse-in-pyopengl
        # if event.type == pygame.MOUSEMOTION:
        #                 if button_down == True:
        #                     glRotatef(event.rel[1], 1, 0, 0)
        #                     glRotatef(event.rel[0], 0, 1, 0)
        #                 print(event.rel)
        if not modifiers & key.MOD_SHIFT:
            # still don't know to distinguish between ad drag and simple press
            self.app.vs.alpha_x += math.radians(-dy)
            self.app.vs.alpha_y += math.radians(dx)

    def on_mouse_press(self, x, y, button, modifiers):
        if modifiers & (key.MOD_SHIFT | key.MOD_CTRL):
            return main_g_mouse_click.on_mouse_press(self, self.app.vs, self.app.op, self.viewer, x, y, modifiers)

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

        # restore state

        gl.glPushAttrib(gl.GL_MATRIX_MODE)

        # using Projection mode
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()

        gl.glPopAttrib()  # matrix mode

    def draw_animation(self):
        animation = self._animation

        if animation:
            # print("Play animation")
            animation.draw()

    @property
    def animation_running(self):
        """
        Return non None if animation is running
        :return:
        """
        return self._animation


# noinspection PyPep8Naming


def main():
    app: App = App()
    win = Window(app, 720, 720, '"Cube"')

    win.set_mouse_visible(True)
    pyglet.app.run()


if __name__ == '__main__':
    main()
