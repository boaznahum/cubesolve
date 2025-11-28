from collections.abc import MutableSequence, Iterable, Sequence
from typing import Callable, Tuple, TYPE_CHECKING

import numpy as np
from numpy import ndarray

from cube.model import Part, Corner, Edge, Center
from cube.model import PartFixedID
from cube.model.cube_face import Face
from ._cell import _Cell, _CELL_SIZE, _CORNER_SIZE

_FACE_SIZE = 3

if TYPE_CHECKING:
    from ._board import _Board


class _FaceBoard:
    """
     0,0 | 0,1 | 0,2
     ---------------
     1,0 | 1,1 | 1,2
     ---------------
     2,0 | 2,1 | 2,2
    """

    # face size in terms of cells
    # todo: delete
    _h_size: int = 1 * _FACE_SIZE
    _v_size: int = 1 * _FACE_SIZE

    def __init__(self,
                 board: "_Board",
                 cube_face_supplier: Callable[[], Face],
                 f0: np.ndarray, left_right_direction: ndarray, left_top_direction: ndarray,
                 ortho_direction: ndarray
                 ) -> None:
        super().__init__()
        self._board: "_Board" = board
        self.cube_face_supplier = cube_face_supplier
        # self.flip_h = flip_h
        # self.flip_v = flip_v
        self.f0: np.ndarray = f0
        self.left_right_direction: ndarray = left_right_direction
        self.left_top_direction: ndarray = left_top_direction
        self._ortho_direction: ndarray = ortho_direction

        self._cells: dict[PartFixedID, _Cell] = {p.fixed_id: _Cell(self) for p in
                                                 self.cube_face_supplier().parts}


    def release_resources(self) -> None:

        """
        Release cells resources
        :return:
        """

        c: _Cell
        for c in self._cells.values():
            c.release_resources()

        self._cells = {p.fixed_id: _Cell(self) for p in
                                                 self.cube_face_supplier().parts}

    @property
    def cube_face(self) -> Face:
        return self.cube_face_supplier()

    @property
    def board(self) -> "_Board":
        """Get the parent board."""
        return self._board

    # noinspection PyUnusedLocal

    def prepare_gui_geometry(self) -> None:

        f: Face = self.cube_face

        def _create_cell(cy: int, cx: int, part: Part):

            left_bottom3, left_top3, right_bottom3, right_top3 = self._calc_cell_quad_coords(part, cx, cy)

            box: MutableSequence[np.ndarray] = [left_bottom3, right_bottom3, right_top3, left_top3]

            # why it is needed
            l_box = [x.reshape((3,)) for x in box]

            # # convert to gl,
            # # but this is waste of time, when calculating center and rotate axis, we again convert to ndarray
            # for i in range(len(l_box)):
            #     l_box[i] = [c_float(l_box[i][0]), c_float(l_box[i][1]), c_float(l_box[i][2])]


            self._cells[part.fixed_id].prepare_geometry(part, l_box)

        _create_cell(2, 0, f.corner_top_left)
        _create_cell(2, 1, f.edge_top)
        _create_cell(2, 2, f.corner_top_right)
        _create_cell(1, 0, f.edge_left)
        _create_cell(1, 1, f.center)
        _create_cell(1, 2, f.edge_right)
        _create_cell(0, 0, f.corner_bottom_left)
        _create_cell(0, 1, f.edge_bottom)
        _create_cell(0, 2, f.corner_bottom_right)

    def update(self) -> None:
        c: _Cell
        for c in self._cells.values():
            c.update_drawing()


    def _calc_cell_quad_coords(self, part: Part, cx, cy):

        face_size: float = _CELL_SIZE * 3.0

        max_corner_size = _CELL_SIZE  #  3x3 Cube
        min_corner_size: float = face_size * _CORNER_SIZE  # Very big NxN -> oo

        cube_size = part.cube.size

        #
        corner_size = min_corner_size + (max_corner_size-min_corner_size) * 3/cube_size

        center_size = face_size - 2 * corner_size

        cell_width: float
        cell_height: float

        x0: float
        y0: float

        if isinstance(part, Corner):
            # cx = 0 | 2
            # cy = 0 | 2
            x0 = cx / 2.0 * (corner_size + center_size)
            x1 = x0 + corner_size  # corner_size or face_size

            y0 = cy / 2.0 * (corner_size + center_size)
            y1 = y0 + corner_size  # edge_with or face_size
        elif isinstance(part, Edge):
            # cx, cy:
            #  0, 1 - left     x= 0, corner  y = corner, corner+center
            #  2, 1 - right    x= corner + center, corner + center + corner
            #  1, 0 - bottom   x = corner
            #  1, 2 - up
            match (cx, cy):
                case (0, 1):  # left
                    x0 = 0
                    x1 = x0 + corner_size
                    y0 = corner_size
                    y1 = y0 + center_size
                case (2, 1):  # right
                    x0 = face_size - corner_size
                    x1 = face_size
                    y0 = corner_size
                    y1 = y0 + center_size

                case (1, 0):  # bottom
                    x0 = corner_size
                    x1 = x0 + center_size
                    y0 = 0
                    y1 = y0 + corner_size

                case (1, 2):  # top
                    x0 = corner_size
                    x1 = x0 + center_size
                    y0 = face_size - corner_size
                    y1 = face_size

                case _:
                    assert False

        else:
            assert isinstance(part, Center)
            x0 = corner_size
            x1 = x0 + center_size

            y0 = corner_size
            y1 = y0 + center_size

        l_r_d = self.left_right_direction
        l_t_d = self.left_top_direction
        left_bottom3 = self.f0 + l_r_d * x0 + l_t_d * y0

        right_bottom3 = self.f0 + l_r_d * x1 + l_t_d * y0

        right_top3 = self.f0 + l_r_d * x1 + l_t_d * y1

        left_top3 = self.f0 + l_r_d * x0 + l_t_d * y1

        return left_bottom3, left_top3, right_bottom3, right_top3


    @property
    def cells(self) -> Iterable[_Cell]:
        return self._cells.values()


    @property
    def board(self):
        return self._board

    def gui_objects(self) -> Sequence[int]:
        lists: list[int] = []
        for c in self.cells:
            lists.extend(c.gui_movable_gui_objects())

        return lists

    def get_center(self) -> ndarray:

        face: Face = self.cube_face
        bl: ndarray = self._cells[face.corner_bottom_left.fixed_id].left_bottom_v3
        rt: ndarray = self._cells[face.corner_top_right.fixed_id].right_top_v3

        _bl = bl
        _rt = rt

        center = (_bl + _rt) / 2

        return center

    def center_and_gui_objects(self) -> Tuple[ndarray, Sequence[int]]:

        return self.get_center(), self.gui_objects()

    def get_part_gui_object(self, p: Part) -> Iterable[int]:
        return self._cells[p.fixed_id].gui_movable_gui_objects()

    def get_all_gui_elements(self, dest: set[int]):
        """
        Including hidden, for drawing
        :param dest
        :return:
        """
        for c in self.cells:
            c.get_all_gui_elements(dest)

    def get_cell(self, _id: PartFixedID) -> _Cell:
        return self._cells[_id]

    @property
    def ortho_direction(self) -> ndarray:
        return self._ortho_direction

