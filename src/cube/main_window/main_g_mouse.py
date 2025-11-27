#
#
#  Handles rotating with the mouse
#
#
import functools
import math
from typing import Tuple, Any

import numpy as np
from numpy import ndarray
from pyglet.window import key, mouse  # type: ignore
from pyglet import gl  # type: ignore

from cube.config import INPUT_MOUSE_DEBUG as INPUT_MOUSE_DEBUG
from cube.config import INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM as INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM
from cube.config import INPUT_MOUSE_ROTATE_ADJUSTED_FACE as INPUT_MOUSE_ROTATE_ADJUSTED_FACE

from cube.algs.SliceAlg import SliceAlg
from cube.algs import Alg, Algs
from cube.app.abstract_ap import AbstractApp
from cube.app.app_exceptions import InternalSWError
from cube.app.app_state import ApplicationAndViewState
from .main_g_abstract import AbstractWindow
from cube.model.cube_boy import FaceName
from cube.model.cube_face import Face
from cube.model import PartEdge, PartSlice, Part, Corner, Edge, EdgeWing, CenterSlice

# to avoid the case we start another handling while animation is running
_FACE_ROTATING_BY_MOUSE_MOUSE_ALG_IS_RUNNING = False

_DRAG_VECTOR_DETECTION_DATA_LENGTH = 10

# https://stackoverflow.com/questions/34608657/mouse-drag-direction-tolerance
_DRAG_VECTOR_DETECTION_DATA: list[Tuple[int, int]] = []
_DRAG_VECTOR_DETECTION_DATA_X0_Y0: Tuple[int, int] = (0, 0)


def on_mouse_drag(win: AbstractWindow, x, y, dx, dy, buttons, modifiers):
    # these are persevered for clik slicing, and panning
    if not modifiers & (key.MOD_SHIFT | key.MOD_CTRL | key.MOD_ALT):

        if INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM:
            if buttons & mouse.RIGHT:
                _handle_model_view_rotate_by_drag(win, dx, dy)
            else:
                # don't allow cube modification during animation
                if win.app.op.is_animation_running:
                    return
                _handle_face_slice_rotate_by_drag(win, x, y, dx, dy)

    elif (modifiers & key.MOD_ALT) == key.MOD_ALT:

        win.app.vs.change_offset(dx, dy, 0)


def on_mouse_press(window: AbstractWindow, vs: ApplicationAndViewState, x, y, modifiers):
    # don't allow cube modification during animation
    if window.app.op.is_animation_running:
        return

    if modifiers & (key.MOD_SHIFT | key.MOD_CTRL):

        selected: tuple[PartEdge, ndarray, Any] | None = _get_selected_slice(vs, window, x, y)

        if selected:
            _handle_selected_slice(window, selected[0], modifiers & key.MOD_CTRL)


def on_mouse_release():
    global _DRAG_VECTOR_DETECTION_DATA

    # cancel data collection
    _DRAG_VECTOR_DETECTION_DATA.clear()


def on_mouse_scroll(window: AbstractWindow, scroll_y):
    vs = window.app.vs

    vs.change_fov_y(scroll_y)

    vs.set_projection(window.width, window.height)


def _handle_model_view_rotate_by_drag(win, dx, dy):
    app = win.app

    # print(f"{dx=}, {dy=}")
    # https://stackoverflow.com/questions/59823131/how-to-rotate-a-cube-using-mouse-in-pyopengl
    # if event.type == pygame.MOUSEMOTION:
    #                 if button_down == True:
    #                     glRotatef(event.rel[1], 1, 0, 0)
    #                     glRotatef(event.rel[0], 0, 1, 0)
    #                 print(event.rel)

    # still don't know to distinguish between ad drag and simple press
    app.vs.alpha_x += math.radians(-dy)
    app.vs.alpha_y += math.radians(dx)


def _handle_face_slice_rotate_by_drag(window: AbstractWindow, x, y, dx, dy):
    global _FACE_ROTATING_BY_MOUSE_MOUSE_ALG_IS_RUNNING

    if INPUT_MOUSE_DEBUG:
        print(f"Mouse drag: Handler started: {x=}, {y=})")

    if _FACE_ROTATING_BY_MOUSE_MOUSE_ALG_IS_RUNNING:
        return

    global _DRAG_VECTOR_DETECTION_DATA
    global _DRAG_VECTOR_DETECTION_DATA_LENGTH
    global _DRAG_VECTOR_DETECTION_DATA_X0_Y0

    data = _DRAG_VECTOR_DETECTION_DATA

    data.append((dx, dy))

    n = len(data)

    if n == 1:  # first point
        _DRAG_VECTOR_DETECTION_DATA_X0_Y0 = (x, y)

    # print(f"{n}")

    if n < _DRAG_VECTOR_DETECTION_DATA_LENGTH:
        if INPUT_MOUSE_DEBUG:
            print(f"Mouse drag: Not enough points {n} / {_DRAG_VECTOR_DETECTION_DATA_LENGTH}")
        # Since we add a texture, draw become expansive (don't know why)
        #  so we found that we are not handling these events fast enough, so never slicing/rotating (big cube)
        window.app.vs.skip_next_on_draw = True
        return

    dx = functools.reduce(lambda s, t: s + t[0], data, 0) / n
    dy = functools.reduce(lambda s, t: s + t[1], data, 0) / n

    data.clear()  # prepare for next

    app: AbstractApp = window.app

    x, y = _DRAG_VECTOR_DETECTION_DATA_X0_Y0

    selected: tuple[PartEdge, ndarray, Any] | None = _get_selected_slice(app.vs, window, x, y)

    if not selected:
        if INPUT_MOUSE_DEBUG:
            print(f"Mouse drag: Didn't find selected element: {x=}, {y=})")

        return

    # print(f"{selected}")

    slice_edge: PartEdge = selected[0]
    left_to_right = selected[1]
    left_to_top = selected[2]

    p0 = _screen_to_model(app.vs, window, x, y)  # todo we already in selected !!!
    p1 = _screen_to_model(app.vs, window, x + dx, y + dy)
    d_vector: ndarray = p1 - p0

    on_left_to_right = d_vector.dot(left_to_right)
    on_left_to_top = d_vector.dot(left_to_top)

    part_slice: PartSlice = slice_edge.parent
    part: Part = part_slice.parent

    if INPUT_MOUSE_DEBUG:
        print(f"Mouse drag:{type(part)=}, { part_slice.index=}, {d_vector=}, {on_left_to_right=}, {on_left_to_top=}")

    it_left_to_right = abs(on_left_to_right) > abs(on_left_to_top)

    rotate_adjusted_face = INPUT_MOUSE_ROTATE_ADJUSTED_FACE

    _FACE_ROTATING_BY_MOUSE_MOUSE_ALG_IS_RUNNING = True
    try:
        slice_face = slice_edge.face

        if isinstance(part, Corner):
            # print("Is corner")

            if rotate_adjusted_face:

                alg, inv = _handle_slice_on_corner_adjusted_face(slice_face,
                                                                 it_left_to_right,
                                                                 on_left_to_right,
                                                                 on_left_to_top, part)
            else:
                alg, inv = _handle_slice_on_corner_same_face(slice_face,
                                                             it_left_to_right,
                                                             on_left_to_right,
                                                             on_left_to_top, part)

        elif isinstance(part, Edge):

            alg, inv = _handle_slice_on_edge(rotate_adjusted_face,
                                             slice_face, part, slice_edge, it_left_to_right, on_left_to_right,
                                             on_left_to_top)

        elif isinstance(part_slice, CenterSlice):
            c_index: tuple[int, int] = part_slice.index
            xi = c_index[1]
            yi = c_index[0]

            if it_left_to_right:
                alg = _slice_on_edge_alg(slice_face.edge_right, slice_face, yi, on_center=True)
                inv = on_left_to_right < 0
            else:
                alg = _slice_on_edge_alg(slice_face.edge_top, slice_face, xi, on_center=True)
                inv = on_left_to_top < 0

        else:
            raise InternalSWError

        if alg:
            if inv:
                alg = alg.inv()
            _play(window, alg)

    finally:
        _FACE_ROTATING_BY_MOUSE_MOUSE_ALG_IS_RUNNING = False


def _handle_slice_on_edge(rotate_adjusted_face: bool,
                          slice_face: Face,
                          part: Edge,
                          slice_edge: PartEdge,
                          it_left_to_right: bool,
                          on_left_to_right: bool,
                          on_left_to_top: bool) -> Tuple[Alg, bool]:
    """
    Handle slice on edge
    :param it_left_to_right: the significant movement is left to right on_left_to_right>on_left_to_top
    :param on_left_to_right: the movement in left to right direction
    :param on_left_to_top: the movement in left to top direction
    :param part: the part where mouse was dragged
    :param slice_face:

    """

    if part is slice_face.edge_right:
        if it_left_to_right:  # slicing
            alg = _slice_on_part_edge_alg(slice_edge)
            inv = on_left_to_right < 0  # D is left to right
        else:
            if rotate_adjusted_face:
                alg, inv = _handle_slice_on_edge_adjusted_face(slice_face, part, on_left_to_right, on_left_to_top)
            else:
                alg = Algs.of_face(slice_face.name)
                inv = on_left_to_top > 0

    elif part is slice_face.edge_left:
        if it_left_to_right:  # slicing
            alg = _slice_on_part_edge_alg(slice_edge)
            inv = on_left_to_right < 0  # D is left to right
        else:
            if rotate_adjusted_face:
                alg, inv = _handle_slice_on_edge_adjusted_face(slice_face, part, on_left_to_right, on_left_to_top)
            else:
                alg = Algs.of_face(slice_face.name)
                inv = on_left_to_top < 0

    elif part is slice_face.edge_top:
        if not it_left_to_right:  # slicing
            alg = _slice_on_part_edge_alg(slice_edge)
            inv = on_left_to_top < 0  # R is left to top
        else:
            if rotate_adjusted_face:
                alg, inv = _handle_slice_on_edge_adjusted_face(slice_face, part, on_left_to_right, on_left_to_top)
            else:
                alg = Algs.of_face(slice_face.name)
                inv = on_left_to_right < 0
    elif part is slice_face.edge_bottom:
        if not it_left_to_right:  # slicing
            alg = _slice_on_part_edge_alg(slice_edge)
            inv = on_left_to_top < 0  # R is left to top
        else:
            if rotate_adjusted_face:
                alg, inv = _handle_slice_on_edge_adjusted_face(slice_face, part, on_left_to_right, on_left_to_top)
            else:
                alg = Algs.of_face(slice_face.name)
                inv = on_left_to_right > 0
    else:
        raise InternalSWError

    return alg, inv


def _handle_slice_on_edge_adjusted_face(slice_face: Face,
                                        part: Edge,
                                        on_left_to_right: float,
                                        on_left_to_top: float) -> Tuple[Alg, bool]:
    """
    When edge is dragged, if rotate the adjusted face. e.g. when front right face is dragged,
    rotate right face

    :param on_left_to_right: the movement in left to right direction
    :param on_left_to_top: the movement in left to top direction
    :param part: the part where mouse was dragged
    :param slice_face:

    """

    adjusted_face = part.get_other_face(slice_face)
    face_alg = Algs.of_face(adjusted_face.name)

    if part is slice_face.edge_right:

        inv = on_left_to_top < 0

    elif part is slice_face.edge_left:

        inv = on_left_to_top > 0

    elif part is slice_face.edge_top:

        inv = on_left_to_right > 0

    elif part is slice_face.edge_bottom:
        inv = on_left_to_right < 0

    else:
        raise InternalSWError

    return face_alg, inv


def _handle_slice_on_corner_same_face(slice_face: Face,
                                      it_left_to_right: bool,
                                      on_left_to_right: float,
                                      on_left_to_top: float,
                                      part: Corner) -> Tuple[Alg, bool]:
    """
    The face where the part slice was dragged
    Rotate the face the that belong the corner facet that was dragged

    :param it_left_to_right: the significant movement is left to right on_left_to_right>on_left_to_top
    :param on_left_to_right: the movement in left to right direction
    :param on_left_to_top: the movement in left to top direction
    :param part: the part where mouse was dragged
    :param slice_face:
    :return:
    """

    alg: Alg = Algs.of_face(slice_face.name)
    if part is slice_face.corner_top_right:
        #   ----|  ^
        #       |  |
        #    -->
        if it_left_to_right:
            inv = on_left_to_right < 0
        else:
            inv = on_left_to_top > 0
    elif part is slice_face.corner_top_left:
        #   |----  ^
        #   |      |
        #    -->
        if it_left_to_right:
            inv = on_left_to_right < 0
        else:
            inv = on_left_to_top < 0
    elif part is slice_face.corner_bottom_left:
        # print("slice_face.corner_bottom_left")
        #   |      ^
        #   |---   |
        #    -->
        if it_left_to_right:
            inv = on_left_to_right > 0
        else:
            inv = on_left_to_top < 0
    else:
        #      |   ^
        #   ---|   |
        #    -->
        if it_left_to_right:
            inv = on_left_to_right > 0
        else:
            inv = on_left_to_top > 0
    return alg, inv


def _handle_slice_on_corner_adjusted_face(slice_face: Face,
                                          it_left_to_right: bool,
                                          on_left_to_right: float,
                                          on_left_to_top: float,
                                          part: Corner) -> Tuple[Alg, bool]:
    """
    The face where the part slice was dragged
    Rotate the face the is adjusted to the corner (the adjusted is selected according to direction)

    :param it_left_to_right: the significant movement is left to right on_left_to_right>on_left_to_top
    :param on_left_to_right: the movement in left to right direction
    :param on_left_to_top: the movement in left to top direction
    :param part: the part where mouse was dragged
    :param slice_face:
    :return:
    """

    edge: Edge
    if part is slice_face.corner_top_right:

        edge = slice_face.edge_top if it_left_to_right else slice_face.edge_right

    elif part is slice_face.corner_top_left:

        edge = slice_face.edge_top if it_left_to_right else slice_face.edge_left

    elif part is slice_face.corner_bottom_left:

        edge = slice_face.edge_bottom if it_left_to_right else slice_face.edge_left

    else:  # bottom right
        edge = slice_face.edge_bottom if it_left_to_right else slice_face.edge_right

    # todo: the caller process edged again, can be optimized
    return _handle_slice_on_edge_adjusted_face(slice_face,
                                               edge,
                                               on_left_to_right,
                                               on_left_to_top)


def _play(window: AbstractWindow, alg: Alg):
    op = window.app.op

    op.play(alg)
    # why I need that
    if not op.animation_enabled:
        window.update_gui_elements()


def _handle_selected_slice(window: AbstractWindow, slice_face: PartEdge, inv: bool):
    def __play(alg: Alg):

        if inv:
            alg = alg.prime

        # print(f"{alg=}")

        op = window.app.op

        op.play(alg)
        # why I need that
        if not op.animation_enabled:
            window.update_gui_elements()

    if slice_face:
        _slice: PartSlice = slice_face.parent
        part: Part = _slice.parent
        face: Face = slice_face.face
        face_name: FaceName = face.name

        # print(f"@@@@@@@@@@@@@@@@@ {slice_face} {part} @ {slice_face.face} {type(part)}")
        # print(f"@@@@@@@@@@@@@@@@@ {str(_slice)}")

        # is it a corner ?
        if isinstance(part, Corner):
            # print("Is corner")
            face_alg = Algs.of_face(face_name)
            __play(face_alg)

        if isinstance(part, Edge):

            # print("Is Edge")

            assert isinstance(_slice, EdgeWing)

            slice_alg: SliceAlg | None = None
            neg_slice_index = False
            if face_name in [FaceName.F, FaceName.B]:

                if face.is_bottom_or_top(part):
                    slice_alg = Algs.M  # we want over L
                    neg_slice_index = face_name == FaceName.B  # but r start at right, ltr is from left
                else:
                    slice_alg = Algs.E  # we want over D
                    neg_slice_index = False
            elif face_name in [FaceName.R, FaceName.L]:

                if face.is_bottom_or_top(part):
                    slice_alg = Algs.S  # we want over F
                    neg_slice_index = face_name == FaceName.L
                else:
                    slice_alg = Algs.E  # we want over D
                    neg_slice_index = False
            elif face_name in [FaceName.U, FaceName.D]:

                if face.is_bottom_or_top(part):
                    slice_alg = Algs.M  # we want over L
                    neg_slice_index = True
                else:
                    slice_alg = Algs.S  # we want over F
                    neg_slice_index = face_name == FaceName.D

            if slice_alg:

                index = _slice.index
                index = part.get_ltr_index_from_slice_index(face, index)

                if neg_slice_index:
                    index = face.inv(index)

                slice_alg = slice_alg[index + 1]  # index start from 1

                __play(slice_alg)


def _slice_on_edge_alg(part: Edge, face: Face, index: int, on_center=False) -> Alg:
    """

    :param part:
    :param face:
    :param index:
    :param on_center: actually we are coming from center, so slice is always ltr, no need to convert
    :return:
    """
    face_name: FaceName = face.name

    slice_alg: SliceAlg
    neg_slice_index: bool
    inv: bool = False
    if face_name in [FaceName.F, FaceName.B]:

        if face.is_bottom_or_top(part):
            slice_alg = Algs.M  # we want over L
            neg_slice_index = face_name == FaceName.B  # but r start at right, ltr is from left
            inv = face_name == FaceName.F
        else:
            slice_alg = Algs.E  # we want over D
            neg_slice_index = False
    elif face_name in [FaceName.R, FaceName.L]:

        if face.is_bottom_or_top(part):
            slice_alg = Algs.S  # we want over F
            neg_slice_index = face_name == FaceName.L
            inv = face_name == FaceName.R  # over F, so left-top is F prime
        else:
            slice_alg = Algs.E  # we want over D
            neg_slice_index = False
    elif face_name in [FaceName.U, FaceName.D]:

        if face.is_bottom_or_top(part):
            slice_alg = Algs.M  # we want over L
            neg_slice_index = False
        else:
            slice_alg = Algs.S  # we want over F
            neg_slice_index = face_name == FaceName.D
            inv = face_name == FaceName.D

    else:
        raise InternalSWError

    if not on_center:
        index = part.get_ltr_index_from_slice_index(face, index)

    if neg_slice_index:
        index = face.inv(index)

    slice_alg = slice_alg[index + 1]  # index start from 1

    if inv:
        return slice_alg.prime
    else:
        return slice_alg


def _slice_on_part_edge_alg(part_edge: PartEdge) -> Alg:
    _slice: PartSlice = part_edge.parent

    assert isinstance(_slice, EdgeWing)

    part: Edge = _slice.parent

    return _slice_on_edge_alg(part, part_edge.face, _slice.index)


def _screen_to_model(vs, window, x, y) -> np.ndarray:
    # almost as in
    # https://stackoverflow.com/questions/57495078/trying-to-get-3d-point-from-2d-click-on-screen-with-opengl
    # print(f"on mouse press: {x} {y}")
    x = float(x)
    y = window.height - float(y)
    # The following could work if we were not initially scaling to zoom on
    # the bed
    # if self.orthographic:
    #    return (x - self.width / 2, y - self.height / 2, 0)
    pmat = (gl.GLdouble * 16)()
    mvmat = (gl.GLdouble * 16)()
    # mvmat = self.get_modelview_mat(local_transform)
    viewport = (gl.GLint * 4)()
    px = gl.GLdouble()
    py = gl.GLdouble()
    pz = gl.GLdouble()
    vs = vs
    vs.prepare_objects_view()
    # 0, 0, width, height
    gl.glGetIntegerv(gl.GL_VIEWPORT, viewport)
    # print(f"{[f for f in viewport]}")
    gl.glGetDoublev(gl.GL_PROJECTION_MATRIX, pmat)
    gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX, mvmat)
    real_y = viewport[3] - y  # mouse is up down, gl is down up
    d = (gl.GLfloat * 1)()  # why ?
    gl.glReadPixels(int(x), int(real_y), 1, 1, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, d)
    # print(f"{[ f for f in d ]=}")
    # the z coordinate
    depth = d[0]
    gl.gluUnProject(x, real_y, depth, mvmat, pmat, viewport, px, py, pz)
    # print(f"{px.value=}, {py.value=}, {pz.value=}")
    vs.restore_objects_view()

    return np.array([px.value, py.value, pz.value])


def _get_selected_slice(vs, window, x, y) -> Tuple[PartEdge, np.ndarray, np.ndarray] | None:
    p = _screen_to_model(vs, window, x, y)

    return window.viewer.find_facet(p[0], p[1], p[2])
