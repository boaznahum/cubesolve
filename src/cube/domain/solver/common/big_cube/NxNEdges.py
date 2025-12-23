from collections import defaultdict
from typing import Tuple

from cube.domain.algs import Alg, Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color, Edge, EdgeWing, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.model.ModelHelper import ModelHelper
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.CommonOp import EdgeSliceTracker
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider
from cube.utils.OrderedSet import OrderedSet


class NxNEdges(SolverElement):
    work_on_b: bool = True

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider, advanced_edge_parity: bool) -> None:
        super().__init__(slv)
        self._advanced_edge_parity = advanced_edge_parity

    def debug(self, *args, level=3):
        if level <= NxNEdges.D_LEVEL:
            super().debug("NxX Edges:", args)


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

        if self._is_solved():
            return False

        with self.ann.annotate(h1="Big cube edges"):
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

        face = self.cube.front

        with self.ann.annotate(h2=lambda: f"Fixing {edge.name_n_faces}"):

            self.debug(f"Brining {edge} to front-right")
            self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
            edge = self.cube.front.edge_left

            # We can't do  it before  bringing to front because we don't know which edge will be on front
            if n_slices % 2:
                _slice = edge.get_slice(n_slices // 2)
                color_un_ordered = _slice.colors_id
                ordered_color = self._get_slice_ordered_color(face, _slice)
            else:
                ordered_color = self._find_max_of_color(face, edge)
                color_un_ordered = frozenset(ordered_color)

            # Override the above
            def _h2():
                return f"/Fixing {edge.name_n_faces} " \
                       f"{ModelHelper.color_id_to_name(ordered_color)}"

            with self.ann.annotate(h2=_h2):
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
        slices_to_fix = OrderedSet[int]()
        slices_to_slice = OrderedSet[int]()

        for i in range(0, n_slices):

            a_slice = edge.get_slice(i)

            a_slice_id = a_slice.colors_id

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
            search_in: list[Edge] = [self.cube.front.edge_right, *OrderedSet(self.cube.edges) - {edge}]
            edge_can_destroyed = self.cqr.find_edge(search_in, lambda e: not e.is3x3)
            assert edge_can_destroyed
            self.cmn.bring_edge_to_front_right_preserve_front_left(edge_can_destroyed)

        slices = [edge.get_slice(i) for i in slices_to_slice]
        ltrs = [edge.get_ltr_index_from_slice_index(face, i) for i in slices_to_slice]

        # Now fix

        self.debug(f"On same edge, going to slice {ltrs}")

        with self.ann.annotate((slices, AnnWhat.Moved),
                               (lambda: (edge.get_slice(inv(i)) for i in slices_to_slice),
                                AnnWhat.FixedPosition),
                               h2="Flip on same edge"
                               ):

            slice_alg = Algs.E[[ltr + 1 for ltr in ltrs]]

            self.op.play(slice_alg)  # move me to opposite E begin from D, slice begin with 1
            self.op.play(self.rf)
            # bring them back
            self.op.play(slice_alg.prime)  # move me to opposite E begin from D, slice begin with 1

        for i in slices_to_fix:
            assert self._get_slice_ordered_color(face, edge.get_slice(inv(i))) == ordered_color

    def _fix_all_from_other_edges(self, face: Face, edge: Edge, ordered_color: Tuple[Color, Color],
                                  color_un_ordered: PartColorsID):

        other_edges = OrderedSet(face.cube.edges) - {edge}
        assert len(other_edges) == 11

        while not edge.is3x3:

            # start from one on right - to optimize
            edge_right = face.edge_right
            _other_edges = [edge_right, *(other_edges - {edge_right})]
            source_slice = self.cqr.find_slice_in_edges(_other_edges,
                                                           lambda s: s.colors_id == color_un_ordered)

            assert source_slice

            self.debug(f"Found source slice {source_slice}")

            self.cmn.bring_edge_to_front_right_preserve_front_left(source_slice.parent)

            source_slice = self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered)
            assert source_slice

            while self._find_slice_in_edge_by_color_id(edge_right, color_un_ordered):
                # ok now do for all that color order match
                # is there one that can be sliced ?

                if not any(self._get_slice_ordered_color(face, s) == ordered_color for s in edge_right.all_slices):
                    self.op.play(self.rf)

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

            if source_slice.colors_id != color_un_ordered:
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

            if target_slice.colors_id == color_un_ordered:
                raise InternalSWError("Don't know how to handle")

        if not target_slices:
            return False

        self.debug(f"Going to slice, sources={source_slice_indices}, target={target_indices}")

        # now slice them all
        with self.ann.annotate((source_slices, AnnWhat.Moved), (target_slices, AnnWhat.FixedPosition)):

            slice_alg = Algs.E[[i + 1 for i in target_indices]]

            # for target_index in target_indices:
            #     # slice me
            self.op.play(slice_alg)  # slice begin with 1
            self.op.play(self.rf)
            # for target_index in target_indices:
            self.op.play(slice_alg.prime)

        for target_index in target_indices:
            assert self._get_slice_ordered_color(face, edge.get_slice(target_index)) == ordered_color

        return True

    def _do_last_edge_parity(self):

        assert self._left_to_fix == 1

        # self.op.toggle_animation_on()
        # still don't know how to handle
        cube = self.cube

        edge = self.cqr.find_edge(cube.edges, lambda e: not e.is3x3)
        assert edge

        self._do_edge_parity_on_edge(edge)

    def _do_edge_parity_on_edge(self, edge) -> None:

        cube = self.cube
        n_slices = cube.n_slices

        face = cube.front

        tracer: EdgeSliceTracker
        with self.cmn.track_e_slice(edge.get_slice(0)) as tracer:
            self.debug(f"Doing parity on {edge}", level=1)
            edge = self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
            assert edge is face.edge_left
            assert edge is cube.fl
            self.op.play(Algs.F)

            # not true on even, edge is OK
            # assert CubeQueries.find_edge(cube.edges, lambda e: not e.is3x3) is face.edge_top

            edge = tracer.the_slice_nl.parent
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

        slices_to_fix: list[EdgeWing] = []
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
            # slices are from [1 nn], so we need to add 1
            # actually, simple alg doesn't care if we fix i or inv(i), because on
            # Advance alg - I don't know, so I'm keeping the index matches R - for the advanced
            # last edge they come in pairs i<->inv(i)
            #
            plus_one = [ i + 1 for i in slices_indices_to_fix]

            if not self._advanced_edge_parity:
                self.debug(f"*** Doing parity on M {plus_one}", level=2)
                for _ in range(4):
                    self.op.play(Algs.M[plus_one].prime)
                    self.op.play(Algs.U * 2)
                self.op.play(Algs.M[plus_one].prime)
            else:
                # in case of R/L we need to add 1, because 1 is R, and slices begin with 2
                plus_one = [i + 1 for i in plus_one]

                self.debug(f"*** Doing parity on R {plus_one}", level=2)
                #  https://speedcubedb.com/a/6x6/6x6L2E
                # 3R' U2 3L F2 3L' F2 3R2 U2 3R U2 3R' U2 F2 3R2 F2

                # noinspection PyPep8Naming
                Rs = Algs.R[plus_one]
                # noinspection PyPep8Naming
                Ls = Algs.L[plus_one]

                # noinspection PyPep8Naming
                U = Algs.U
                # noinspection PyPep8Naming
                F = Algs.F

                alg = Rs.prime + U * 2 + Ls + F * 2 + Ls.prime + F * 2 + Rs * 2 + U * 2 + Rs + U * 2 + Rs.p + U * 2 + F * 2
                alg += Rs * 2 + F * 2

                self.op.play(alg)

    @staticmethod
    def _get_slice_ordered_color(f: Face, s: EdgeWing) -> Tuple[Color, Color]:
        """

        :param f:
        :param s:
        :return:  (on face color, on_other color)
        """

        return s.get_face_edge(f).color, s.get_other_face_edge(f).color

    @staticmethod
    def _find_slice_in_edge_by_color_id(edge: Edge, color_un_ordered: PartColorsID) -> EdgeWing | None:

        for i in range(edge.n_slices):
            s = edge.get_slice(i)
            if s.colors_id == color_un_ordered:
                return s

        return None

    @property
    def rf(self) -> Alg:
        return Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F

    def do_even_full_edge_parity_on_any_edge(self):
        assert self.cube.n_slices % 2 == 0

        self._do_edge_parity_on_edge(self.cube.front.edge_left)

    def _find_max_of_color(self, face, edge) -> Tuple[Color, Color]:
        c_max = None
        n_max = 0

        hist: dict[PartColorsID, int] = defaultdict(int)

        for i in range(0, self.cube.n_slices):

            c = edge.get_slice(i).colors_id

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
            if _slice.colors_id == c_max:

                c = edge.get_slice(i).colors_id

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
