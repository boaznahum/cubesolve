import math
import time
import traceback
from collections.abc import Iterable, Collection, Set
from typing import MutableSequence, Callable

import glooey  # type: ignore
import numpy as np
import pyglet  # type: ignore
from numpy import ndarray
from pyglet import gl
from pyglet.window import key  # type: ignore

import algs
import config
from algs import Alg, Algs
from app_exceptions import AppExit, RunStop, OpAborted
from cube import Cube
from cube_operator import Operator
from elements import FaceName, PartSlice
from solver import Solver, SolveStep
from view_state import ViewState
from viewer_g import GCubeViewer


# pyglet.options["debug_graphics_batch"] = True


class Animation:

    def __init__(self) -> None:
        super().__init__()
        self.done: bool = False
        self._animation_update_only: Callable[[], None] | None = None
        self._animation_draw_only: Callable[[], None] | None = None
        self._animation_cleanup: Callable[[], None] | None = None
        self.delay = 1 / 20.

    def update_gui_elements(self):
        if self._animation_update_only:
            self._animation_update_only()

    def draw(self):
        if self._animation_draw_only:
            self._animation_draw_only()

    def cleanup(self):
        if self._animation_cleanup:
            self._animation_cleanup()


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
class Window(pyglet.window.Window):
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
        s += ", Sanity check:" + _b(config.CHECK_CUBE_SANITY)
        s += ", Debug=" + _b(self.app.slv.is_debug_config_mode)
        self.text.append(pyglet.text.Label(s,
                                           x=10, y=130, font_size=10, color=(255, 255, 0, 255), bold=True))
        # ----------------------------

        s = f"S={cube.size}, Is 3x3:{'Yes' if cube.is3x3 else 'No'}"

        s += ", Slices"
        vs = self.app.vs
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

    def draw_axis(self):
        gl.glPushAttrib(gl.GL_MATRIX_MODE)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        gl.glPushMatrix()

        gl.glLoadIdentity()
        gl.glTranslatef(0, 0, -400)

        # print_matrix("GL_MODELVIEW_MATRIX", gl.GL_MODELVIEW_MATRIX)
        # print_matrix("GL_PROJECTION_MATRIX", gl.GL_PROJECTION_MATRIX)
        # print_matrix("GL_VIEWPORT", gl.GL_VIEWPORT)

        # ideally we want the axis to be fixed, but in this case we won't see the Z,
        #  so we rotate the Axes, or we should change the perspective
        vs: ViewState = self.app.vs
        gl.glRotatef(math.degrees(vs.alpha_x_0), 1, 0, 0)
        gl.glRotatef(math.degrees(vs.alpha_y_0), 0, 1, 0)
        gl.glRotatef(math.degrees(vs.alpha_z_0), 0, 0, 1)

        gl.glPushAttrib(gl.GL_LINE_WIDTH)
        gl.glLineWidth(3)

        gl.glBegin(gl.GL_LINES)

        gl.glColor3ub(255, 255, 255)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(200, 0, 0)
        gl.glEnd()

        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(255, 0, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 200, 0)
        gl.glEnd()

        gl.glBegin(gl.GL_LINES)
        gl.glColor3ub(0, 255, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 0, 200)

        gl.glEnd()

        gl.glPopAttrib()  # line width

        # Pop Matrix off stack
        gl.glPopMatrix()
        gl.glPopAttrib()  # GL_MATRIX_MODE

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
def _create_animation(window: Window, alg: algs.AnimationAbleAlg, n_count) -> Animation:
    rotate_face: FaceName
    cube_parts: Collection[PartSlice]

    rotate_face, cube_parts = alg.get_animation_objects(window.app.cube)

    # to be on the safe side !!!
    if not isinstance(cube_parts, Set):
        cube_parts = set(cube_parts)

    face_center: ndarray
    opposite_face_center: ndarray
    gui_objects: Iterable[int]

    viewer = window.viewer
    face_center, opposite_face_center, gui_objects = viewer.get_slices_movable_gui_objects(rotate_face, cube_parts)

    #
    # if alg.face:
    #     face_center, opposite_face_center, gui_objects = viewer.get_face_objects(alg.face)
    # elif alg.axis_name:
    #     face_center, opposite_face_center, gui_objects = viewer.git_whole_cube_objects(alg.axis_name)
    # elif alg.slice_name:
    #     face_center, opposite_face_center, gui_objects = viewer.git_slice_objects(alg.slice_name)
    # else:
    #     raise TimeoutError(f"At lest face/axis/slice name in {alg}")

    vs: ViewState = window.app.vs
    current_angel = 0

    # compute target_angel
    n = n_count % 4
    if n == 3:
        n = -1
    target_angel = math.radians(90 * n)
    angel_delta = target_angel / float(window.app.vs.animation_speed_number_of_steps)

    # Rotate A Point
    # About An Arbitrary Axis
    # (3 Dimensions)
    # Written by Paul Bourke
    # https://www.eng.uc.edu/~beaucag/Classes/Properties/OptionalProjects/CoordinateTransformationCode/Rotate%20about%20an%20arbitrary%20axis%20(3%20dimensions).html#:~:text=Step%202-,Rotate%20space%20about%20the%20x%20axis%20so%20that%20the%20rotation,no%20additional%20rotation%20is%20necessary.

    x1 = face_center[0]
    y1 = face_center[1]
    z1 = face_center[2]
    T: ndarray = np.array([[1, 0, 0, -x1],
                           [0, 1, 0, -y1],
                           [0, 0, 1, -z1],
                           [0, 0, 0, 1]
                           ], dtype=float)
    TT = np.linalg.inv(T)
    U = (face_center - opposite_face_center) / np.linalg.norm(face_center - opposite_face_center)
    a = U[0]
    b = U[1]
    c = U[2]
    d = math.sqrt(b * b + c * c)
    if d == 0:
        Rx = np.array([[1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]], dtype=float)
    else:
        Rx = np.array([[1, 0, 0, 0],
                       [0, c / d, -b / d, 0],
                       [0, b / d, c / d, 0],
                       [0, 0, 0, 1]], dtype=float)

    RxT = np.linalg.inv(Rx)

    Ry = np.array([[d, 0, -a, 0],
                   [0, 1, 0, 0],
                   [a, 0, d, 0],
                   [0, 0, 0, 1]], dtype=float)

    RyT = np.linalg.inv(Ry)

    # TT @ RxT @ RyT @ Rz @ Ry @ Rx @ T
    MT: ndarray = TT @ RxT @ RyT  # ? == inv(M)
    M: ndarray = Ry @ Rx @ T

    animation = Animation()
    animation.done = False
    animation._animation_cleanup = lambda: viewer.unhidden_all()

    # noinspection PyPep8Naming

    last_update = time.time()

    def _update():

        nonlocal current_angel
        nonlocal last_update

        # print(f"In update before {current_angel=} {target_angel}")
        if (time.time() - last_update) > animation.delay:
            _angel = current_angel + angel_delta

            if abs(_angel) > abs(target_angel):

                if current_angel < target_angel:
                    current_angel = target_angel
                else:
                    animation.done = True
            else:
                # don't update if done, make animation smoother, no jump at end
                current_angel = _angel

            last_update = time.time()

        # print(f"In update after {current_angel=} {target_angel}")

    # noinspection PyPep8Naming
    def _draw():

        nonlocal current_angel

        # print(f"In _draw {current_angel=} {target_angel=}")

        if abs(current_angel) > abs(target_angel):
            animation.done = True
            return

        vs.prepare_objects_view()

        ct = math.cos(current_angel)
        st = math.sin(current_angel)
        Rz = np.array([[ct, st, 0, 0],
                       [-st, ct, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]], dtype=float)

        m: ndarray = MT @ Rz @ M

        gm = (gl.GLfloat * 16)(0)
        # column major
        gm[:] = m.flatten(order="F")

        gl.glMultMatrixf(gm)

        try:
            for f in gui_objects:
                gl.glCallList(f)
        finally:
            vs.restore_objects_view()

        return True

    animation.delay = window.app.vs.animation_speed_delay_between_steps
    animation._animation_draw_only = _draw
    animation._animation_update_only = _update

    return animation

    # def _fire_event(dt):
    #     window.dispatch_event("on_draw")
    #
    # func = _fire_event
    #
    # pyglet.clock.schedule_interval(func, 1 / 10)


def op_and_play_animation(window: Window, operator: Operator, inv: bool, alg: algs.SimpleAlg):
    """
    This must be called only from operator
    :param window:
    :param operator:
    :param inv:
    :param alg:
    :return:
    """
    # if True:
    #     operator.op(alg, inv, animation=False)
    #     return

    if not operator.animation_enabled:
        operator.op(alg, inv)
        return

    event_loop = pyglet.app.event_loop

    if event_loop.has_exit:
        return  # maybe long alg is still running

    platform_event_loop = pyglet.app.platform_event_loop

    if alg.is_ann:
        operator.op(alg, inv, animation=False)
        window.update_gui_elements()
        #        time.sleep(1)
        platform_event_loop.notify()
        return

    if inv:
        _alg = alg.inv().simplify()
        assert isinstance(_alg, algs.SimpleAlg)
        alg = _alg
        inv = False

    if not isinstance(alg, algs.AnimationAbleAlg):
        print(f"{alg} is not animation-able")
        operator.op(alg, False, animation=False)
        return

    animation: Animation = _create_animation(window, alg, alg.n)
    delay: float = animation.delay

    # this is called from window.on_draw
    window._animation = animation

    def _update(_):
        animation.update_gui_elements()
        platform_event_loop.notify()

    clock: pyglet.clock.Clock = event_loop.clock
    clock.schedule_interval(_update, delay)

    # copied from EventLoop#run
    while not event_loop.has_exit and not animation.done:
        timeout = event_loop.idle()  # this will trigger on_draw
        platform_event_loop.step(timeout)

    if event_loop.has_exit:
        return

    clock.unschedule(_update)

    # while not animation.done:
    #     window.on_draw()
    #     time.sleep(delay)

    animation.cleanup()
    #     if animation.done:
    #         break  # don't sleep !!!
    #     window.flip()

    window._animation = None

    operator.op(alg, False, animation=False)

    window.update_gui_elements()  # most important !!! otherwise animation jumps
    # window.on_draw()
    # window.flip()


_last_face: FaceName = FaceName.R

good = algs._BigAlg("good")


def _handle_input(window: Window, value: int, modifiers: int):
    # print(f"{hex(value)}=")
    done = False
    app: Main = window.app
    op: Operator = app.op

    print(f"In _handle_input , {value}  {hex(value)} {chr(ord('A') + (value - key.A))} ")

    if window.animation_running or op.is_animation_running:
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
    vs: ViewState = app.vs

    inv = modifiers & key.MOD_SHIFT

    no_operation = False

    global _last_face

    alg: Alg

    def _slice_alg(r: algs.SliceAbleAlg):
        return vs.slice_alg(app.cube, r)

    global good
    # noinspection PyProtectedMember
    match value:


        case key.I:
            print(f"{vs.alpha_x + vs.alpha_x_0=} {vs.alpha_y+vs.alpha_y_0=} {vs.alpha_z+vs.alpha_z_0=}")
            no_operation = True
            from cube_queries import CubeQueries
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
            if modifiers & key.MOD_ALT:
                # Faild on [5:5]B
                # [{good} [3:3]R [3:4]D S [2:2]L]

                alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]  # + Algs.B[5:5]
                op.op(alg, inv, animation=False)

            elif modifiers & key.MOD_CTRL:
                alg = Algs.B[5:5]
                op.op(alg, inv, animation=False)
            else:
                alg = Algs.scramble(app.cube.size)
                op.op(alg, inv, animation=False)

        case key._1:
            # noinspection PyProtectedMember
            alg = Algs.scramble(app.cube.size, value - key._0, 5)
            op.op(alg, inv, animation=False)

        case key._2 | key._3 | key._4 | key._5 | key._6:

            print(f"{modifiers & key.MOD_CTRL=}  {modifiers & key.MOD_ALT=}")
            if modifiers & key.MOD_CTRL:
                balg: algs._BigAlg = Algs.scramble(app.cube.size, value - key._0)
                good = algs._BigAlg("good")
                for a in balg.algs:
                    try:
                        op.op(a, animation=False)
                        good = good + a
                    except:
                        from cube_queries import CubeQueries
                        CubeQueries.print_dist(app.cube)
                        print("Faild on", a)
                        print(good)
                        raise
            elif modifiers & key.MOD_ALT:
                print("Rerunning good:", good)
                for a in good.algs:
                    try:
                        op.op(a, animation=False)
                        from cube_queries import CubeQueries
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
                        n_loops +=1

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
