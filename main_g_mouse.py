#
#
#  Handles rotating with the mouse
#
#
import math
from typing import Tuple, Any

import numpy as np
from numpy import ndarray
from pyglet.window import key, mouse  # type: ignore
from pyglet import gl  # type: ignore

import config
from algs import algs
from algs.algs import Alg, Algs
from app_exceptions import InternalSWError
from app_state import AppState
from cube_operator import Operator
from main_g_animation import AbstractWindow
from main_g_app import AbstractApp
from model.cube_boy import FaceName
from model.cube_face import Face
from model.elements import PartEdge, PartSlice, Part, Corner, Edge, EdgeSlice, Center, CenterSlice
from viewer.viewer_g import GCubeViewer


def on_mouse_drag(win: AbstractWindow, x, y, dx, dy, buttons, modifiers):

    if not modifiers & (key.MOD_SHIFT | key.MOD_CTRL):  # this is persevered for clik slicing

        if config.INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM:
            if bool(buttons & mouse.RIGHT) == bool(config.INPUT_MOUSE_MODEL_ROTATE_BY_DRAG_RIGHT_BOTTOM):
                _handle_modle_view_rotate_by_drag(win, dx, dy)
            else:
                _handle_face_slice_rotate_by_drag(win, x, y, dx, dy)


def _handle_modle_view_rotate_by_drag(win, dx, dy):
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


_HADNLING_ALT_MOUSE = False


def _handle_face_slice_rotate_by_drag(window: AbstractWindow, x, y, dx, dy):
    global _HADNLING_ALT_MOUSE

    if _HADNLING_ALT_MOUSE:
        return

    app: AbstractApp = window.app

    selected: tuple[PartEdge, ndarray, Any] | None = _get_selected_slice(app.vs, window, x, y)

    if not selected:
        return

    # print(f"{selected}")

    slice_face = selected[0]
    left_to_right = selected[1]
    left_to_top = selected[2]

    p0 = _screen_to_model(app.vs, window, x, y)  # todo we already in selected !!!
    p1 = _screen_to_model(app.vs, window, x + dx, y + dy)
    d_vector: ndarray = p1 - p0

    on_left_to_right = d_vector.dot(left_to_right)
    on_left_to_top = d_vector.dot(left_to_top)

    part_slice: PartSlice = slice_face.parent
    part: Part = part_slice.parent

    print(f"{type(part)=}, {on_left_to_right=}, {on_left_to_top=}")

    it_left_to_right = abs(on_left_to_right) > abs(on_left_to_top)

    _HADNLING_ALT_MOUSE = True
    try:
        face = slice_face.face
        face_name = face.name

        alg: Alg | None = None
        inv = False
        if isinstance(part, Corner):
            # print("Is corner")
            alg = Algs.of_face(face_name)

            if part is face.corner_top_right:
                #   ----|  ^
                #       |  |
                #    -->
                if it_left_to_right:
                    inv = on_left_to_right < 0
                else:
                    inv = on_left_to_top > 0
            elif part is face.corner_top_left:
                #   |----  ^
                #   |      |
                #    -->
                if it_left_to_right:
                    inv = on_left_to_right < 0
                else:
                    inv = on_left_to_top < 0
            elif part is face.corner_bottom_left:
                # print("face.corner_bottom_left")
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

        elif isinstance(part, Edge):

            print(f"Is Edge !!!!")

            face_alg = Algs.of_face(face_name)

            if part is face.edge_right:
                if it_left_to_right:  # slicing
                    alg = _slice_on_part_edge_alg(slice_face)
                    inv = on_left_to_right < 0  # D is left to right
                else:
                    alg = face_alg
                    inv = on_left_to_top > 0

            elif part is face.edge_left:
                if it_left_to_right:  # slicing
                    alg = _slice_on_part_edge_alg(slice_face)
                    inv = on_left_to_right < 0  # D is left to right
                else:
                    alg = face_alg
                    inv = on_left_to_top < 0

            elif part is face.edge_top:
                if not it_left_to_right:  # slicing
                    alg = _slice_on_part_edge_alg(slice_face)
                    inv = on_left_to_top < 0  # R is left to top
                else:
                    alg = face_alg
                    inv = on_left_to_right < 0
            elif part is face.edge_bottom:
                if not it_left_to_right:  # slicing
                    alg = _slice_on_part_edge_alg(slice_face)
                    inv = on_left_to_top < 0  # R is left to top
                else:
                    alg = face_alg
                    inv = on_left_to_right > 0
            else:
                raise InternalSWError

        elif isinstance(part_slice, CenterSlice):
            c_index: tuple[int, int] = part_slice.index
            xi = c_index[1]
            yi = c_index[0]

            if it_left_to_right:
                alg = _slice_on_edge_alg(face.edge_right, face, yi)
                inv = on_left_to_right < 0
            else:
                alg = _slice_on_edge_alg(face.edge_top, face, xi)
                inv = on_left_to_top < 0

        else:
            raise InternalSWError

        if alg:
            if inv:
                alg = alg.inv()
            _play(window, alg)

    finally:
        _HADNLING_ALT_MOUSE = False


def on_mouse_press(window: AbstractWindow, vs: AppState, op: Operator, viewer: GCubeViewer, x, y, modifiers):
    if modifiers & (key.MOD_SHIFT | key.MOD_CTRL):

        selected: tuple[PartEdge, ndarray, Any] | None = _get_selected_slice(vs, window, x, y)

        if selected:
            _handle_selected_slice(window, selected[0], modifiers & key.MOD_CTRL)


def _play(window: AbstractWindow, alg: Alg):
    op = window.app.op

    op.op(alg)
    # why I need that
    if not op.animation_enabled:
        window.update_gui_elements()


def _handle_selected_slice(window: AbstractWindow, slice_face: PartEdge, inv: bool):
    def _play(alg: Alg):

        if inv:
            alg = alg.prime

        # print(f"{alg=}")

        op = window.app.op

        op.op(alg)
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
            _play(face_alg)

        if isinstance(part, Edge):

            # print("Is Edge")

            assert isinstance(_slice, EdgeSlice)

            slice_alg: algs.SliceAlg | None = None
            neg_slice_index = False
            if face_name in [FaceName.F, FaceName.B]:

                if face.is_bottom_or_top(part):
                    slice_alg = Algs.M  # we want over R
                    neg_slice_index = face_name == FaceName.F  # but r start at right, ltr is from left
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
                    slice_alg = Algs.M  # we want over R
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

                _play(slice_alg)


def _slice_on_edge_alg(part: Edge, face: Face, index: int) -> Alg:
    face_name: FaceName = face.name

    slice_alg: algs.SliceAlg
    neg_slice_index: bool
    inv: bool
    if face_name in [FaceName.F, FaceName.B]:

        if face.is_bottom_or_top(part):
            slice_alg = Algs.M  # we want over R
            neg_slice_index = face_name == FaceName.F  # but r start at right, ltr is from left
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
            slice_alg = Algs.M  # we want over R
            neg_slice_index = True
        else:
            slice_alg = Algs.S  # we want over F
            neg_slice_index = face_name == FaceName.D

    else:
        raise InternalSWError

    index = part.get_ltr_index_from_slice_index(face, index)

    if neg_slice_index:
        index = face.inv(index)

    slice_alg = slice_alg[index + 1]  # index start from 1

    return slice_alg


def _slice_on_part_edge_alg(part_edge: PartEdge) -> Alg:
    _slice: PartSlice = part_edge.parent

    assert isinstance(_slice, EdgeSlice)

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
