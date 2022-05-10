import math
import traceback

import pyglet
from pyglet.gl import *
from pyglet.window import key

import algs
import viewer_g
from algs import Alg, Algs
from cube import Cube
from cube_operator import Operator
from solver import Solver
from viewer_g import GCubeViewer


# pyglet.options["debug_graphics_batch"] = True


# class Screen:
#
#     def __init__(self) -> None:
#         super().__init__()
#         self.batch = None
#         self.window = None
#         # self.status: glooey.Label | None = None
#         self.status: pyglet.text.Label | None = None
#
#         self.alpha_x: float = 0
#         self.alpha_y: float = 0
#         self.alpha_z: float = 0
#         self.alpha_delta = 0.1
#         self.cube = None


class Main:

    def __init__(self) -> None:
        super().__init__()
        self.cube = Cube()
        self.op: Operator = Operator(self.cube)
        self.slv: Solver = Solver(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.alpha_x: float = 0
        self.alpha_y: float = 0
        self.alpha_z: float = 0
        self.alpha_delta = 0.1
        self.reset()

    def reset(self):
        self.cube.reset()
        self.alpha_x: float = 0.3
        self.alpha_y: float = -0.4
        self.alpha_z: float = 0


# noinspection PyAbstractClass
class Window(pyglet.window.Window):
    #     # Cube 3D start rotation
    xRotation = yRotation = 30

    def __init__(self, app: Main, width, height, title=''):
        super(Window, self).__init__(width, height, title, resizable=True)
        # from cube3d
        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)

        self.app: Main = app
        self.batch = pyglet.graphics.Batch()
        self.viewer: GCubeViewer = GCubeViewer(self.batch, app.cube)

        self.status = pyglet.text.Label("Status:" + app.slv.status, x=-100, y=-100, font_size=15, batch=self.batch)

    def on_draw(self):
        self.clear()

        self.draw_axis()

        viewer_g.alpha_x = self.app.alpha_x
        viewer_g.alpha_y = self.app.alpha_y
        viewer_g.alpha_z = self.app.alpha_z
        self.viewer.update(self.app.alpha_x, self.app.alpha_y, self.app.alpha_z)
        self.batch.draw()

    def on_resize(self, width, height):
        # https://hub.packtpub.com/creating-amazing-3d-guis-pyglet/
        # set the Viewport
        glViewport(0, 0, width, height)

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect_ratio = width / height
        gluPerspective(35, aspect_ratio, 1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -400)

    def on_key_press(self, symbol, modifiers):
        done = _handle_input(self, symbol, modifiers)
        if done:
            self.close()

    def draw_axis(self):
        glPushMatrix()

        glRotatef(math.degrees(self.app.alpha_x), 1, 0, 0)
        glRotatef(math.degrees(self.app.alpha_y), 0, 1, 0)
        glRotatef(math.degrees(self.app.alpha_z), 0, 0, 1)

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

        glPopAttrib()

        # Pop Matrix off stack
        glPopMatrix()


# def _create_initial_gui() -> Screen:
#     window = pyglet.window.Window(400, 400, "Cube")
#     batch = pyglet.graphics.Batch()
#
#     s: Screen = Screen()
#     s.window = window
#     s.batch = batch
#
#     # gui = glooey.Gui(window, batch=batch)
#     #
#     # grid = glooey.Grid()
#     #
#     # ph = glooey.Placeholder()
#     # grid.add(0, 0, ph)
#     #
#     # ph = glooey.Placeholder()
#     # grid.add(0, 1, ph)
#     #
#     # hbox1 = glooey.HBox()
#     # hbox1.hide()
#     # grid.add(0, 1, hbox1)
#     # hbox2 = glooey.HBox()
#     # grid.add(1, 0, hbox2)
#     #
#     # hbox3 = glooey.HBox()
#     # grid.add(1, 0, hbox2)
#     #
#     # grid.add(1, 1, hbox3)
#     #
#     # gui.add(grid)
#     #
#     # s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)
#     s.status = pyglet.text.Label("Status", x=360, y=300, font_size=36, batch=batch)
#
#     # document = pyglet.text.decode_text('Hello, world.')
#     # layout = pyglet.text.layout.TextLayout(document, 100, 20, batch=batch)
#
#     @window.event
#     def on_draw():
#         window.clear()
#         cube3d.on_draw()
#         # batch.draw()
#
#     @window.event
#     def on_resize(width, height):
#         cube3d.on_resize(width, height)
#
#     return s


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

        case "M":
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

        case "<":
            op.undo()

        case key.SLASH:
            slv.solve()

        case "T":
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

    #    if not not_operation:
    # print("Updating ....")
    #viewer.update(app.alpha_x, app.alpha_y, app.alpha_z)
    # no need to redraw, on_draw is called after any event
    window.status.text = "Status:" + slv.status
    # window.flip()
    # text_viewer.plot(s.cube)

    return done

    # print("DONE=", done)


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
