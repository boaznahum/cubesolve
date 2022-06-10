import math
import time
from collections.abc import Collection, Set, Iterable

import numpy as np
import pyglet  # type: ignore
from numpy import ndarray
from pyglet import gl  # type: ignore

from algs import algs
from app_state import AppState
from cube_operator import Operator
from main_g_abstract import Animation, AbstractWindow
from model.cube import Cube
from model.cube_boy import FaceName
from model.elements import PartSlice
from viewer.viewer_g import GCubeViewer


def op_and_play_animation(window: AbstractWindow, operator: Operator, inv: bool, alg: algs.SimpleAlg):
    _op_and_play_animation(window,
                           window.app.cube,
                           window.viewer,
                           window.app.vs,
                           operator,
                           inv, alg)


def _create_animation(cube: Cube, viewer: GCubeViewer, vs: AppState, alg: algs.AnimationAbleAlg, n_count) -> Animation:
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

        model_view: ndarray = mt @ Rz @ m

        gm = (gl.GLfloat * 16)(0)
        # column major
        gm[:] = model_view.flatten(order="F")

        gl.glMultMatrixf(gm)

        try:
            for f in gui_objects:
                gl.glCallList(f)
        finally:
            vs.restore_objects_view()

        return True

    animation.delay = animation_speed.delay_between_steps
    animation._animation_draw_only = _draw
    animation._animation_update_only = _update

    return animation


def _op_and_play_animation(window: AbstractWindow, cube: Cube, viewer: GCubeViewer, vs: AppState, operator: Operator,
                           inv: bool, alg: algs.SimpleAlg):
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

    if not operator.animation_enabled:
        operator.op(alg, inv)
        return

    event_loop = pyglet.app.event_loop

    if event_loop.has_exit:
        return  # maybe long alg is still running

    platform_event_loop = pyglet.app.platform_event_loop

    if isinstance(alg, algs.Annotation):
        text1 = alg.text1
        text2 = alg.text2

        window.set_annotation_text(text1, text2)

        operator.op(alg, inv, animation=False)
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
        operator.op(alg, False, animation=False)
        return

    clock: pyglet.clock.Clock = event_loop.clock

    # single step mode ?
    if vs.single_step_mode:

        vs.paused_on_single_step_mode = alg

        def _update_gui(_):
            window.update_gui_elements()
            platform_event_loop.notify()

        # TO UPDATE TEXT
        clock.schedule_once(_update_gui, 0)

        # wait for user press space
        while not event_loop.has_exit and vs.paused_on_single_step_mode:
            timeout = event_loop.idle()  # this will trigger on_draw
            platform_event_loop.step(timeout)

    # but still useful for SS mode
    if alg.n % 4 == 0:
        print(f"{alg} is zero rotating, can't animate")
        operator.op(alg, False, animation=False)
        return

    animation: Animation = _create_animation(cube, viewer, vs, alg, alg.n)
    delay: float = animation.delay

    # this is called from window.on_draw
    window.set_animation(animation)

    def _update(_):
        animation.update_gui_elements()
        platform_event_loop.notify()

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
