import math
import sys
import traceback
from typing import MutableSequence

import glooey
import pyglet
from pyglet.gl import *
from pyglet.window import key

import algs
import viewer_g
from algs import Alg, Algs
from cube import Cube
from cube_operator import Operator
from solver import Solver
from view_state import ViewState
from viewer_g import GCubeViewer


# pyglet.options["debug_graphics_batch"] = True


class Main:

    def __init__(self) -> None:
        super().__init__()
        self._error = None
        self.cube = Cube()
        self.op: Operator = Operator(self.cube)
        self.slv: Solver = Solver(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.vs = ViewState(0, 0, 0, 0)

        self.reset()

    def reset(self):
        self.cube.reset()
        # can't change instance, it is shared
        self.vs.reset(0.3, -0.4, 0, 0.1)
        self._error = None

    def set_error(self, error: str):
        self._error = error

    @property
    def error(self):
        return self._error


# noinspection PyAbstractClass
class Window(pyglet.window.Window):
    #     # Cube 3D start rotation
    xRotation = yRotation = 30

    def __init__(self, app: Main, width, height, title=''):
        super(Window, self).__init__(width, height, title, resizable=True)
        # from cube3d
        glClearColor(0, 0, 0, 1)

        # see Z-Buffer in
        #  https://learnopengl.com/Getting-started/Coordinate-Systems  #Z-buffer
        glEnable(GL_DEPTH_TEST)

        self.batch = pyglet.graphics.Batch()
        # self.create_layout()

        self.app: Main = app
        self.viewer: GCubeViewer = GCubeViewer(self.batch, app.cube, app.vs)
        self.text: MutableSequence[pyglet.text.Label] = []

        self.update_gui_elements()

    def update_gui_elements(self):

        # so they can be used by draw mehod

        self.viewer.update()
        self.text.clear()
        self.text.append(pyglet.text.Label("Status:" + self.app.slv.status,
                                           x=10, y=10, font_size=10))
        h = Algs.simplify(*self.app.op.history)
        self.text.append(pyglet.text.Label("History: #" + str(h.count()) + "  " + str(h),
                                           x=10, y=30, font_size=10))
        h = self.app.op.history
        self.text.append(pyglet.text.Label("History: #" + str(Algs.count(*h)) + "  " + str(h),
                                           x=10, y=50, font_size=10))

        err = "R L U S/Z/F B D  M/X/R E/Y/U (SHIFT-INv), ?-Solve, Clear, Q " + "0-9 scramble1, <undo, Test"
        self.text.append(pyglet.text.Label(err,
                                           x=10, y=70, font_size=10))

        solution = self.app.slv.solution().simplify()
        s = "Solution:(" + str(solution.count()) + ") "+ str(solution)
        self.text.append(pyglet.text.Label(s,
                                           x=10, y=90, font_size=10))

        if self.app.error:
            err = f"Error:{self.app.error}"
            self.text.append(pyglet.text.Label(err,
                                               x=10, y=110, font_size=10, color=(255, 0, 0, 255), bold=True))


    def on_draw(self):
        # need to understand which buffers it clear, see
        #  https://learnopengl.com/Getting-started/Coordinate-Systems  #Z-buffer
        self.clear()

        self.draw_axis()

        self.viewer.draw()
        # self.batch.draw()
        self.draw_text()

    def on_resize(self, width, height):
        # https://hub.packtpub.com/creating-amazing-3d-guis-pyglet/
        # set the Viewport
        glViewport(0, 0, width, height)

        glPushAttrib(GL_MATRIX_MODE)
        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect_ratio = width / height
        gluPerspective(35, aspect_ratio, 1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -400)

        glPopAttrib()

    def on_key_press(self, symbol, modifiers):
        try:
            done = _handle_input(self, symbol, modifiers)
            if done:
                self.close()

        except Exception as e:
            traceback.print_exc()

            m = str(e)
            s = "Some error occurred"
            if m:
                s += m

            self.app.set_error(s)
            self.update_gui_elements()  # to create error label

    # def on_text(self, text):
    #     # printing some message
    #     print("You are entering : " + text)
    #     return GL_NOT

    def draw_axis(self):
        glPushAttrib(GL_MATRIX_MODE)
        glMatrixMode(GL_MODELVIEW)

        glPushMatrix()

        glLoadIdentity()
        glTranslatef(0, 0, -400)

        # ideally we want the axis to be fixed, but in this case we won't see the Z,
        #  so we rotate the Axes, or we should change the perspective
        vs: ViewState = self.app.vs
        glRotatef(math.degrees(vs.alpha_x_0), 1, 0, 0)
        glRotatef(math.degrees(vs.alpha_y_0), 0, 1, 0)
        glRotatef(math.degrees(vs.alpha_z_0), 0, 0, 1)

        glPushAttrib(GL_LINE_WIDTH)
        glLineWidth(3)

        glBegin(GL_LINES)

        glColor3ub(255, 255, 255)
        glVertex3f(0, 0, 0)
        glVertex3f(200, 0, 0)
        glEnd()

        glBegin(GL_LINES)
        glColor3ub(255, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 200, 0)
        glEnd()

        glBegin(GL_LINES)
        glColor3ub(0, 255, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 200)

        glEnd()

        glPopAttrib()  # line width

        # Pop Matrix off stack
        glPopMatrix()
        glPopAttrib()  # GL_MATRIX_MODE

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

        glPushAttrib(GL_MATRIX_MODE)

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        w = window.width
        h = window.height
        glOrtho(0, w, 0, h, -1.0, 1.0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glPopAttrib()  # matrix mode

        for t in self.text:
            t.draw()

        # restore state

        glPushAttrib(GL_MATRIX_MODE)

        # using Projection mode
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glPopAttrib()  # matrix mode


def main():
    app: Main = Main()
    Window(app, 720, 720, '"Cube"')
    pyglet.app.run()


def _handle_input(window: Window, value: int, modifiers: int) -> bool:
    done = False

    app: Main = window.app
    op: Operator = app.op
    slv: Solver = app.slv
    vs: ViewState = app.vs

    inv = modifiers & key.MOD_SHIFT

    no_operation = False

    # noinspection PyProtectedMember
    match value:

        case key.EQUAL:
            print("Flipping...")
            window.flip()

        case key.I:
            print(f"{vs.alpha_x=} {vs.alpha_y=} {vs.alpha_z=}")
            no_operation = True

        case key.R:
            op.op(algs.Algs.R, inv)
        case key.L:
            op.op(algs.Algs.L, inv)

        case key.U:
            op.op(algs.Algs.U, inv)

        case key.E:
            op.op(algs.Algs.E, inv)

        case key.F:
            op.op(algs.Algs.F, inv)

        case key.S:
            op.op(algs.Algs.S, inv)

        case key.B:
            op.op(algs.Algs.B, inv)

        case key.D:
            op.op(algs.Algs.D, inv)

        case key.X:
            if modifiers & key.MOD_CTRL:
                vs.alpha_x -= vs.alpha_delta
                no_operation = True

            elif modifiers & key.MOD_ALT:
                vs.alpha_x += vs.alpha_delta
                no_operation = True

            else:
                op.op(algs.Algs.X, inv)

        case key.M:
            op.op(algs.Algs.M, inv)

        case key.Y:
            if modifiers & key.MOD_CTRL:
                vs.alpha_y -= vs.alpha_delta
                no_operation = True
            elif modifiers & key.MOD_ALT:
                vs.alpha_y += vs.alpha_delta
                no_operation = True
            else:
                op.op(algs.Algs.Y, inv)

        case key.E:
            op.op(algs.Algs.E, inv)

        case key.Z:
            if modifiers & key.MOD_CTRL:
                vs.alpha_z -= vs.alpha_delta
                no_operation = True
            elif modifiers & key.MOD_ALT:
                vs.alpha_z += vs.alpha_delta
                no_operation = True
            else:
                op.op(algs.Algs.Z, inv)

        case "A":

            alg: Alg = get_alg()
            op.op(alg, inv)

        case key.C:
            op.reset()
            app.reset()

        case key._0:
            alg: Alg = Algs.scramble()
            op.op(alg, inv)

        case key._1 | key._2 | key._3 | key._4 | key._5 | key._6:
            # to match test int
            # noinspection PyProtectedMember
            alg: Alg = Algs.scramble(value - key._0)
            op.op(alg, inv)

        case key.COMMA:
            op.undo()

        case key.SLASH:
            slv.solve()

        case key.T:
            # test
            for s in range(0, 50):
                op.reset()
                alg: Alg = Algs.scramble(s)
                op.op(alg)

                # noinspection PyBroadException
                try:
                    slv.solve()
                    assert slv.is_solved

                except Exception as e:
                    print(f"Failure on {s}")
                    traceback.print_exc()
                    raise

        case key.Q:
            return True

        case _:
            return False

    # no need to redraw, on_draw is called after any event

    if not no_operation:
        window.update_gui_elements()

    return done


def get_alg() -> Alg:
    print("Algs:")
    _algs = algs.Algs.lib()

    for i, a in enumerate(_algs):
        print("", i + 1, "):", str(a))

    index = input("Alg index:")

    return _algs[int(index) - 1]

    pass


if __name__ == '__main__':
    main()
