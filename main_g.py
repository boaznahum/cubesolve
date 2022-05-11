import math
import traceback

import glooey
import pyglet
from pyglet.gl import *
from pyglet.window import key

import algs
from algs import Alg, Algs
from cube import Cube
from cube_operator import Operator
from solver import Solver
from viewer_g import GCubeViewer


# pyglet.options["debug_graphics_batch"] = True


class Main:

    def __init__(self) -> None:
        super().__init__()
        self.cube = Cube()
        self.op: Operator = Operator(self.cube)
        self.slv: Solver = Solver(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        # for axes
        self.alpha_x_0: float = 0.3
        self.alpha_y_0: float = -0.4
        self.alpha_z_0: float = 0

        self.alpha_x: float = 0
        self.alpha_y: float = 0
        self.alpha_z: float = 0
        self.alpha_delta = 0.1

        self.reset()

    def reset(self):
        self.cube.reset()
        self.alpha_x: float = self.alpha_x_0
        self.alpha_y: float = self.alpha_y_0
        self.alpha_z: float = self.alpha_z_0


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
        #self.create_layout()

        self.app: Main = app
        self.viewer: GCubeViewer = GCubeViewer(self.batch, app.cube)

    def on_draw(self):
        # need to understand which buffers it clear, see
        #  https://learnopengl.com/Getting-started/Coordinate-Systems  #Z-buffer
        self.clear()

        self.draw_axis()

        self.viewer.update(self.app.alpha_x, self.app.alpha_y, self.app.alpha_z)
        #self.batch.draw()
        self.plot_text()

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
        done = _handle_input(self, symbol, modifiers)
        if done:
            self.close()

    # def on_text(self, text):
    #     # printing some message
    #     print("You are entering : " + text)
    #     return GL_NOT

    def draw_axis(self):
        # p = (GLint)()
        # glGetIntegerv(GL_MATRIX_MODE, p)
        # print(p, GL_MODELVIEW, GL_MODELVIEW==p.value)
        # default is GL_MODELVIEW, but we need to make sue by push attributes

        glPushAttrib(GL_MATRIX_MODE)
        glMatrixMode(GL_MODELVIEW)

        glPushMatrix()

        # ideally we want the axis to be fixed, but in this case we won't see the Z
        #  so we rotate the Axes, or we should change the perspective
        glRotatef(math.degrees(self.app.alpha_x_0), 1, 0, 0)
        glRotatef(math.degrees(self.app.alpha_y_0), 0, 1, 0)
        glRotatef(math.degrees(self.app.alpha_z_0), 0, 0, 1)

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

        hbox1 = glooey.HBox()
        #        hbox1.hide()
        grid.add(0, 1, hbox1)
        hbox2 = glooey.HBox()
        grid.add(1, 0, hbox2)

        hbox3 = glooey.HBox()
        grid.add(1, 0, hbox2)

        grid.add(1, 1, hbox3)

        gui.add(grid)
        #
        # s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)

    #        s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)

    # document = pyglet.text.decode_text('Hello, world.')
    # layout = pyglet.text.layout.TextLayout(document, 100, 20, batch=batch)

    def plot_text(self):
        window = self

        glPushAttrib(GL_MATRIX_MODE)

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        w = window.width
        h = window.height
        glOrtho(0, w, 0, h / 2, -1.0, 1.0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glPopAttrib()  # matrix mode

        status = pyglet.text.Label("Status:" + self.app.slv.status,
                                   x=10, y=10, font_size=10)
        status.draw()

        h = Algs.simplify(*self.app.op.history)
        status = pyglet.text.Label("History: #" + str(h.count()) + "  "+ str(h),
                                   x=10, y=30, font_size=10)
        status.draw()

        h = self.app.op.history
        status = pyglet.text.Label("History: #" + str(Algs.count(*h)) + "  "+ str(h),
                                   x=10, y=50, font_size=10)
        status.draw()



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
    viewer: GCubeViewer = window.viewer
    slv: Solver = app.slv

    inv = modifiers & key.MOD_SHIFT

    # noinspection PyProtectedMember
    match value:

        case key.EQUAL:
            print("Flipping...")
            window.flip()

        case key.I:
            print(f"{app.alpha_x=} {app.alpha_y=} {app.alpha_z=}")

        case key.R:
            op.op(algs.Algs.R, inv)
        case key.L:
            op.op(algs.Algs.L, inv)

        case key.U:
            op.op(algs.Algs.U, inv)

        case key.F:
            op.op(algs.Algs.F, inv)

        case key.B:
            op.op(algs.Algs.B, inv)

        case key.D:
            op.op(algs.Algs.D, inv)

        case key.X:
            if modifiers & key.MOD_CTRL:
                app.alpha_x -= app.alpha_delta
            elif modifiers & key.MOD_ALT:
                app.alpha_x += app.alpha_delta
            else:
                op.op(algs.Algs.X, inv)

        case key.Y:
            if modifiers & key.MOD_CTRL:
                app.alpha_y -= app.alpha_delta
            elif modifiers & key.MOD_ALT:
                app.alpha_y += app.alpha_delta
            else:
                op.op(algs.Algs.Y, inv)

        case key.Z:
            if modifiers & key.MOD_CTRL:
                app.alpha_z -= app.alpha_delta
            elif modifiers & key.MOD_ALT:
                app.alpha_z += app.alpha_delta

        case key.M:
            op.op(algs.Algs.M, inv)

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

                except Exception:
                    print(f"Failure on {s}")
                    traceback.print_exc()
                    break

        case key.Q:
            return True

        # case _:
        #     return False

    # no need to redraw, on_draw is called after any event

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
