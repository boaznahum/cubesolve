from collections.abc import Collection
from typing import Hashable, Tuple, Callable, Iterable

import colorama  # type: ignore
import numpy as np
import pyglet  # type: ignore
import pyglet.gl as gl  # type: ignore
import pyglet.gl.glu as glu  # type: ignore
from numpy import ndarray
from pyglet.gl import *  # type: ignore
from pyglet.graphics import Batch  # type: ignore

from app_state import AppState
from model.cube import Cube
from model.cube_face import Face
from model.elements import Part, FaceName, PartEdge
from model.elements import PartSlice
# noinspection PyMethodMayBeStatic


from ._cell import _CELL_SIZE
from ._faceboard import _FACE_SIZE, _FaceBoard
from ._board import _Board

_parts: dict[Hashable, int] = {}


def _part_id(p: Part) -> str:
    p_id = p.colors_id_by_color

    _id = _parts.get(p_id)

    if not _id:
        _id = len(_parts) + 1
        _parts[p_id] = _id

    return chr(ord("A") + _id - 1)


def _plot_face(b: _Board, f: Callable[[], Face], left_bottom: list[float],  # 3d
               left_right_direction: list[int],  # 3d
               left_top_direction: list[int],  # 3d
               orthogonal_direction: list[int]
               ):
    """

    :param b:
    :param f:
    :param left_bottom: in units of faces
    :param left_right_direction:
    :param left_top_direction:
    :return:
    """
    """
     0,0 | 0,1 | 0,2
     ---------------
     1,0 | 1,1 | 1,2
     ---------------
     2,0 | 2,1 | 2,2
    """

    fy0 = 0  # 480 - 100
    fx0 = 0  # 10
    fz0 = 0

    f0: ndarray = np.array([fx0, fy0, fz0], dtype=float).reshape(3, 1)
    # left_bottom is length=1 vector, we convert it to face size in pixels
    fs = np.array(left_bottom, dtype=float).reshape(3, 1) * _FACE_SIZE * _CELL_SIZE

    f0 = f0 + fs
    _left_right_d: ndarray = np.array(left_right_direction, dtype=float).reshape(3, 1)
    _left_top_d: ndarray = np.array(left_top_direction, dtype=float).reshape(3, 1)

    _ortho: ndarray = np.array(orthogonal_direction, dtype=float).reshape((3,))

    fb: _FaceBoard = b.create_face(f, f0, _left_right_d, _left_top_d, _ortho)

    fb.draw_init()


class GCubeViewer:
    __slots__ = ["_batch", "_cube", "_board", "_test",
                 "_hidden_objects", "_vs"]

    def __init__(self, batch: Batch, cube: Cube, vs: AppState) -> None:
        super().__init__()
        self._cube = cube
        self._batch = batch
        self._vs = vs

        #        self._test = pyglet.shapes.Line(0, 0, 20, 20, width=10, color=(255, 255, 255), batch=batch)

        self._board: _Board = _Board(self._batch, vs)

        self._init_gui()

    def update(self):
        """
        Called on any cue change to re-construct graphic elements
        :return:
        """
        self._board.update()

    def draw(self):
        """
        Draw the graphic elements that were update in :upate
        :return:
        """
        self._board.draw()

    def reset(self):
        """
        Called on cube resize
        :return:
        """
        self._board.reset()
        self._init_gui()

    def _init_gui(self):
        b = self._board
        cube = self._cube

        """
             Face coordinates

                    0  1  2
                0:     U
                1:  L  F  R
                2:     D
                3:     B

         """

        # we pass a supplier to Face and not a face, because might reset itself

        # debug with # s.alpha_x=-0.30000000000000004 s.alpha_y=-0.5 s.alpha_z=0

        _plot_face(b, lambda: cube.up, [0, 1, 1], [1, 0, 0], [0, 0, -1], [0, 1, 0])

        _plot_face(b, lambda: cube.left, [-0, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])
        if "L" in self._vs.draw_shadows:
            # -0.75 from it x location, so we can see it in isometric view
            _plot_face(b, lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])

        _plot_face(b, lambda: cube.front, [0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1])

        _plot_face(b, lambda: cube.right, [1, 0, 1], [0, 0, -1], [0, 1, 0], [1, 0, 0])

        _plot_face(b, lambda: cube.back, [1, 0, -0], [-1, 0, 0], [0, 1, 0], [0, 0, -1])
        if "B" in self._vs.draw_shadows:
            # -2 far away so we can see it
            _plot_face(b, lambda: cube.back, [1, 0, -2], [-1, 0, 0], [0, 1, 0], [0, 0, -1])

        _plot_face(b, lambda: cube.down, [0, -0, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])
        if "D" in self._vs.draw_shadows:
            # -05 below so we see it
            _plot_face(b, lambda: cube.down, [0, -0.5, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])

        self._board.finish_faces()

    def _get_face(self, name: FaceName) -> _FaceBoard:
        for f in self._board.faces:
            if f.cube_face.name == name:
                return f

        assert False

    def _get_faces(self, name: FaceName) -> Iterable[_FaceBoard]:

        for f in self._board.faces:
            if f.cube_face.name == name:
                yield f

    def _get_face_gui_objects(self, f: _FaceBoard) -> Iterable[int]:

        lists: set[int] = set()

        this_face_objects = f.gui_objects()
        lists.update(this_face_objects)

        this_cube_face: Face = f.cube_face

        cube_face_adjusts: Iterable[Face] = this_cube_face.adjusted_faces()

        for adjust in cube_face_adjusts:
            adjust_board: _FaceBoard = self._get_face(adjust.name)
            for p in adjust.parts:
                if p.on_face(this_cube_face):
                    p_lists = adjust_board.get_part_gui_object(p)
                    lists.update(p_lists)

        return lists

    def _get_faces_gui_objects(self, fs: Iterable[_FaceBoard]) -> Iterable[int]:

        lists: set[int] = set()

        for f in fs:
            lists.update(self._get_face_gui_objects(f))

        return lists

    def unhidden_all(self):
        self._board.unhidden_all()

    def get_slices_movable_gui_objects(self, face_name_rotate_axis: FaceName,
                                       cube_parts: Collection[PartSlice],
                                       hide=True) -> Tuple[ndarray, ndarray, Iterable[int]]:

        face_name: FaceName = face_name_rotate_axis

        right: _FaceBoard = self._get_face(face_name)
        left: _FaceBoard = self._get_face(self._cube.face(face_name).opposite.name)

        right_center: ndarray = right.get_center()
        # because left,back and down have more than one gui faces
        left_center: ndarray = left.get_center()

        objects: set[int] = set()

        objects.update(self._board.get_all_gui_elements(cube_parts))

        if hide:
            self._board.set_hidden(objects)

        return right_center, left_center, objects

    def find_facet(self, x: float, y: float, z: float) -> PartEdge | None:
        return self._board.find_facet(x, y, z)
