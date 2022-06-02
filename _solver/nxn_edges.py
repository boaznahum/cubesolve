from collections.abc import Iterator, Sequence
from typing import Tuple, Callable, Collection

import algs
from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from algs import Algs
from app_exceptions import InternalSWError
from cube_boy import CubeLayout
from cube_face import Face
from cube_queries import CubeQueries, Pred
from elements import FaceName, Color, CenterSlice, Edge, PartColorsID, EdgeSlice


def use(_):
    pass


_status = None

FaceTracker = Callable[[], Face]


class FaceLoc:

    def __init__(self, color: Color, tracker: FaceTracker) -> None:
        super().__init__()
        self._tracker = tracker
        self._color = color

    @property
    def face(self):
        return self._tracker()

    @property
    def color(self):
        return self._color


class NxNEdges(SolverElement):
    work_on_b: bool = True

    D_LEVEL = 3

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    def debug(self, *args, level=3):
        if level <= NxNEdges.D_LEVEL:
            super().debug("NxX Edges:", args)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_solved(self):
        return all((e.is3x3 for e in self.cube.edges))

    def solved(self) -> bool:
        """

        :return: if all centers have unique colors, and it is a boy
        """

        return self._is_solved()

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        edge: Edge = next(self.cube.edges.__iter__())

        self._do_edge(edge)

    def _do_edge(self, edge: Edge):

        if edge.is3x3:
            self.debug(f"Edge {edge} is already solved")
        else:
            self.debug(f"Need to work on Edge {edge} ")

        # find needed color
        n_slices = self.cube.n_slices
        color_un_ordered: PartColorsID

        if n_slices % 2:
             color_un_ordered = edge.get_slice(n_slices // 2).colors_id_by_color
        else:
            # todo: Count max in edge
            color_un_ordered = edge.get_slice(0).colors_id_by_color

        self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)

        self._solve_on_front_left(color_un_ordered)

    def _solve_on_front_left(self, color_un_ordered: PartColorsID):
        """
        Edge is on front left, and we need to solve it without moving it
        :return:
        """

        # first we need to find the right color

        cube = self.cube
        edge: Edge = cube.front.edge_left
        n_slices = cube.n_slices
        _slice: EdgeSlice
        if n_slices % 2:
            _slice = edge.get_slice(n_slices // 2)
        else:
            _slice = self._find_slice_in_edge_by_color_id(edge, color_un_ordered)


        # ordered color
        c_front = _slice.get_face_edge(cube.front).color
        c_other = _slice.get_other_face_edge(cube.front).color

        # now start to work
        self.debug(f"Working on edge {edge} color {(c_front, c_other)}")



    def _find_slice_in_edge_by_color_id(self, edge, color_un_ordered) -> EdgeSlice:

        for i in range(edge.n_slices):
            s = edge.get_slice(i)
            if s.colors_id_by_color == color_un_ordered:
                return s

        assert False







