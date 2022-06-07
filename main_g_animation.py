import math
import time
from abc import ABC, abstractmethod
from collections.abc import Collection, Set, Iterable
from typing import Callable
import numpy as np
from numpy import ndarray
from pyglet import gl  # type: ignore
import pyglet  # type: ignore

from algs import algs
from app_state import ViewState
from cube_operator import Operator
from model.cube import Cube
from model.cube_boy import FaceName
from model.elements import PartSlice
from viewer.viewer_g import GCubeViewer




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


class AbstractWindow(pyglet.window.Window):

    @abstractmethod
    def set_animation(self, an: Animation | None):
        pass

    @abstractmethod
    def update_gui_elements(self):
        pass


def _create_animation(cube: Cube, viewer: GCubeViewer, vs: ViewState, alg: algs.AnimationAbleAlg, n_count) -> Animation:
    rotate_face: FaceName
    cube_parts: Collection[PartSlice]

    rotate_face, cube_parts = alg.get_animation_objects(cube)

    # to be on the safe side !!!
    if not isinstance(cube_parts, Set):
        cube_parts = set(cube_parts)

    face_center: ndarray
    opposite_face_center: ndarray
    gui_objects: Iterable[int]

    face_center, opposite_face_center, gui_objects = viewer.get_slices_movable_gui_objects(rotate_face, cube_parts)

    current_angel = 0

    # compute target_angel
    n = n_count % 4
    if n == 3:
        n = -1
    target_angel = math.radians(90 * n)
    angel_delta = target_angel / float(vs.animation_speed_number_of_steps)

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

    animation.delay = vs.animation_speed_delay_between_steps
    animation._animation_draw_only = _draw
    animation._animation_update_only = _update

    return animation


def op_and_play_animation(window: AbstractWindow, cube: Cube, viewer: GCubeViewer, vs: ViewState, operator: Operator, inv: bool, alg: algs.SimpleAlg):
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

    animation: Animation = _create_animation(cube, viewer, vs, alg, alg.n)
    delay: float = animation.delay

    # this is called from window.on_draw
    window.set_animation(animation)

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

    window.set_animation(None)

    operator.op(alg, False, animation=False)

    window.update_gui_elements()  # most important !!! otherwise animation jumps
    # window.on_draw()
    # window.flip()
