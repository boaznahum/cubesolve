from collections import defaultdict
from collections.abc import Set, MutableSequence, Sequence, Iterable, Collection
from typing import Callable

import numpy as np
from numpy import ndarray
from pyglet import gl  # type: ignore
from pyglet.graphics import Batch  # type: ignore

from app_state import AppState
from model.cube import Cube
from model.cube_face import Face
from model.elements import PartFixedID, SuperElement, PartSlice, PartEdge
from ._cell import _Cell, _CELL_SIZE
from ._faceboard import _FACE_SIZE, _FaceBoard


##########################################################################
# Sequence diagram  (wht a mess !!!!)
#
# Viewer              Board                       _Face                        _Cell
#  init     -->        init
#                        empty cells list ?
#   >---------|
#   <reset <--|
#
#   reset ---reset------|          -*reset----------|  -----*release_resources    |
#                                                          --*init----------------| basically empty collections
#
#                      _create_faces -*init-----------|
#                                                   empty cell list
#                                   * --draw_init---|   -----*create_objects------|
#                           collect cells from all faces

#
#   update  --update----|           -*update--------|-------------------|
#                                                   <-----draw_init-----|


class _Board:
    """

        Face coordinates

           0  1  2
       0:     U
       1:  L  F  R
       2:     D
       3:     B
    """

    _y_faces = 4
    _x_faces = 3
    # in terms of faces
    _h_size: int = _FACE_SIZE * 3  # L F R
    _v_size: int = _FACE_SIZE * 4  # U F D B

    def __init__(self, cube: Cube, batch: Batch, vs: AppState) -> None:
        super().__init__()
        self._hidden_objects: Set[int] = set()
        self.batch = batch
        self._faces: MutableSequence[_FaceBoard] = []
        self._vs = vs

        # why sequence, because we can have multiple back faces
        self._cells: dict[PartFixedID, MutableSequence[_Cell]] = dict()
        self._cube: Cube = cube

    def reset(self):
        for f in self._faces:
            f.release_resources()

        self._faces.clear()

        self._create_faces()

        self.update()

    def update(self):

        # start = time.time_ns()
        # try:
        for face in self._faces:
            face.update()

    # finally:
    #     print(f"Update took {(time.time_ns() - start) / (10 ** 9)}")

    def draw(self):
        # for face in self._faces:
        #     face.draw()

        lists: set[int] = set()

        for f in self._faces:
            f.get_all_gui_elements(lists)

        hidden: Set[int] = self.get_hidden()

        lists -= hidden

        n = len(lists)

        lists_array = (gl.GLint * n)()
        lists_array[:] = [*lists]

        self._prepare_view_state()

        # https://www.glprogramming.com/red/chapter07.html
        gl.glCallLists(n, gl.GL_INT, lists_array)

        # for ll in lists:
        #     gl.glCallList(ll)

        self._restore_view_state()

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
        if "L" in self._vs.draw_shadows:
            # -0.75 from it x location, so we can see it in isometric view
            self._create_face(lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])

        self._create_face(lambda: cube.front, [0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1])

        self._create_face(lambda: cube.right, [1, 0, 1], [0, 0, -1], [0, 1, 0], [1, 0, 0])

        self._create_face(lambda: cube.back, [1, 0, -0], [-1, 0, 0], [0, 1, 0], [0, 0, -1])
        if "B" in self._vs.draw_shadows:
            # -2 far away so we can see it
            self._create_face(lambda: cube.back, [1, 0, -2], [-1, 0, 0], [0, 1, 0], [0, 0, -1])

        self._create_face(lambda: cube.down, [0, -0, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0])
        if "D" in self._vs.draw_shadows:
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
        fs = np.array(left_bottom, dtype=float).reshape(3, 1) * _FACE_SIZE * _CELL_SIZE

        f0 = f0 + fs
        _left_right_d: ndarray = np.array(left_right_direction, dtype=float).reshape(3, 1)
        _left_top_d: ndarray = np.array(left_top_direction, dtype=float).reshape(3, 1)

        _ortho: ndarray = np.array(orthogonal_direction, dtype=float).reshape((3,))

        fb: _FaceBoard = self.create_face(f, f0, _left_right_d, _left_top_d, _ortho)

        fb.prepare_gui_geometry()

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
        f = _FaceBoard(self, cube_face, self.batch, f0, left_right_direction, left_top_direction, ortho_direction)
        self._faces.append(f)
        return f

    def finish_faces(self):

        cells: dict[PartFixedID:list[_Cell]] = defaultdict(list)

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

    def _prepare_view_state(self):

        vs: AppState = self.vs
        vs.prepare_objects_view()

    def _restore_view_state(self):

        vs: AppState = self.vs
        vs.restore_objects_view()

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

    # todo: to delete
    def get_all_cells_movable_gui_elements(self, element: SuperElement) -> Set[int]:

        lists: set[int] = set()

        # need to optimize !!!
        for s in element.slices:

            c: _Cell
            for cs in self._cells.values():
                for c in cs:
                    lists.update(c.gui_slice_movable_gui_objects(s))

        return lists

    def get_all_gui_elements(self, for_parts: Collection[PartSlice]) -> Set[int]:

        lists: set[int] = set()

        # need otpimization !!!
        c: _Cell
        for cs in self._cells.values():
            for c in cs:
                for s in for_parts:
                    lists.update(c.gui_slice_movable_gui_objects(s))

        return lists


    def find_facet(self, x: float, y: float, z: float) -> PartEdge | None:
        # print(x, y, z)

        f: _FaceBoard

        # for f in self._faces:
        #     c: _Cell
        #     for c in f.cells:
        #         for e, r in c.facets.items():
        #             print(f"{e} {e.parent} {r}")

        for f in self._faces:

            ortho_dir: ndarray = f.ortho_direction
            norm = np.linalg.norm(ortho_dir)
            ortho_dir /= norm

            ortho_dir *= 2

            c: _Cell
            for c in f.cells:
                for e, rg in c.facets.items():

                    r = rg.two_d_draw_rect

                    #: param bottom_quad:  [left_bottom, right_bottom, right_top, left_top]
                    # :param top_quad:  [left_bottom, right_bottom, right_top, left_top]

                    bottom_quad = [p - ortho_dir for p in r]
                    top_quad = [p + ortho_dir for p in r]

                    if self._in_box(x, y, z, bottom_quad, top_quad):
                        return e

        return None

    @staticmethod
    def _in_box(x, y, z, bottom_quad: Sequence[np.ndarray],
                top_quad: Sequence[np.ndarray]):
        """
        https://stackoverflow.com/questions/2752725/finding-whether-a-point-lies-inside-a-rectangle-or-not
        https://math.stackexchange.com/questions/1472049/check-if-a-point-is-inside-a-rectangular-shaped-area-3d
        :param x:
        :param y:
        :param z: # vertex = [left_bottom3, right_bottom3, right_top3, left_top3]
        :param bottom_quad:  [left_bottom, right_bottom, right_top, left_top]
        :param top_quad:  [left_bottom, right_bottom, right_top, left_top]
        :return:
        """

        # Assuming the rectangle is represented by three points A,B,C, with AB and BC perpendicula

        #    p6-------p7
        #   /         /
        #  /         /
        # p5 ------ p8
        #
        #
        #    p2-------p3
        #   /         /
        #  /         /
        # p1 ------ p4

        # Given p1,p2,p4,p5 vertices of your cuboid, and pv the point to test for intersection with the cuboid, compute:
        # i=p2−p1
        # j=p4−p1
        # k=p5−p1
        # v=pv−p1
        # then, if
        # 0<v⋅i<i⋅i
        # 0<v⋅j<j⋅j
        # 0<v⋅k<k⋅k

        p1 = bottom_quad[0]
        p2 = bottom_quad[3]
        p4 = bottom_quad[1]
        p5 = top_quad[0]

        i = p2 - p1
        j = p4 - p1
        k = p5 - p1
        v = np.array([x, y, z]) - p1

        dot = np.dot

        ii = dot(i, i)
        jj = dot(j, j)
        kk = dot(k, k)
        vi = dot(v, i)
        vj = dot(v, j)
        vk = dot(v, k)

        return 0 <= vi <= ii and 0 <= vj <= jj and 0 <= vk <= kk

        pass
