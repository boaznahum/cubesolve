from collections import defaultdict
from typing import Tuple

from cube.domain.algs import Alg, Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.geometry_types import FaceOrthogonalEdgesInfo
from cube.domain.model import Color, Edge, EdgeWing, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.model.ModelHelper import ModelHelper
from cube.domain.model._part import EdgeName
from cube.domain.solver.common.big_cube.NxNEdgesCommon import NxNEdgesCommon
from cube.domain.solver.direct.lbl import _common
from cube.domain.solver.direct.lbl._common import mark_slice_and_v_mark_if_solved
from cube.domain.tracker import FacesTrackerHolder
from cube.domain.tracker.PartSliceTracker import EdgeWingTracker, PartSliceTracker
from cube.domain.tracker.trackers import FaceTracker
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.CommonOp import EdgeSliceTracker
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider
from cube.domain.solver.solver import SmallStepSolveState
from cube.utils.OrderedSet import OrderedSet


class _LBLNxNEdges(SolverHelper):
    """
    Edge solver for NxN cubes using layer-by-layer approach.

    Coordinate Convention - row_distance_from_l1:
    =============================================
    In this class, `row_distance_from_l1` represents the distance from the L1 (white) face,
    NOT the row index in the face's LTR coordinate system.

    - row_distance_from_l1=0: The row/column closest to L1 (touching the shared edge)
    - row_distance_from_l1=1: The next row/column away from L1
    - row_distance_from_l1=n-1: The row/column furthest from L1

    This abstraction is orientation-independent. See cube_layout.py's
    get_orthogonal_index_by_distance_from_face() for full documentation with diagrams.
    """
    work_on_b: bool = True

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider, advanced_edge_parity: bool) -> None:
        super().__init__(slv)
        self._set_debug_prefix("LBL-Edges")
        self._logger.set_level(_LBLNxNEdges.D_LEVEL)
        self._advanced_edge_parity = advanced_edge_parity

        # claude: all used methods and their dependencies should be moved to
        self._edges_helper: NxNEdgesCommon = NxNEdgesCommon(self, False)

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

    def solve_single_center_face_row(
            self, l1_white_tracker: FaceTracker, target_face_t: FaceTracker, face_row: int
    ) -> None:
        """
        Solve edge slices on a single row of a face, starting from the L1 layer.

        This method solves the edge pieces on both sides (left and right edges) of
        a horizontal row on the target face. The row is specified by its distance
        from the L1 (white) face, not by its LTR row index.

        Args:
            l1_white_tracker: FaceTracker for L1 (white) face. Must currently be at Down.
            target_face_t: FaceTracker for the face whose edges we're solving.
            face_row: Distance from L1 face (0 = closest row to L1).
                See class docstring for full explanation.

        Example (5x5 cube, L1=Down, target=Front):
            row_distance_from_l1=0 → solves edges on row 4 (bottom row of Front)
            row_distance_from_l1=1 → solves edges on row 3
            row_distance_from_l1=2 → solves edges on row 2 (middle)
        """

        # see with _setup_l1
        white: Face = l1_white_tracker.face
        assert white is self.cube.down

        with self._logger.tab(f"Solving edges on face {target_face_t} row {face_row}"):

            self.cmn.bring_face_front_preserve_down(target_face_t.face)

            # from now target face is on front
            # only now we can assign
            target_face = target_face_t.face

            edge_info: FaceOrthogonalEdgesInfo = self.cube.sized_layout.get_orthogonal_index_by_distance_from_face(
                target_face,
                l1_white_tracker.face, face_row
                )

            self.debug(
                lambda: lambda: f"Working on edges {edge_info.edge_one.name}/{edge_info.index_on_edge_one} {edge_info.edge_two.name}/{edge_info.index_on_edge_two}")

            def patch() -> None:
                # PATCH PATCH PATCH try to solve onw wing both sides
                # preserve
                front_color = self.cube.front.color

                assert target_face is self.cube.front

                faces = []
                edge_wing = edge_info.edge_one.get_slice(edge_info.index_on_edge_one)
                for f in edge_wing.faces():
                    faces.append(f.color)

                the_wing = edge_info.edge_one.get_slice(edge_info.index_on_edge_one)

                the_colors = the_wing.colors_id

                self.debug(f"patch: "
                           f"Wing is {the_wing.parent_name_and_index_colors}")

                assert the_wing.parent.name is EdgeName.FL

                solved: SmallStepSolveState = SmallStepSolveState.NOT_SOLVED
                fc: Color
                for fc in faces:


                    the_target_face = self.cube.color_2_face(fc)

                    with self._logger.tab(f"patch: Working on {target_face}"):

                        self.cmn.bring_face_front_preserve_down(the_target_face)

                        the_target_face = self.cube.color_2_face(fc)

                        the_edge =  the_target_face.edge_left

                        the_wing = the_edge.get_slice(edge_info.index_on_edge_one)

                        #assert the_wing.colors_id == the_colors, f" {the_wing.colors_id} != {the_colors}"

                        solved = self._solve_one_side_edge(l1_white_tracker, the_target_face, face_row, the_wing.parent,
                                                  the_wing.index)

                        if solved.is_solved:
                            break


                #restore - we dont know what caller expect
                self.cmn.bring_face_front_preserve_down(self.cube.color_2_face(front_color))

                assert solved.is_solved


            if True:
                with self._logger.tab("🟰🟰🟰🟰🟰🟰🟰🟰🟰 PATCH !!!!!!!!!!!!!!!!!!!!!!!!"):
                    patch()
            else:

                self._solve_one_side_edge(l1_white_tracker, target_face, face_row, edge_info.edge_one, edge_info.index_on_edge_one)
                self._solve_one_side_edge(l1_white_tracker, target_face, face_row, edge_info.edge_two, edge_info.index_on_edge_two)


            pass

    def _solve_one_side_edge(self,
                             l1_white_tracker: FaceTracker,
                             target_face: Face,
                             face_row: int, # for now for debug only
                             target_edge: Edge,
                             index_on_target_edge) -> SmallStepSolveState:

        debug = self.debug

        target_edge_wing: EdgeWing = target_edge.get_slice(index_on_target_edge)

        required_color_ordered = self._get_slice_required_ordered_color(target_face, target_edge_wing)

        with self._logger.tab(
                f"Working on edge {target_face.get_edge_position(target_edge)} / {index_on_target_edge} wing {required_color_ordered}"):

            if mark_slice_and_v_mark_if_solved(target_edge_wing):
                debug(lambda: f"EdgWing {target_edge_wing} already solved")
                return SmallStepSolveState.WAS_SOLVED

            # the colors keys of the wing starting from the target face

            with self.ann.annotate(
                    h1=lambda: f"Fixing edge wing {target_edge_wing.parent_name_and_index} -> {required_color_ordered}"):

                # position_id gives us the face CENTER colors of the slot (where piece SHOULD go)
                required_color_unordered: PartColorsID = target_edge_wing.position_id

                required_indexes = [index_on_target_edge, self.cube.inv(index_on_target_edge)]

                source_slices: list[EdgeWing] = [*self.cqr.find_all_slice_in_edges(self.cube.edges,
                                                                                   lambda s:
                                                                                   #s is not target_edge_wing and  # don't select target as source
                                                                                   not _common.is_slice_solved(s) and  # dont touch solved slices !!!
                                                                                   s.index in required_indexes and s.colors_id == required_color_unordered)]

                debug(lambda: f"source_slices: {source_slices}")

                assert source_slices  # at least one

                status = self._solve_edge_win_all_source(
                    l1_white_tracker,
                    source_slices,
                    target_face,
                    face_row,
                    target_edge_wing
                )

                self.debug(lambda: f"❓❓❓Solving all source_slices: {source_slices} status: {status}")
                if mark_slice_and_v_mark_if_solved(target_edge_wing):
                    debug(lambda: f"✅✅✅✅ EdgWing {target_edge_wing.parent_name_and_index_colors} solved")

                return status

    def _solve_edge_win_all_source(self, l1_white_tracker,
                                   source_slices: list[EdgeWing],
                                   target_face: Face,
                                   face_row: int, # for now for debug only
                                   target_edge_wing: EdgeWing,  # redundant - you have the index
                                   ) -> SmallStepSolveState:
        """Try to solve the target edge wing using any of the source slices.

        Iterates through candidate source wings and attempts to solve the target
        using each one until successful or all sources exhausted.

        Args:
            source_slices: List of EdgeWing candidates that could solve target.
            target_face: The face we're solving edges for.
            target_edge: The edge containing the target wing.
            target_edge_wing: The specific wing to solve.
            index_on_target_edge: Slice index within the target edge.

        Returns:
            SOLVED if target was successfully solved, NOT_SOLVED otherwise.
        """

        def print_solved_till_now(title: str):

            with self._logger.tab(lambda  : title + " Solved edges"):
                for i in range(face_row + 1):
                    with self._logger.tab(lambda: f"Row {i}"):
                        for edge in _common.get_edge_row_pieces(self.cube, l1_white_tracker, i):
                            if edge.match_faces:
                                self.debug(lambda : edge.parent_name_and_index_colors)


        with self._logger.tab(lambda: f"Working on all sources  {[w.parent_name_and_index for w in source_slices]}"):

            with PartSliceTracker.with_trackers(source_slices) as sts:

                st: EdgeWingTracker
                for st in sts:

                    print_solved_till_now(f"Before solving {target_edge_wing.parent_name_and_index_colors}")
                    status = self._solve_edge_wing_by_source(target_face, target_edge_wing, st)
                    print_solved_till_now(f"After solving ({status}) {target_edge_wing.parent_name_and_index_colors}")

                    if status == SmallStepSolveState.SOLVED:
                        return SmallStepSolveState.SOLVED
                return SmallStepSolveState.NOT_SOLVED

    def _solve_edge_wing_by_source(self, target_face: Face,
                                   _target_edge_wing: EdgeWing,
                                   source_edge_wing_t: EdgeWingTracker) -> SmallStepSolveState:

        # if we reach here it is not solved

        untracked_source_wing = source_edge_wing_t.slice
        untracked_target_edge_wing = _target_edge_wing  # target wing is by location not by color, no need to track

        if True:
            with self._logger.tab(lambda: f"Working with source wing  {untracked_source_wing}"):

                untracked_source_edge: Edge = untracked_source_wing.parent
                target_face_color = target_face.color

                self.debug(
                    f"Found source EdgeWing for target {untracked_source_wing.parent_name_and_index_colors} : {untracked_source_wing} / {untracked_source_wing.index}")

                self.debug(lambda: f"on faces {untracked_source_wing.faces()} {untracked_source_edge.name}")

                # From here source may move !!!
                # boaz: need to optimzie start with the one thay best match on up at least
                # # simple case edge is on top
                cube = self.cube
                if not untracked_source_wing.on_face(cube.up):

                    #assert False, f"Source wing {source_edge_wing} is not on up"
                    with self._logger.tab(lambda: f"‼️‼️Trying to bring  {untracked_source_wing.parent_name_and_index} to to top"):

                        self._bring_source_wing_to_top(target_face, source_edge_wing_t)

                        # still same face
                        assert target_face.color == target_face_color

                        # we should get rid of it
                        untracked_source_wing = source_edge_wing_t.slice
                        untracked_source_edge = untracked_source_wing.parent

                        assert untracked_source_wing.on_face(cube.up)



                self.debug(lambda: f"💚💚 Wing {untracked_source_wing.parent_name_and_index_colors}  is on {cube.up} {untracked_source_edge.name}")

                #Now it need to be also on front
                if not untracked_source_wing.on_face(cube.front):

                    #assert False, f"Source wing {source_edge_wing} is not on up"
                    with self._logger.tab(lambda: f"‼️‼️Trying to bring  {untracked_source_wing.parent_name_and_index} to to front"):

                        for _ in range(3): ### calude: optimize it !!!!
                            self.op.play(Algs.U)
                            untracked_source_wing = source_edge_wing_t.slice
                            if untracked_source_wing.on_face(cube.front):
                                break

                        untracked_source_wing = source_edge_wing_t.slice
                        assert untracked_source_wing.on_face(cube.front)
                        untracked_source_edge = untracked_source_wing.parent

                self.debug(
                    lambda: f"💚💚 Wing {untracked_source_wing.parent_name_and_index_colors}  is on {cube.front} {untracked_source_edge.name}")


                # now check if we can use it ?

                # if the coloron top is not our color then itmust be us

                if untracked_source_wing.get_face_edge(cube.up).color != target_face.color:
                    assert target_face.color == untracked_source_wing.get_other_face_edge(cube.up).color

                    self.debug(lambda: f"💚💚💚 Wing {untracked_source_wing}  match target color {target_face_color}")

                    # from here it is collection of hard code assumption that we need to generalize

                    # bring edge to front
                    self.cmn.bring_edge_on_up_to_front(self, untracked_source_edge)

                    # you can no longer use it

                    # patch patch patch use cube sized layout to compute this
                    # it is different logic if it left


                    # soon it is going to moved

                    # this move target wing
                    moved = self._do_right_or_left_edge_to_edge_communicator(untracked_target_edge_wing,
                                                                             source_edge_wing_t.slice)

                    if moved:
                        self.debug(lambda: "💚💚💚💚 Source index and target match")

                        assert untracked_target_edge_wing.match_faces

                        self.debug(lambda: f"✅✅💚💚💚💚💚✅✅ Solved {untracked_target_edge_wing}")

                        return SmallStepSolveState.SOLVED


                    else:
                        self.debug(lambda: "❌❌ Source index and target don't match")

                    # from now, you cannot use untracked_source_wing
                else:
                    self.debug(
                        lambda: f"❌❌❌ Wing {untracked_source_wing}  doesnt match target color {target_face_color}")

        return SmallStepSolveState.NOT_SOLVED

    def _bring_source_wing_to_top(self, target_face: Face, source_edge_wing_t: EdgeWingTracker):

        target_face_color = target_face.color

        # claude we need to be able to create single FaceTracker that track face
        with FacesTrackerHolder(self) as th:


            self.cmn.bring_edge_to_front_right_or_left_preserve_down(source_edge_wing_t.slice.parent)

            # yes the source is the target
            self._do_right_or_left_edge_to_edge_communicator(source_edge_wing_t.slice, None)

            self.cmn.bring_face_front_preserve_down(th.get_face_by_color(target_face_color))

            assert th.get_face_by_color(target_face_color) is self.cube.front






    def _do_right_or_left_edge_to_edge_communicator(self,
                                                    target_wing:EdgeWing,
                                                    source_wing: EdgeWing | None) -> bool:

        cube = self.cube
        # current we only support front
        target_edge = target_wing.parent
        target_face = cube.front
        assert target_edge.on_face(target_face)

        face_row_index_on_target_edge = target_edge.get_face_ltr_index_from_edge_slice_index(target_face,
                                                                                             target_wing.index)

        assert target_edge in [cube.fl, cube.fr]

        is_target_right_edge = target_edge is cube.fr

        if is_target_right_edge:
            required_source_wing_face_column_index = cube.inv(face_row_index_on_target_edge)
        else:
            required_source_wing_face_column_index = face_row_index_on_target_edge

        source_wing_edge = cube.fu
        if source_wing is not None:
            assert source_wing.parent is source_wing_edge
            source_wing_index = source_wing.index
            face_column_on_source_edge = source_wing.parent.get_face_ltr_index_from_edge_slice_index(
                target_face, source_wing_index)
        else:
            face_column_on_source_edge = required_source_wing_face_column_index
            source_wing_index = source_wing_edge.get_edge_slice_index_from_face_ltr_index(target_face, face_column_on_source_edge)

        source_wing =  source_wing_edge.get_slice(source_wing_index)

        with self._logger.tab(
                    lambda: f"Trying communicator from wing {source_wing.parent_name_and_index} to wing {target_wing.parent_name_and_index}"):

            self.debug(lambda: f"required_source_wing_face_column_index: {required_source_wing_face_column_index}")
            self.debug(lambda: f"face_column_on_source_edge: {face_column_on_source_edge}")

            if required_source_wing_face_column_index != face_column_on_source_edge:
                self.debug(lambda: "❌❌ Source index and target don't match")
                assert source_wing is not None, "We calculate it it must be equal"
                return False  # can't perform

            alg_index = face_column_on_source_edge + 1  # one based
            alg: Alg
            if is_target_right_edge:

                # U R
                # U' [2]M'
                # U R'
                # U' [2]M

                alg = Algs.seq(Algs.U, Algs.R,
                               Algs.U.prime, Algs.M[alg_index].prime,
                               Algs.U, Algs.R.prime,
                               Algs.U.prime, Algs.M[alg_index]
                               )
            else:
                #  U' L'
                #  U [1]M'
                #  U' L
                #  U [1]M
                alg = Algs.seq(
                    Algs.U.prime , Algs.L.prime,
                    Algs.U , Algs.M[alg_index].prime,
                    Algs.U.prime , Algs.L,
                    Algs.U + Algs.M[alg_index]
                )


            with self.annotate(h2=f"Bringing {source_wing.parent_name_and_index_colors} to {target_wing.parent_name_and_index}"):
                # U R U' [2]M' U R' U' [2]M
                self.op.play(alg)

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
            self.debug(f"Edge {edge} is already solved", level=3)
            return False
        else:
            self.debug(f"Need to work on Edge {edge} ", level=3)

        # if self._left_to_fix < 2:
        #     self.debug( f"But I can't continue because I'm the last {edge} ", level=3)
        #     return False

        # find needed color
        n_slices = self.cube.n_slices
        color_un_ordered: PartColorsID

        face = self.cube.front

        with self.ann.annotate(h2=lambda: f"Fixing {edge.name_n_faces}"):

            self.debug(f"Brining {edge} to front-right", level=3)
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
        self.debug(f"Working on edge {edge} color {ordered_color}", level=3)

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
        ltrs = [edge.get_face_ltr_index_from_edge_slice_index(face, i) for i in slices_to_slice]

        # Now fix

        self.debug(f"On same edge, going to slice {ltrs}", level=3)

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

            self.debug(f"Found source slice {source_slice}", level=3)

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

            source_ltr_index = edge_right.get_face_ltr_index_from_edge_slice_index(face, source_index)

            # source nad target have the sme lrt
            target_index = edge.get_edge_slice_index_from_face_ltr_index(face, source_ltr_index)

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

        self.debug(f"Going to slice, sources={source_slice_indices}, target={target_indices}", level=3)

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
            plus_one = [i + 1 for i in slices_indices_to_fix]

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

    def _get_slice_required_ordered_color(self, f: Face, s: EdgeWing) -> Tuple[Color, Color]:
        """

        :param f:
        :param s:
        :return:  (on face color, on_other color)
        """

        return f.color, s.get_other_face(f).color

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

