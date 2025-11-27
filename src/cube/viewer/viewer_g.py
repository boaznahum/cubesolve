from collections.abc import Collection
from typing import Tuple, Iterable

import colorama  # type: ignore
import pyglet  # type: ignore
import pyglet.gl as gl  # type: ignore
from numpy import ndarray
from pyglet.gl import *  # type: ignore
from pyglet.graphics import Batch  # type: ignore

from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.model.cube_face import Face
from cube.model import FaceName, PartSlice, PartEdge
# noinspection PyMethodMayBeStatic
from cube.utils import prof
from ._board import _Board
from ._faceboard import _FaceBoard
from .. import config
from ..gui.protocols.renderer import Renderer


# todo: delete ?
#  _parts: dict[Hashable, int] = {}


class GCubeViewer:
    __slots__ = ["_batch", "_cube", "_board", "_test",
                 "_hidden_objects", "_vs", "_renderer"]

    def __init__(
        self,
        batch: Batch,
        cube: Cube,
        vs: ApplicationAndViewState,
        renderer: Renderer | None = None,
    ) -> None:
        super().__init__()
        self._cube = cube
        self._batch = batch
        self._vs = vs
        self._renderer = renderer

        #        self._test = pyglet.shapes.Line(0, 0, 20, 20, width=10, color=(255, 255, 255), batch=batch)

        self._board: _Board = _Board(cube, self._batch, vs, renderer)

        self.reset()

    @property
    def renderer(self) -> Renderer | None:
        """Get the renderer instance."""
        return self._renderer

    def reset(self):
        """
        Called on cube resize
        :return:
        """
        self._board.reset()

    def cleanup(self):
        """
        Release resources upon exit
        :return:
        """
        self._board.cleanup()

    def update(self):
        """
        Called on any cue change to re-construct graphic elements
        :return:
        """
        with prof.w_prof("GUI update", config.VIEWER_TRACE_DRAW_UPDATE):
            self._board.update()

    def draw(self):
        """
        Draw the graphic elements that were update in :upate
        :return:
        """
        with prof.w_prof("GUI draw", config.VIEWER_TRACE_DRAW_UPDATE):
            self._board.draw()

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

        objects.update(self._board.get_all_movable_gui_elements(cube_parts))

        if hide:
            self._board.set_hidden(objects)

        return right_center, left_center, objects

    def find_facet(self, x: float, y: float, z: float) -> Tuple[PartEdge, ndarray, ndarray] | None:

        with prof.w_prof("Locate facet", config.PROF_VIEWER_SEARCH_FACET):
            return self._board.find_facet(x, y, z)
