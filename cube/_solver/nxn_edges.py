from collections import defaultdict
from typing import Tuple

from cube._solver.base_solver import SolverElement, ISolver
from cube._solver.common_op import CommonOp, EdgeSliceTracker
from cube.algs import algs as algs
from cube.algs.algs import Algs
from cube.app_exceptions import InternalSWError
from cube.model.cube_face import Face
from cube.model.cube_queries import CubeQueries
from cube.model.elements import Color, Edge, PartColorsID, EdgeSlice
from cube.operator.op_annotation import AnnWhat


def use(_):
    pass


_status = None


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

    def solve(self) -> bool:
        """

        :return: True if edge parity was performed
        """

        self._do_first_11()

        if self._is_solved():
            return False

        assert self._left_to_fix == 1

        # even cube can have edge parity too
        self._do_last_edge_parity()

        self._do_first_11()

        assert self._is_solved()

        return True

    def _do_first_11(self):
        """

        :return:
        """

        # We must not try to solve the last one - it is parity - even in even cube
        while self._left_to_fix > 1:
            n_to_fix = self._left_to_fix
            # we need to search again and gain because solving move all edges
            # search first front-left to avoid rotation
            e = next(e for e in [self.cube.front.edge_left, *self.cube.front.edges, *self.cube.edges] if not e.is3x3)
            assert e
            self._do_edge(e)
            assert self._left_to_fix < n_to_fix

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

        # if self._left_to_fix < 2:
        #     self.debug(f"But I can't continue because I'm the last {edge} ")
        #     return False

        # find needed color
        n_slices = self.cube.n_slices
        color_un_ordered: PartColorsID

        self.debug(f"Brining {edge} to front-right")
        self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
        edge = self.cube.front.edge_left

        face = self.cube.front

        if n_slices % 2:
            _slice = edge.get_slice(n_slices // 2)
            color_un_ordered = _slice.colors_id_by_color
            ordered_color = self._get_slice_ordered_color(face, _slice)
        else:
            ordered_color = self._find_max_of_color(face, edge)
            color_un_ordered = frozenset(ordered_color)

        self._solve_on_front_left(color_un_ordered, ordered_color)

        self._report_done(f"Done {edge}")

        return True

    def _solve_on_front_left(self, color_un_ordered: PartColorsID, ordered_color: Tuple[Color, Color]):
        """
        Edge is on front left, and we need to solve it without moving it
        :return:
        """

        # first we need to find the right color

        cube = self.cube
        face = cube.front
        edge: Edge = face.edge_left

        # now start to work
        self.debug(f"Working on edge {edge} color {ordered_color}")

        # first fix all that match color on this edge
        self._fix_all_slices_on_edge(face, edge, ordered_color, color_un_ordered)

        # now search in other edges
        self._fix_all_from_other_edges(face, edge, ordered_color, color_un_ordered)

    def _fix_all_slices_on_edge(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                color_un_ordered: PartColorsID):

        n_slices = edge.n_slices

        inv = edge.inv

        edge_can_destroyed: Edge | None = None

        is_last = self._left_to_fix == 1

        assert not is_last

        # Why set, because sometimes we need to fix i nad inv(i), so when we reach inv(i) we will try to add
        # again inv(inv(i)) == i
        slices_to_fix: set[int] = set()
        slices_to_slice: set[int] = set()

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

            other_slice_i = inv(i)
            other_slice = edge.get_slice(other_slice_i)
            other_order = self._get_slice_ordered_color(face, other_slice)
            if other_order == ordered_color:
                raise InternalSWError("Don't know what to do")

            slices_to_fix.add(i)
            slices_to_slice.add(i)
            slices_to_slice.add(inv(i))

        if not slices_to_fix:
            return

        # bring an edge to help
        if not is_last and edge_can_destroyed is None:
            search_in: list[Edge] = [self.cube.front.edge_right, *set(self.cube.edges) - {edge}]
            edge_can_destroyed = CubeQueries.find_edge(search_in, lambda e: not e.is3x3)
            assert edge_can_destroyed
            self.cmn.bring_edge_to_front_right_preserve_front_left(edge_can_destroyed)

        slices = [edge.get_slice(i) for i in slices_to_slice]
        ltrs = [edge.get_ltr_index_from_slice_index(face, i) for i in slices_to_slice]

        # Now fix

        self.debug(f"On same edge, going to slice {ltrs}")

        with self.ann.annotate( (slices, AnnWhat.Moved)):

            slice_alg = Algs.E[[ltr + 1 for ltr in ltrs]]

            self.op.op(slice_alg)  # move me to opposite E begin from D, slice begin with 1
            self.op.op(self.rf)
            # bring them back
            self.op.op(slice_alg.prime)  # move me to opposite E begin from D, slice begin with 1

        for i in slices_to_fix:
            assert self._get_slice_ordered_color(face, edge.get_slice(inv(i))) == ordered_color

    def _fix_all_from_other_edges(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                  color_un_ordered: PartColorsID):

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

            while self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered):
                # ok now do for all that color order match
                # is there one that can be sliced ?

                if not any(self._get_slice_ordered_color(face, s) == ordered_color for s in edge_right.all_slices):
                    self.op.op(self.rf)

                self._fix_many_from_other_edges_same_order(face, edge, ordered_color, color_un_ordered)

    def _fix_many_from_other_edges_same_order(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                              color_un_ordered: PartColorsID):

        """
        Source edge is in front right

        Slice all slices that are opposite of required color
        :param face:
        :param edge:
        :param ordered_color:
        :param color_un_ordered:
        :return:
        """

        inv = edge.inv

        source_slice_indices = []
        source_slices = []
        target_slices = []
        target_indices = []

        edge_right = face.edge_right

        for source_index in range(edge.n_slices):

            source_slice = edge_right.get_slice(source_index)

            if source_slice.colors_id_by_color != color_un_ordered:
                continue  # skip this one

            if self._get_slice_ordered_color(face, source_slice) != ordered_color:
                continue  # we will handle it in next iteration

            source_ltr_index = edge_right.get_ltr_index_from_slice_index(face, source_index)

            # source nad target have the sme lrt
            target_index = edge.get_slice_index_from_ltr_index(face, source_ltr_index)

            target_index = inv(target_index)  # we want to bring to opposite location

            # if n slices=4, we can't handle both 1, 4, it will be handled in next iteration
            if inv(target_index) in target_indices:
                continue

            source_slices.append(source_slice)
            source_slice_indices.append(source_index)

            target_slice = edge.get_slice(target_index)

            target_slices.append(target_slice)
            target_indices.append(target_index)

            if target_slice.colors_id_by_color == color_un_ordered:
                raise InternalSWError("Don't know how to handle")

        if not target_slices:
            return False

        self.debug(f"Going to slice, sources={source_slice_indices}, target={target_indices}")

        # now slice them all
        with self.ann.annotate(([source_slices, target_slices], AnnWhat.Moved)):

            slice_alg = Algs.E[[i + 1 for i in target_indices]]

            # for target_index in target_indices:
            #     # slice me
            self.op.op(slice_alg)  # slice begin with 1
            self.op.op(self.rf)
            # for target_index in target_indices:
            self.op.op(slice_alg.prime)

        for target_index in target_indices:
            assert self._get_slice_ordered_color(face, edge.get_slice(target_index)) == ordered_color

        return True

    def _do_last_edge_parity(self):

        assert self._left_to_fix == 1

        # self.op.toggle_animation_on()
        # still don't know how to handle
        cube = self.cube

        edge = CubeQueries.find_edge(cube.edges, lambda e: not e.is3x3)
        assert edge

        self._do_edge_parity_on_edge(edge)

    def _do_edge_parity_on_edge(self, edge):

        cube = self.cube
        n_slices = cube.n_slices

        face = cube.front

        tracer: EdgeSliceTracker
        with self.cmn.track_e_slice(edge.get_slice(0)) as tracer:
            self.debug(f"Doing parity on {edge}", level=1)
            edge = self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
            assert edge is face.edge_left
            # todo: optimize it , use directly bring to up
            self.op.op(Algs.F)

            # not true on even, edge is OK
            # assert CubeQueries.find_edge(cube.edges, lambda e: not e.is3x3) is face.edge_top

            edge = tracer.the_slice.parent
            assert edge is face.edge_top
            edge = cube.front.edge_top

        if n_slices % 2:
            required_color = self._get_slice_ordered_color(face, edge.get_slice(n_slices // 2))
        else:
            # In even, we can have partial and complete parity in cas eof complete, we reach here from solver after
            # finding edge in 3x3 with partial we reach here from this solver so in first case we need to reverse all
            # slices in second case we have no idea which, so we pick the first one (that can later cause and OLL
            # parity when solving as 3x3)
            required_color = self._get_slice_ordered_color(face, edge.get_slice(0))
            required_color = required_color[::-1]

        slices_to_fix: list[EdgeSlice] = []
        slices_indices_to_fix: list[int] = []
        _all = True
        for i in range(n_slices // 2):

            s = edge.get_slice(i)
            color = self._get_slice_ordered_color(face, s)
            # print(f"{i} ,{required_color}, {color}")
            if color != required_color:
                slices_indices_to_fix.append(i)
                slices_to_fix.append(s)
            else:
                _all = False

        ann = "Fixing edge(OLL) Parity"
        if n_slices % 2 == 0 and _all:
            ann += "(Full even)"

        # self.op.toggle_animation_on(enable=True)
        with self.ann.annotate((slices_to_fix, AnnWhat.Moved), h1=ann):
            plus_one = [i + 1 for i in slices_indices_to_fix]
            for _ in range(4):
                self.debug(f"*** Doing parity on R {plus_one}", level=2)
                self.op.op(Algs.M[plus_one])
                self.op.op(Algs.U * 2)
            self.op.op(Algs.M[plus_one])

    @staticmethod
    def _get_slice_ordered_color(f: Face, s: EdgeSlice) -> Tuple[Color, Color]:
        """

        :param f:
        :param s:
        :return:  (on face color, on_other color)
        """

        return s.get_face_edge(f).color, s.get_other_face_edge(f).color

    @staticmethod
    def _find_slice_in_edge_by_color_id(edge: Edge, color_un_ordered: PartColorsID) -> EdgeSlice | None:

        for i in range(edge.n_slices):
            s = edge.get_slice(i)
            if s.colors_id_by_color == color_un_ordered:
                return s

        return None

    @property
    def rf(self) -> algs.Alg:
        return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F

    def do_edge_parity_on_any(self):
        assert self.cube.n_slices % 2 == 0

        self._do_edge_parity_on_edge(self.cube.front.edge_left)

    def _find_max_of_color(self, face, edge) -> Tuple[Color, Color]:
        c_max = None
        n_max = 0

        hist: dict[PartColorsID, int] = defaultdict(int)

        for i in range(0, self.cube.n_slices):

            c = edge.get_slice(i).colors_id_by_color

            hist[c] += 1

            if hist[c] > n_max:
                n_max = hist[c]
                c_max = c

        assert c_max

        n_c1 = 0
        n_c2 = 0
        c1 = None
        c2 = None

        for i in range(self.cube.n_slices):

            _slice = edge.get_slice(i)
            if _slice.colors_id_by_color == c_max:

                c = edge.get_slice(i).colors_id_by_color

                ordered = self._get_slice_ordered_color(face, _slice)

                if c == ordered:
                    n_c1 += 1
                    c1 = ordered
                else:
                    n_c2 += 1
                    c2 = ordered

        assert c1 or c2

        if n_c1 > n_c2:
            assert c1
            return c1
        else:
            assert c2
            return c2
