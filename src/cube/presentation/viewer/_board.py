from collections import defaultdict
from collections.abc import (
    Collection,
    Iterable,
    Mapping,
    MutableSequence,
    Sequence,
    Set,
)
from typing import Callable, Tuple

import numpy as np
from numpy import ndarray

from cube.application.state import ApplicationAndViewState
from cube.domain.model import PartEdge, PartFixedID, PartSlice
from cube.domain.model.Cube import Cube
from cube.domain.model.cube_boy import FaceName
from cube.domain.model.Face import Face

from ..gui.protocols import Renderer
from ..gui.types import DisplayList
from ..gui.ViewSetup import ViewSetup
from ._cell import _Cell
from ._faceboard import _FACE_SIZE, _FaceBoard

#
#   update  --update----|           -*update--------|-------------------|
#                                                   <-----draw_init-----|
from .TextureData import TextureData

##########################################################################
# Sequence diagram
#
# Viewer              Board                       _Face                        _Cell
#  init     -->        init
#                        empty cells list ?
#   >---------|
#   <reset <--|
#
#   (non public call)
#   reset ---reset------|          -*reset----------|  -----*release_resources    |
#                                                          --*init----------------| basically empty collections
#
#                      _create_faces -*init-----------|
#                                                   empty cell list
#                                   * --draw_init---|   -----*create_objects------|
#                           collect cells from all faces


class _Board:
    """

        Face coordinates

           0  1  2
       0:     U
       1:  L  F  R
       2:     D
       3:     B
    """
    _cubie_texture: TextureData

    _y_faces = 4
    _x_faces = 3
    # in terms of faces
    _h_size: int = _FACE_SIZE * 3  # L F R
    _v_size: int = _FACE_SIZE * 4  # U F D B

    def __init__(
        self,
        cube: Cube,
        vs: ApplicationAndViewState,
        renderer: Renderer | None = None,
    ) -> None:
        super().__init__()
        self._hidden_objects: Set[int] = set()
        self._faces: MutableSequence[_FaceBoard] = []
        self._vs = vs
        self._renderer = renderer

        # why sequence, because we can have multiple back faces
        self._cells: Mapping[PartFixedID, MutableSequence[_Cell]] = dict()
        self._cube: Cube = cube

        texture_map: list[tuple[int, int]] = [(0, 0), (0, 1), (1, 1), (1, 0)]

        # Load texture using renderer abstraction
        self._cubie_texture = TextureData.load("cubie.bmp", texture_map, self.renderer)

    @property
    def renderer(self) -> Renderer:
        """Get the renderer instance.

        Raises:
            RuntimeError: If renderer is not configured.
        """
        if self._renderer is None:
            raise RuntimeError("Renderer is required but not configured. Use BackendRegistry.create_renderer()")
        return self._renderer

    def reset(self):
        for f in self._faces:
            f.release_resources()

        self._faces.clear()

        self._create_faces()

        self.update()

    def update(self):

        # we error after cube reset, and we don't want to complicate the call to viewer
        if self._front is not self._cube.front:  # same cube as before
            self.reset()
        else:
            # start = time.time_ns()
            # try:
            for face in self._faces:
                face.update()

    # finally:
    #     print(f"Update took {(time.time_ns() - start) / (10 ** 9)}")

    def draw(self) -> None:
        # for face in self._faces:
        #     face.draw()

        lists: set[int] = set()

        for f in self._faces:
            f.get_all_gui_elements(lists)

        hidden: Set[int] = self.get_hidden()

        lists -= hidden

        self._prepare_view_state()

        renderer = self.renderer
        # Use renderer abstraction
        display_lists = [DisplayList(ll) for ll in lists]
        renderer.display_lists.call_lists(display_lists)

        self._restore_view_state()

    def cleanup(self):
        """
        Release resources upon exit
        :return:
        """
        self._cubie_texture.cleanup()

    def _create_faces(self):
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

        self._create_face(lambda: cube.up, [0, 1, 1], [1, 0, 0], [0, 0, -1], [0, 1, 0])

        self._create_face(lambda: cube.left, [-0, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])
        if self._vs.get_draw_shadows_mode(FaceName.L):
            # -0.75 from it x location, so we can see it in isometric view
            self._create_face(lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])

        self._create_face(lambda: cube.front, [0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1])
        self._front = cube.front

        self._create_face(lambda: cube.right, [1, 0, 1], [0, 0, -1], [0, 1, 0], [1, 0, 0])

        self._create_face(lambda: cube.back, [1, 0, -0], [-1, 0, 0], [0, 1, 0], [0, 0, -1])
        if self._vs.get_draw_shadows_mode(FaceName.B):
            # -2 far away so we can see it
            self._create_face(lambda: cube.back, [1, 0, -2], [-1, 0, 0], [0, 1, 0], [0, 0, -1])

        self._create_face(lambda: cube.down, [0, -0, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])
        if self._vs.get_draw_shadows_mode(FaceName.D):
            # -05 below so we see it
            self._create_face(lambda: cube.down, [0, -0.5, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])

        self.finish_faces()

    def _create_face(self, f: Callable[[], Face], left_bottom: list[float],  # 3d
                     left_right_direction: list[int],  # 3d
                     left_top_direction: list[int],  # 3d
                     orthogonal_direction: list[int]
                     ):
        """

        :param self:
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
        cell_size = self._vs.config.cell_size
        fs = np.array(left_bottom, dtype=float).reshape(3, 1) * _FACE_SIZE * cell_size

        f0 = f0 + fs
        _left_right_d: ndarray = np.array(left_right_direction, dtype=float).reshape(3, 1)
        _left_top_d: ndarray = np.array(left_top_direction, dtype=float).reshape(3, 1)

        _ortho: ndarray = np.array(orthogonal_direction, dtype=float).reshape((3,))

        fb: _FaceBoard = self.create_face(f, f0, _left_right_d, _left_top_d, _ortho)

        fb.prepare_gui_geometry()

        return fb

    @property
    def h_size(self) -> int:
        return _Board._h_size

    @property
    def v_size(self) -> int:
        return _Board._v_size

    def create_face(self, cube_face: Callable[[], Face],
                    f0: ndarray,
                    left_right_direction: ndarray,
                    left_top_direction: ndarray,
                    ortho_direction: ndarray):
        f = _FaceBoard(self, cube_face, f0, left_right_direction, left_top_direction, ortho_direction)
        self._faces.append(f)
        return f

    def finish_faces(self) -> None:

        cells: dict[PartFixedID, list[_Cell]] = defaultdict(list)

        for fb in self._faces:

            f: Face = fb.cube_face
            for p in f.parts:
                _id = p.fixed_id
                cell: _Cell = fb.get_cell(_id)
                cells[_id].append(cell)

        self._cells = cells

    def get_cells(self, _id: PartFixedID) -> Sequence[_Cell]:
        """
        PArt can appear more than none due to multiple faces
        :param _id:
        :return:
        """
        return self._cells[_id]

    def _prepare_view_state(self) -> None:

        vs: ApplicationAndViewState = self.vs
        ViewSetup.prepare_objects_view(vs, self.renderer)

    def _restore_view_state(self) -> None:

        ViewSetup.restore_objects_view(self.renderer)

    @property
    def alpha_x(self):
        return self._vs.alpha_x

    @property
    def alpha_y(self):
        return self._vs.alpha_y

    @property
    def alpha_z(self):
        return self._vs.alpha_z

    @property
    def vs(self):
        return self._vs

    @property
    def faces(self):
        return self._faces

    def set_hidden(self, lists: Iterable[int]):
        self._hidden_objects = set(lists)

    def get_hidden(self) -> Set[int]:
        return self._hidden_objects

    def unhidden_all(self):
        self._hidden_objects = set()

    def get_all_movable_gui_elements(self, for_parts: Collection[PartSlice]) -> Set[int]:

        lists: set[int] = set()

        # need optimization !!!
        c: _Cell
        for cs in self._cells.values():
            for c in cs:
                for s in for_parts:
                    lists.update(c.gui_slice_movable_gui_objects(s))

        return lists

    def find_facet(self, x: float, y: float, z: float) -> Tuple[PartEdge, ndarray, ndarray] | None:
        # print(x, y, z)

        """

        :param x:
        :param y:
        :param z:
        :return:  found part and on face left-right and left-top vectors
        """

        f: _FaceBoard

        # for f in self._faces:
        #     c: _Cell
        #     for c in f.cells:
        #         for e, r in c.facets.items():
        #             print(f"{e} {e.parent} {r}")

        for f in self._faces:

            c: _Cell
            # if f.cube_face.name == FaceName.F:
            #     for c in f.cells:
            #         for e, rg in c.facets.items():
            #             print(f"{e}, {type(e.parent)}, {rg.two_d_draw_rect}")

            for c in f.cells:

                if c.cell_geometry.in_box(x, y, z):
                    for e, rg in c.facets.items():

                        if rg.in_box(x, y, z):
                            return e, f.left_right_direction, f.left_top_direction

        return None

    @property
    def cubie_texture(self) -> TextureData:
        return self._cubie_texture
