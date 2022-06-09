import math
import traceback
from typing import MutableSequence

import glooey  # type: ignore
import pyglet  # type: ignore
from pyglet import gl
from pyglet.window import key  # type: ignore

import algs.algs as algs
import config
import main_g_animation
import main_g_mouse_click
from algs.algs import Alg, Algs
from app_exceptions import AppExit, RunStop, OpAborted
from app_state import ViewState
from cube_operator import Operator
from main_g_animation import Animation
from model.cube import Cube
from model.elements import FaceName
from solver import Solver, SolveStep
from viewer.viewer_g import GCubeViewer
# pyglet.options["debug_graphics_batch"] = True
from viewer.viewer_g_ext import GViewerExt


class Main:

    def __init__(self) -> None:
        super().__init__()
        self._error: str | None = None

        self.vs = ViewState()

        self.cube = Cube(self.vs.cube_size)

        self.op: Operator = Operator(self.cube, config.animation_enabled)

        self.slv: Solver = Solver(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.reset()

    def reset(self, dont_reset_axis=False):
        self.cube.reset(self.vs.cube_size)
        # can't change instance, it is shared
        if not dont_reset_axis:
            self.vs.reset()
        self._error = None

    def set_error(self, _error: str):
        self._error = _error

    @property
    def error(self):
        return self._error


# noinspection PyAbstractClass
class Window(main_g_animation.AbstractWindow):
    #     # Cube 3D start rotation
    xRotation = yRotation = 30

    def __init__(self, app: Main, width, height, title=''):
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

        self.app: Main = app
        self.viewer: GCubeViewer = GCubeViewer(self.batch, app.cube, app.vs)
        self.text: MutableSequence[pyglet.text.Label] = []

        self._animation: Animation | None = None

        self._last_edge_solve_count = 0

        self.update_gui_elements()

        self.app.op._animation_hook = lambda op, alg: op_and_play_animation(self, op, False, alg)

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

        app_vs: ViewState = self.app.vs

        self.text.clear()
        self.text.append(pyglet.text.Label("Status:" + self.app.slv.status,
                                           x=10, y=10, font_size=10))
        # h = Algs.simplify(*self.app.op.history)
        # sh = str(h)[-70:]
        self.text.append(pyglet.text.Label("Edges: #" + str(self._last_edge_solve_count),
                                           x=10, y=30, font_size=10))
        # h = Algs.simplify(*self.app.op.history)
        # sh = str(h)[-70:]
        # self.text.append(pyglet.text.Label("History: #" + str(h.count()) + "  " + sh,
        #                                    x=10, y=30, font_size=10))
        h = self.app.op.history
        sh = str(h)[-70:]
        self.text.append(pyglet.text.Label("History: #" + str(Algs.count(*h)) + "  " + sh,
                                           x=10, y=50, font_size=10))
        err = "R L U S/Z/F B D  M/X/R E/Y/U (SHIFT-INv), ?-Solve, Clear, Q " + "0-9 scramble1, <undo, Test"
        self.text.append(pyglet.text.Label(err,
                                           x=10, y=70, font_size=10))
        # solution = self.app.slv.solution().simplify()
        # s = "Solution:(" + str(solution.count()) + ") " + str(solution)
        # self.text.append(pyglet.text.Label(s,
        #                                    x=10, y=90, font_size=10))

        s = f"Sanity:{cube.is_sanity(force_check=True)}"

        if self.app.error:
            s += f", Error:{self.app.error}"

        self.text.append(pyglet.text.Label(s,
                                           x=10, y=110, font_size=10, color=(255, 0, 0, 255), bold=True))

        # ---------------------------------------

        def _b(b: bool): return "On" if b else "Off"

        s = f"Animation:{_b(self.app.op.animation_enabled)}"
        s += ", [" + str(app_vs.get_speed_index) + "] " + app_vs.get_speed.get_speed()
        s += ", Sanity check:" + _b(config.CHECK_CUBE_SANITY)
        s += ", Debug=" + _b(self.app.slv.is_debug_config_mode)
        self.text.append(pyglet.text.Label(s,
                                           x=10, y=130, font_size=10, color=(255, 255, 0, 255), bold=True))
        # ----------------------------

        s = f"S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"

        s += ", Slices"
        vs = app_vs
        s += "  [" + str(vs.slice_start) + ", " + str(vs.slice_stop) + "]"

        s += ", " + str(vs.slice_alg(cube, Algs.R))
        s += ", " + str(vs.slice_alg(cube, Algs.M))

        self.text.append(pyglet.text.Label(s,
                                           x=10, y=150, font_size=10, color=(0, 255, 0, 255), bold=True))

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
            _handle_input(self, symbol, modifiers)

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


def op_and_play_animation(window: Window, operator: Operator, inv: bool, alg: algs.SimpleAlg):
    main_g_animation.op_and_play_animation(window,
                                           window.app.cube,
                                           window.viewer,
                                           window.app.vs,
                                           operator,
                                           inv, alg)


_last_face: FaceName = FaceName.R

good = Algs.bigAlg("good")


def _handle_input(window: Window, value: int, modifiers: int):
    # print(f"{hex(value)}=")
    done = False
    app: Main = window.app
    op: Operator = app.op

    print(f"In _handle_input , {value}  {hex(value)} {chr(ord('A') + (value - key.A))} ")

    vs: ViewState = app.vs

    def handle_in_both_modes():
        match value:
            case key.NUM_ADD:
                vs.inc_speed()
                return True

            case key.NUM_SUBTRACT:
                vs.dec_speed()
                return True

    if window.animation_running or op.is_animation_running:

        if handle_in_both_modes():
            return

        #
        # print(f"{value==key.S}")
        match value:

            case key.Q:
                op.abort()  # solver will not try to check state
                window.close()
                raise AppExit

            case key.S:
                op.abort()  # doesn't work, we can't catch it, maybe pyglet ignore it, because it is in handler

        return False

    slv: Solver = app.slv

    inv = modifiers & key.MOD_SHIFT

    no_operation = False

    global _last_face

    alg: Alg

    def _slice_alg(r: algs.SliceAbleAlg):
        return vs.slice_alg(app.cube, r)

    global good
    # noinspection PyProtectedMember

    if not handle_in_both_modes():

        match value:

            case key.I:
                print(f"{vs.alpha_x + vs.alpha_x_0=} {vs.alpha_y+vs.alpha_y_0=} {vs.alpha_z+vs.alpha_z_0=}")
                no_operation = True
                from model.cube_queries import CubeQueries
                CubeQueries.print_dist(app.cube)

            case key.W:
                app.cube.front.corner_top_right.annotate(False)
                app.cube.front.corner_top_left.annotate(True)
                op.op(Algs.AN)

            case key.P:
                op.op(Algs.RD)

            case key.O:
                if modifiers & key.MOD_CTRL:
                    config.SOLVER_DEBUG = not config.SOLVER_DEBUG
                elif modifiers & key.MOD_ALT:
                    config.CHECK_CUBE_SANITY = not config.CHECK_CUBE_SANITY
                else:
                    op.toggle_animation_on()

            case key.EQUAL:
                app.vs.cube_size += 1
                app.cube.reset(app.vs.cube_size)
                op.reset()
                window.viewer.reset()

            case key.MINUS:
                if vs.cube_size > 3:
                    app.vs.cube_size -= 1
                app.cube.reset(app.vs.cube_size)
                op.reset()
                window.viewer.reset()

            case key.BRACKETLEFT:
                if modifiers and key.MOD_ALT:
                    vs.slice_start = vs.slice_stop = 0

                elif modifiers and key.MOD_SHIFT:
                    if vs.slice_start:
                        vs.slice_start -= 1
                    else:
                        vs.slice_start = 0
                    if vs.slice_start < 1:
                        vs.slice_start = 1

                else:
                    if vs.slice_start:
                        vs.slice_start += 1
                    else:
                        vs.slice_start = 1
                    if vs.slice_start > vs.slice_stop:
                        vs.slice_start = vs.slice_stop

            case key.BRACKETRIGHT:
                if modifiers and key.MOD_SHIFT:
                    vs.slice_stop -= 1
                    if vs.slice_stop < vs.slice_start:
                        vs.slice_stop = vs.slice_start
                else:
                    vs.slice_stop += 1
                    if vs.slice_stop > app.cube.size:
                        vs.slice_stop = app.cube.size

            # case key.P:
            #     op_and_play_animation(window, _last_face)

            case key.R:
                # _last_face = FaceName.R
                op.op(_slice_alg(algs.Algs.R), inv)
                # op.op(algs.Algs.R, inv)

            case key.L:
                op.op(_slice_alg(algs.Algs.L), inv)

            case key.U:
                op.op(_slice_alg(algs.Algs.U), inv)

            case key.F:
                op.op(_slice_alg(algs.Algs.F), inv)

            case key.S:
                op.op(_slice_alg(algs.Algs.S), inv)

            case key.B:
                op.op(_slice_alg(algs.Algs.B), inv)

            case key.D:
                _last_face = FaceName.D
                op.op(_slice_alg(algs.Algs.D), inv)

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
                op.op(_slice_alg(algs.Algs.M), inv)

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
                op.op(_slice_alg(algs.Algs.E), inv)

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

                alg = get_alg()
                op.op(alg, inv)

            case key.C:
                op.reset()
                app.reset(not (modifiers and key.MOD_CTRL))

            case key._0:
                with vs.w_animation_speed(4):
                    if modifiers & key.MOD_ALT:
                        # Faild on [5:5]B
                        # [{good} [3:3]R [3:4]D S [2:2]L]


                        alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]  # + Algs.B[5:5]
                        op.op(alg, inv), #animation=False)

                    elif modifiers & key.MOD_CTRL:
                        alg = Algs.B[5:5]
                        op.op(alg, inv)
                    else:
                        alg = Algs.scramble(app.cube.size, n=100)
                        op.op(alg, inv)

            case key._1:
                # noinspection PyProtectedMember
                alg = Algs.scramble(app.cube.size, value - key._0, 5)
                op.op(alg, inv, animation=False)

            case key._2 | key._3 | key._4 | key._5 | key._6:

                print(f"{modifiers & key.MOD_CTRL=}  {modifiers & key.MOD_ALT=}")
                if modifiers & key.MOD_CTRL:
                    # noinspection PyProtectedMember
                    balg: algs.BigAlg = Algs.scramble(app.cube.size, value - key._0)
                    good = algs.BigAlg("good")
                    for a in balg.algs:
                        try:
                            op.op(a, animation=False)
                            good = good + a
                        except:
                            from model.cube_queries import CubeQueries
                            CubeQueries.print_dist(app.cube)
                            print("Failed on", a)
                            print(good)
                            raise
                elif modifiers & key.MOD_ALT:
                    print("Rerunning good:", good)
                    for a in good.algs:
                        try:
                            op.op(a, animation=False)
                            from model.cube_queries import CubeQueries
                            CubeQueries.print_dist(app.cube)
                        except:
                            print(good)
                            raise

                else:
                    # to match test int
                    # noinspection PyProtectedMember
                    alg = Algs.scramble(app.cube.size, value - key._0)
                    op.op(alg, inv, animation=False)

            case key.COMMA:
                op.undo()

            case key.SLASH:
                # solution = slv.solution().simplify()
                # op.op(solution)
                slv.solve()

            case key.F1:
                slv.solve(what=SolveStep.L1)

            case key.F2:
                slv.solve(what=SolveStep.L2)

            case key.F3:

                if modifiers and key.MOD_CTRL:
                    slv.solve(what=SolveStep.L3x)
                else:
                    slv.solve(what=SolveStep.L3)

            case key.F4:

                slv.solve(what=SolveStep.NxNCenters)

            case key.F5:

                n0 = op.count
                slv.solve(what=SolveStep.NxNEdges)
                window._last_edge_solve_count = op.count - n0

            case key.T:
                if modifiers & key.MOD_ALT:
                    scramble_key = 26
                    n = None

                    op.reset()  # also reset cube
                    alg = Algs.scramble(app.cube.size, scramble_key, n)
                    op.op(alg, animation=False)
                    slv.solve(animation=False, debug=False)
                    assert slv.is_solved
                else:
                    # test
                    nn = 50
                    ll = 0
                    count = 0
                    n_loops = 0
                    for s in range(-1, nn):
                        print(str(s + 2) + f"/{nn + 1}, ", end='')
                        ll += 1
                        if ll > 15:
                            print()
                            ll = 0

                        op.reset()  # also reset cube
                        if s == -1:
                            scramble_key = -1
                            n = 5
                        else:
                            scramble_key = s
                            n = None

                        alg = Algs.scramble(app.cube.size, scramble_key, n)

                        op.op(alg, animation=False)

                        # noinspection PyBroadException
                        try:
                            c0 = op.count
                            slv.solve(animation=False, debug=False)
                            assert slv.is_solved
                            count += op.count - c0
                            n_loops += 1

                        except Exception:
                            print(f"Failure on scramble key={scramble_key}, n={n} ")
                            traceback.print_exc()
                            raise
                    print()
                    print(f"Count={count}, average={count / n_loops}")

            case key.Q:
                window.close()
                return

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


def main():
    app: Main = Main()
    Window(app, 720, 720, '"Cube"')
    pyglet.app.run()


if __name__ == '__main__':
    main()
