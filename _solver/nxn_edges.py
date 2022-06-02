from collections.abc import Iterator, Sequence
from typing import Tuple, Callable, Collection, Set

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


class NxNEdges(SolverElement):
    work_on_b: bool = True

    D_LEVEL = 2

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

        first_11 = [*self.cube.edges]
        first_11.pop()

        n_did_work = 0
        while self._left_to_fix > 1:
            n_to_fix = sum(not e.is3x3 for e in first_11)
            self.debug(f"Main loop, {n_did_work} solved in prev, Still more to fix {n_to_fix}", level=1)
            n_did_work = 0
            for e in first_11:
                # because each do move all other edges
                if self._do_edge(e):
                    n_did_work += 1
                    # self.debug(f"Sub loop edge was done, Still more to fix {n_to_fix}", level=1)

        self.debug(f"After main loop, Still more to fix {self._left_to_fix}", level=1)

    def _report_done(self, s):
        n_to_fix = sum(not e.is3x3 for e in self.cube.edges)
        self.debug(f"{s}, Still more to fix {n_to_fix}", level=2)

    @property
    def _left_to_fix(self) -> int:
        n_to_fix = sum(not e.is3x3 for e in self.cube.edges)
        return n_to_fix

    def _do_edge(self, edge: Edge) -> bool:

        if edge.is3x3:
            self.debug(f"Edge {edge} is already solved")
            return False
        else:
            self.debug(f"Need to work on Edge {edge} ")

        if self._left_to_fix < 2:
            self.debug(f"But I can't continue because I'm the last {edge} ")
            return False


        # find needed color
        n_slices = self.cube.n_slices
        color_un_ordered: PartColorsID

        if n_slices % 2:
            color_un_ordered = edge.get_slice(n_slices // 2).colors_id_by_color
        else:
            # todo: Count max in edge
            color_un_ordered = edge.get_slice(0).colors_id_by_color

        self.debug(f"Brining {edge} to front-right")
        self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)

        self._solve_on_front_left(color_un_ordered)

        self._report_done(f"Done {edge}")

        return True

    def _solve_on_front_left(self, color_un_ordered: PartColorsID):
        """
        Edge is on front left, and we need to solve it without moving it
        :return:
        """

        # first we need to find the right color

        cube = self.cube
        face = cube.front
        edge: Edge = face.edge_left

        n_slices = cube.n_slices
        _slice: EdgeSlice
        if n_slices % 2:
            _slice = edge.get_slice(n_slices // 2)
        else:
            _slice = self._find_slice_in_edge_by_color_id(edge, color_un_ordered)

        # ordered color
        ordered_color = self._get_slice_ordered_color(face, _slice)

        # now start to work
        self.debug(f"Working on edge {edge} color {ordered_color}")
        inv = cube.inv

        # first fix all that match color on this edge
        self._fix_all_slices_on_edge(face, edge, ordered_color, color_un_ordered)

        # now search in other edges
        self._fix_all_from_other_edges(face, edge, ordered_color, color_un_ordered)

    def _fix_all_slices_on_edge(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                color_un_ordered: PartColorsID):

        n_slices = edge.n_slices

        inv = edge.inv

        edge_can_destroyed: Edge | None = None

        for i in range(0, n_slices):

            a_slice = edge.get_slice(i)

            a_slice_id = a_slice.colors_id_by_color

            if a_slice_id != color_un_ordered:
                continue

            ordered = self._get_slice_ordered_color(face, a_slice)
            if ordered == ordered_color:
                # done
                continue

            if n_slices % 2 and i == n_slices // 2:
                raise InternalSWError()

            # now need to fix

            other_slice_i = inv(i)
            other_slice = edge.get_slice(other_slice_i)
            other_order = self._get_slice_ordered_color(face, other_slice)
            if other_order == ordered_color:
                raise InternalSWError("Don't know what to do")

            i_ltr = edge.get_ltr_index_from_slice_index(face, i)
            other_ltr = edge.get_ltr_index_from_slice_index(face, other_slice_i)

            if edge_can_destroyed is None:
                search_in: set[Edge] = set(self.cube.edges) - {edge}
                edge_can_destroyed = CubeQueries.find_edge(search_in, lambda e: not e.is3x3)
                assert edge_can_destroyed
                self.cmn.bring_edge_to_front_right_preserve_front_left(edge_can_destroyed)

            self.op.op(Algs.E[i_ltr + 1])  # move me to opposite E begin from D, slice begin with 1
            self.op.op(Algs.E[other_ltr + 1])  # move other

            self.op.op(self.rf)

            # bring them back
            self.op.op(Algs.E[i_ltr + 1].prime)  # move me to opposite E begin from D, slice begin with 1
            self.op.op(Algs.E[other_ltr + 1].prime)  # move other

            assert self._get_slice_ordered_color(face, other_slice) == ordered_color

    def _fix_all_from_other_edges(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                  color_un_ordered: PartColorsID):

        n_slices = edge.n_slices

        inv = edge.inv

        other_edges = set(face.cube.edges) - {edge}
        assert len(other_edges) == 11

        while not edge.is3x3:

            # start from one on right - to optimize
            edge_right = face.edge_right
            _other_edges = [edge_right, *(other_edges - {edge_right})]
            source_slice = CubeQueries.find_slice_in_edges(_other_edges,
                                                           lambda s: s.colors_id_by_color == color_un_ordered)

            assert source_slice

            self.debug(f"Found source slice {source_slice}")

            self.cmn.bring_edge_to_front_right_preserve_front_left(source_slice.parent)

            source_slice = self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered)
            assert source_slice

            assert source_slice.parent is edge_right

            if self._get_slice_ordered_color(face, source_slice) != ordered_color:

                source_index: int = source_slice.index

                self.op.op(self.rf)

                # we can't search again , because it might that we have another one there !!!
                # but we know it was inverted
                source_slice = edge_right.get_slice(inv(source_index))
#                source_slice = self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered)
                assert source_slice

                source_ordered_color = self._get_slice_ordered_color(face, source_slice)
                if source_ordered_color != ordered_color:
                    print(f"Problem, on source slice {source_slice}, {source_slice.index}")
                    print(f"  ....  {source_slice.colors_id_by_color}")
                    print(f"  ....  on source {source_ordered_color}, required {ordered_color}")
                    print(f"  ....  on source {type(source_ordered_color)}, required {type(ordered_color)}")

                assert source_ordered_color == ordered_color

            source_index = source_slice.index

            source_ltr_index = edge_right.get_ltr_index_from_slice_index(face, source_index)

            # source nad target have the sme lrt
            taget_index = edge.get_slice_index_from_ltr_index(face, source_ltr_index)

            taget_index = inv(taget_index)  # we want to bring to opposite location

            target_slice = edge.get_slice(taget_index)

            if target_slice.colors_id_by_color == color_un_ordered:
                raise InternalSWError("Don't know how to handle")

            # slice me
            self.op.op(Algs.E[taget_index + 1])  # slice begin with 1
            self.op.op(self.rf)
            self.op.op(Algs.E[taget_index + 1].prime)

            assert self._get_slice_ordered_color(face, edge.get_slice(taget_index)) == ordered_color

            # need to optimize, should starrt from the one already

    def _get_slice_ordered_color(self, f: Face, s: EdgeSlice) -> Tuple[Color, Color]:
        """

        :param f:
        :param s:
        :return:  (on face color, on_other color)
        """

        return s.get_face_edge(f).color, s.get_other_face_edge(f).color

    def _find_slice_in_edge_by_color_id(self, edge: Edge, color_un_ordered: PartColorsID) -> EdgeSlice:

        for i in range(edge.n_slices):
            s = edge.get_slice(i)
            if s.colors_id_by_color == color_un_ordered:
                return s

        assert False

    @property
    def rf(self) -> algs.Alg:
        return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F
