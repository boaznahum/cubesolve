from typing import Tuple

from cube.domain.algs import Alg, Algs
from cube.domain.geometric.geometry_types import FaceOrthogonalEdgesInfo
from cube.domain.model import Color, Edge, EdgeWing, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.model._part import EdgeName
from cube.domain.solver.direct.lbl import _common
from cube.domain.solver.direct.lbl._common import mark_slice_and_v_mark_if_solved
from cube.domain.tracker import FacesTrackerHolder
from cube.domain.tracker.PartSliceTracker import EdgeWingTracker, PartSliceTracker
from cube.domain.tracker.trackers import FaceTracker
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider
from cube.domain.solver.solver import SmallStepSolveState


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

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "_LBLNxNEdges")
        self._logger.set_level(_LBLNxNEdges.D_LEVEL)

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
        cube = self.cube
        assert white is cube.down


        with self._logger.tab(f"Solving edges on face {target_face_t} row {face_row}"):

            self.cmn.bring_face_front_preserve_down(target_face_t.face)

            # from now target face is on front
            # only now we can assign
            target_face = target_face_t.face

            edge_info: FaceOrthogonalEdgesInfo = cube.sized_layout.get_orthogonal_index_by_distance_from_face(
                target_face,
                l1_white_tracker.face, face_row
                )


            assert edge_info.edge_one is cube.front.edge_left
            assert edge_info.edge_two is cube.front.edge_right

            self.debug(
                lambda: lambda: f"Working on edges {edge_info.wing_one.parent_name_index__position} {edge_info.wing_two.parent_name_index__position}")

            with self._logger.tab("🟰🟰🟰🟰🟰🟰🟰🟰🟰 PATCH !!!!!!!!!!!!!!!!!!!!!!!!"):
                self._solve_single_edge_wing_on_face_try_two_sides(l1_white_tracker, target_face, edge_info, face_row)

    def _solve_single_edge_wing_on_face_try_two_sides(self, l1_white_tracker: FaceTracker, target_face: Face,
                                                      edge_info: FaceOrthogonalEdgesInfo, face_row: int) -> None:
        """PATCH PATCH PATCH try to solve one wing both sides."""
        cube = self.cube

        assert target_face is cube.front

        target_edge_wing = edge_info.wing_one

        if mark_slice_and_v_mark_if_solved(target_edge_wing):
            self.debug(lambda: f"EdgWing {target_edge_wing} already solved")
        else:

            faces_colors = [ f.color for f in target_edge_wing.faces() ]

            # we need to trace it we start to move the cube around
            # we cannot truck it becuase it might moved up becuas eit is a source
            required_color_unordered: PartColorsID = target_edge_wing.position_id

            required_indexes = [target_edge_wing.index, cube.inv(target_edge_wing.index)]

            source_wings: list[EdgeWing] = [*self.cqr.find_all_slice_in_edges(cube.edges,
                                                                              lambda s:
                                                                              not _common.is_slice_marked_solve(s) and  # dont touch solved slices !!!
                                                                              s.index in required_indexes and s.colors_id == required_color_unordered)]

            assert source_wings  # at least one

            solved: SmallStepSolveState = SmallStepSolveState.NOT_SOLVED

            with PartSliceTracker.with_trackers(source_wings) as sts:

                with self._logger.tab(f"Working on single wing {target_edge_wing.parent_name_index_colors_position} ,"
                           f" two faes {faces_colors}"
                           f"sources: {[t.slice.parent_name_index_colors_position for t in sts]}"):

                    assert target_edge_wing.parent.name is EdgeName.FL

                    fc: Color
                    i: int
                    is_fl: bool = True  # Initialize before loop
                    for i, fc in enumerate(faces_colors):

                        with self._logger.tab(lambda: f"Working on face {fc} for wing {target_edge_wing.parent_name_index_colors_position}"):

                            with self._logger.tab(
                                    lambda: f"Working on all sources  {[t.slice.parent_name_index_colors_position for t in sts]}"):

                                st: EdgeWingTracker
                                for st in sts:

                                    the_target_face = cube.color_2_face(fc)

                                    self.cmn.bring_face_front_preserve_down(the_target_face)

                                    # it was moved
                                    the_target_face = cube.color_2_face(fc)

                                    # we track is colors
                                    is_fl = i == 0
                                    if is_fl:
                                        the_wing = cube.front.edge_left.get_slice(edge_info.index_on_edge_one)
                                    else:
                                        the_wing = cube.front.edge_right.get_slice(edge_info.index_on_edge_two)

                                    with self._logger.tab(f"patch: Working on {the_target_face} target {the_wing.parent_name_index_colors_position} source wing {st.slice.parent_name_index_colors}"):


                                        solved = self._solve_one_side_edge_one_source(l1_white_tracker,
                                                                                      the_target_face,
                                                                                      st,
                                                                                      face_row, the_wing)

                                        if solved.is_solved:
                                            break
                                if solved.is_solved:
                                    break

    def _solve_one_side_edge_one_source(self,
                             l1_white_tracker: FaceTracker,
                             target_face: Face,
                             source_wing_t: EdgeWingTracker,
                             face_row: int, # for now for debug only
                             target_edge_wing: EdgeWing,
                                        ) -> SmallStepSolveState:

        """
        Assume face is onthe front
        wing is left or right

        :param l1_white_tracker:
        :param target_face:
        :param source_wing_t:
        :param face_row:
        :param target_edge:
        :param index_on_target_edge:
        :return:
        """

        debug = self.debug

        required_color_ordered = self._get_slice_required_ordered_color(target_face, target_edge_wing)

        with self._logger.tab(
                f"Working on edge {target_edge_wing.parent_name_index_colors_position}"):



            # the colors keys of the wing starting from the target face

            with self.ann.annotate(
                    h1=lambda: f"Fixing edge wing {target_edge_wing.parent_name_and_index} -> {required_color_ordered} source:{source_wing_t.slice.parent_name_index_colors_position}",):

                status = self._solve_edge_win_one_source(
                    l1_white_tracker,
                    source_wing_t,
                    target_face,
                    face_row,
                    target_edge_wing
                )

                self.debug(lambda: f"❓❓❓Solving all source_slices: {source_wing_t.slice.parent_name_index_colors_position} status: {status}")
                if mark_slice_and_v_mark_if_solved(target_edge_wing):
                    debug(lambda: f"✅✅✅✅ EdgWing {target_edge_wing.parent_name_index_colors} solved")

                return status

    def _solve_edge_win_one_source(self, l1_white_tracker: FaceTracker,
                                   source_slice_t: EdgeWingTracker,
                                   target_face: Face,
                                   face_row: int,  # for now for debug only
                                   target_edge_wing: EdgeWing,  # redundant - you have the index
                                   ) -> SmallStepSolveState:

        # this and the above should be one method

        cube = self.cube
        assert target_face is cube.front
        assert target_edge_wing.parent in [target_face.edge_left, target_face.edge_right]

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


        def print_solved_till_now(title: str) -> None:

            with self._logger.tab(lambda  : title + " Solved edges"):
                for i in range(face_row + 1):
                    with self._logger.tab(lambda: f"Row {i}"):
                        for edge in _common.get_edge_row_pieces(cube, l1_white_tracker, i):
                            if edge.match_faces:
                                self.debug(lambda : edge.parent_name_index_colors)


        st = source_slice_t

        print_solved_till_now(f"Before solving {target_edge_wing.parent_name_index_colors}")
        status = self._solve_edge_wing_by_source(target_face, target_edge_wing, st)
        print_solved_till_now(f"After solving ({status}) {target_edge_wing.parent_name_index_colors}")

        return status

    def _solve_edge_wing_by_source(self, target_face: Face,
                                   _target_edge_wing: EdgeWing,
                                   source_edge_wing_t: EdgeWingTracker) -> SmallStepSolveState:

        # if we reach here it is not solved

        untracked_source_wing = source_edge_wing_t.slice
        untracked_target_edge_wing = _target_edge_wing  # target wing is by location not by color, no need to track

        with self._logger.tab(lambda: f"Working with source wing  {untracked_source_wing}"):

            untracked_source_edge: Edge = untracked_source_wing.parent
            target_face_color = target_face.color

            self.debug(
                f"Found source EdgeWing for target {untracked_source_wing.parent_name_index_colors} : {untracked_source_wing} / {untracked_source_wing.index}")

            self.debug(lambda: f"on faces {untracked_source_wing.faces()} {untracked_source_edge.name}")

            # From here source may move !!!
            cube = self.cube
            if not untracked_source_wing.on_face(cube.up):

                with self._logger.tab(lambda: f"‼️‼️Trying to bring  {untracked_source_wing.parent_name_and_index} to to top"):

                    self._bring_source_wing_to_top(target_face, source_edge_wing_t)

                    # still same face
                    assert target_face.color == target_face_color

                    # we should get rid of it
                    untracked_source_wing = source_edge_wing_t.slice
                    untracked_source_edge = untracked_source_wing.parent

                    assert untracked_source_wing.on_face(cube.up)



            self.debug(lambda: f"💚💚 Source Wing is now on up {cube.up} {untracked_source_wing.parent_name_index_colors_position}")

            #Now it need to be also on front
            if not untracked_source_wing.on_face(cube.front):

                with self._logger.tab(lambda: f"‼️‼️Trying to bring  {untracked_source_wing.parent_name_and_index} to to front"):

                    for _ in range(3):
                        self.op.play(Algs.U)
                        untracked_source_wing = source_edge_wing_t.slice
                        if untracked_source_wing.on_face(cube.front):
                            break

                    untracked_source_wing = source_edge_wing_t.slice
                    assert untracked_source_wing.on_face(cube.front)
                    untracked_source_edge = untracked_source_wing.parent

            self.debug(lambda: f"💚💚 Source Wing is now on front {cube.front} {untracked_source_wing.parent_name_index_colors_position}")


            # now check if we can use it ?

            # if the coloron top is not our color then itmust be us

            if untracked_source_wing.get_face_edge(cube.up).color != target_face.color:
                assert target_face.color == untracked_source_wing.get_other_face_edge(cube.up).color

                self.debug(lambda: f"💚💚💚 Wing {untracked_source_wing}  match target color {target_face_color}")

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

    def _bring_source_wing_to_top(self, target_face: Face, source_edge_wing_t: EdgeWingTracker) -> None:

        target_face_color = target_face.color

        with FacesTrackerHolder(self) as th:

            self.cmn.bring_edge_to_front_right_or_left_preserve_down(source_edge_wing_t.slice.parent)

            # yes the source is the target
            self._do_right_or_left_edge_to_edge_communicator(source_edge_wing_t.slice, None)

            self.cmn.bring_face_front_preserve_down(th.get_face_by_color(target_face_color))

            assert th.get_face_by_color(target_face_color) is self.cube.front


    def _do_right_or_left_edge_to_edge_communicator(self,
                                                    target_wing: EdgeWing,
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

        source_wing = source_wing_edge.get_slice(source_wing_index)

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


            with self.annotate(h2=f"Bringing {source_wing.parent_name_index_colors} to {target_wing.parent_name_and_index}"):
                # U R U' [2]M' U R' U' [2]M
                self.op.play(alg)

            return True

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
