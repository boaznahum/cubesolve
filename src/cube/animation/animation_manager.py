import math
import time
from abc import ABC, abstractmethod
from collections.abc import Collection, Set, Iterable
from typing import Callable, TypeAlias

import numpy as np
import pyglet  # type: ignore
from numpy import ndarray
from pyglet import gl  # type: ignore

from cube import algs
from cube.algs import SimpleAlg
from cube.app.app_state import ApplicationAndViewState
from cube.model import PartSlice
from cube.model.cube import Cube
from cube.model.cube_boy import FaceName
from cube.viewer.viewer_g import GCubeViewer
from cube.gui.protocols.renderer import Renderer
from cube.gui.types import DisplayList

OpProtocol: TypeAlias = Callable[[algs.Alg, bool], None]


class Animation:

    def __init__(self) -> None:
        super().__init__()
        self.done: bool = False
        self._animation_update_only: Callable[[], bool] | None = None
        self._animation_draw_only: Callable[[], None] | None = None
        self._animation_cleanup: Callable[[], None] | None = None
        self.delay = 1 / 20.

    def update_gui_elements(self) -> bool:
        if self._animation_update_only:
            return self._animation_update_only()
        else:
            return False

    def draw(self):
        if self._animation_draw_only:
            self._animation_draw_only()

    def cleanup(self):
        if self._animation_cleanup:
            self._animation_cleanup()


class AnimationWindow:
    """
    A window that accepts animation operations
    """

    @property
    @abstractmethod
    def viewer(self) -> GCubeViewer:
        pass

    @abstractmethod
    def update_gui_elements(self):
        pass


class AnimationManager(ABC):
    __slots__ = ["_window", "_current_animation", "_vs"]

    def __init__(self,
                 vs: ApplicationAndViewState):
        self._vs = vs
        self._window: AnimationWindow | None = None
        self._current_animation: Animation | None = None

    def set_window(self, window: AnimationWindow):
        """
        PATCH PATCH PATCH
        :param window:
        :return:
        """
        self._window = window

    # noinspection PyMethodMayBeStatic
    def run_animation(self, cube: Cube, op: OpProtocol, alg: SimpleAlg):
        assert self._window
        _op_and_play_animation(self._window,
                               cube,
                               self._set_animation,
                               self._window.viewer,
                               self._vs,
                               op, False, alg)

    def animation_running(self) -> Animation | None:
        """
        Indicate that the animation hook start and animation _set_animation_was called
        todo: why run_animation is not enough ?
        Usually it is enough to check if Operator:is_animation_running
        because it invokes the animation hook that invokes the windows
        :return:
        """

        return self._current_animation

    def update_gui_elements(self):
        an = self._current_animation
        if an:
            an.update_gui_elements()

    def draw(self):
        an = self._current_animation
        if an:
            an.draw()

    def _set_animation(self, animation: Animation | None):

        if animation:
            assert not self._current_animation

        self._current_animation = animation


def _op_and_play_animation(window: AnimationWindow,
                           cube: Cube,
                           animation_sink: Callable[[Animation | None], None],
                           viewer: GCubeViewer,
                           vs: ApplicationAndViewState,
                           operator: OpProtocol,
                           inv: bool,
                           alg: algs.SimpleAlg):
    """
    This must be called only from operator
    :param viewer:
    :param vs:
    :param cube:
    :param window:
    :param operator:
    :param inv:
    :param alg:
    :return:
    """
    # if True:
    #     operator.op(alg, inv, animation=False)
    #     return

    event_loop = pyglet.app.event_loop

    if event_loop.has_exit:
        return  # maybe long alg is still running

    platform_event_loop = pyglet.app.platform_event_loop

    if isinstance(alg, algs.AnnotationAlg):
        operator(alg, inv)
        window.update_gui_elements()
        #        time.sleep(1)
        platform_event_loop.notify()
        return

    if inv:
        _alg = alg.inv().simplify()
        assert isinstance(_alg, algs.SimpleAlg)
        alg = _alg

    if not isinstance(alg, algs.AnimationAbleAlg):
        print(f"{alg} is not animation-able")
        operator(alg, False)
        return

    clock: pyglet.clock.Clock = event_loop.clock

    # single step mode ?
    if vs.single_step_mode:

        vs.paused_on_single_step_mode = alg

        def _update_gui(_):
            window.update_gui_elements()

        event_loop = pyglet.app.event_loop

        # bug in stop behaviour
        #  we press abort, operator accept in and turn internal flag
        #  but here we wait for space
        # after space is pressed we back to operator
        #  check for abort and quit loop
        # So to fix, we need to check here too, in the event loop
        # meanwhile it is a patch
        try:
            # If you read event loop, only handled events cause to redraw
            clock.schedule_once(_update_gui, 0)

            vs.single_step_mode_stop_pressed = False
            while (not event_loop.has_exit and (vs.paused_on_single_step_mode and vs.single_step_mode)
                   and not vs.single_step_mode_stop_pressed):
                timeout = event_loop.idle()
                platform_event_loop.step(timeout)
        finally:
            vs.paused_on_single_step_mode = None

        if vs.single_step_mode_stop_pressed:
            return

    # but still useful for SS mode
    if alg.n % 4 == 0:
        print(f"{alg} is zero rotating, can't animate")
        operator(alg, False)
        return

    animation: Animation = _create_animation(cube, viewer, vs, alg, alg.n, viewer.renderer)
    delay: float = animation.delay

    # animation.draw() is called from window.on_draw
    animation_sink(animation)

    def _update(_):
        # Advance to next animation step
        animation.update_gui_elements()
        #     vs.skip_next_on_draw = "animation update no change"  # display flicks

    try:
        # If you read event loop, only handled events cause to redraw so after _update, window_on_draw will draw the
        # animation if any other model state is changed, it will update during keyboard handling,
        # and animation.update_gui_elements() will be re-called (is it a problem?) and then redraw again
        # window.on_redraw
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

    finally:
        animation_sink(None)

    operator(alg, False)

    # most important !!! otherwise animation jumps
    # not clear why
    window.update_gui_elements()


def _create_animation(cube: Cube, viewer: GCubeViewer, vs: ApplicationAndViewState, alg: algs.AnimationAbleAlg,
                      n_count, renderer: Renderer | None = None) -> Animation:
    rotate_face: FaceName
    cube_parts: Collection[PartSlice]

    # the rotated face determiners the direction of rotation
    #  by the vector orthogonal to it
    rotate_face, cube_parts = alg.get_animation_objects(cube)

    # to be on the safe side !!!
    if not isinstance(cube_parts, Set):
        cube_parts = set(cube_parts)

    face_center: ndarray
    opposite_face_center: ndarray
    gui_objects: Iterable[int]

    face_center, opposite_face_center, gui_objects = viewer.get_slices_movable_gui_objects(rotate_face, cube_parts)

    current_angel: float = 0

    # compute target_angel
    n = n_count % 4
    if n == 3:
        n = -1
    target_angel = math.radians(90 * n)
    animation_speed = vs.get_speed
    angel_delta = target_angel / float(animation_speed.number_of_steps) / math.fabs(n)

    # Rotate A Point
    # About An Arbitrary Axis
    # (3 Dimensions)
    # Written by Paul Bourke
    # https://www.eng.uc.edu/~beaucag/Classes/Properties/OptionalProjects/CoordinateTransformationCode/Rotate%20about%20an%20arbitrary%20axis%20(3%20dimensions).html#:~:text=Step%202-,Rotate%20space%20about%20the%20x%20axis%20so%20that%20the%20rotation,no%20additional%20rotation%20is%20necessary.

    x1 = face_center[0]
    y1 = face_center[1]
    z1 = face_center[2]
    t: ndarray = np.array([[1, 0, 0, -x1],
                           [0, 1, 0, -y1],
                           [0, 0, 1, -z1],
                           [0, 0, 0, 1]
                           ], dtype=float)
    tt = np.linalg.inv(t)
    u = (face_center - opposite_face_center) / np.linalg.norm(face_center - opposite_face_center)
    a = u[0]
    b = u[1]
    c = u[2]
    d = math.sqrt(b * b + c * c)
    if d == 0:
        rx = np.array([[1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]], dtype=float)
    else:
        rx = np.array([[1, 0, 0, 0],
                       [0, c / d, -b / d, 0],
                       [0, b / d, c / d, 0],
                       [0, 0, 0, 1]], dtype=float)

    rx_t = np.linalg.inv(rx)

    ry = np.array([[d, 0, -a, 0],
                   [0, 1, 0, 0],
                   [a, 0, d, 0],
                   [0, 0, 0, 1]], dtype=float)

    ry_t = np.linalg.inv(ry)

    # tt @ rx_t @ ry_t @ Rz @ ry @ rx @ T
    mt: ndarray = tt @ rx_t @ ry_t  # ? == inv(M)
    m: ndarray = ry @ rx @ t

    animation = Animation()
    animation.done = False
    animation._animation_cleanup = lambda: viewer.unhidden_all()

    # noinspection PyPep8Naming

    last_update = time.time()

    def _update() -> bool:

        nonlocal current_angel
        nonlocal last_update

        # print(f"In update before {current_angel=} {target_angel}")
        if (time.time() - last_update) > animation.delay:
            _angel = current_angel + angel_delta

            if abs(_angel) > abs(target_angel):

                # don't update if done, make animation smoother, no jump at end

                if current_angel < target_angel:
                    current_angel = target_angel
                else:
                    animation.done = True
            else:
                current_angel = _angel

            last_update = time.time()

            return True
        else:
            return False # update was not done

        # print(f"In update after {current_angel=} {target_angel}")

    # noinspection PyPep8Naming
    def _draw() -> None:

        nonlocal current_angel

        # print(f"In _draw {current_angel=} {target_angel=}")

        if abs(current_angel) > abs(target_angel):
            animation.done = True
            return # False

        vs.prepare_objects_view()

        ct = math.cos(current_angel)
        st = math.sin(current_angel)
        Rz = np.array([[ct, st, 0, 0],
                       [-st, ct, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]], dtype=float)

        model_view: ndarray = mt @ Rz @ m

        gm = (gl.GLfloat * 16)(0)
        # column major
        gm[:] = model_view.flatten(order="F")

        gl.glMultMatrixf(gm)

        try:
            if renderer is None:
                raise RuntimeError("Renderer is required but not configured. Use BackendRegistry.create_renderer()")
            # Use renderer to call display lists (maps internal IDs to GL IDs)
            for f in gui_objects:
                renderer.display_lists.call_list(DisplayList(f))
        finally:
            vs.restore_objects_view()

        #return True

    animation.delay = animation_speed.delay_between_steps
    animation._animation_draw_only = _draw
    animation._animation_update_only = _update

    return animation
