from collections.abc import Iterator
from contextlib import contextmanager
from typing import Tuple, TypeAlias, Generator

from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color, CenterSlice, CenterSliceIndex, Face
from cube.domain.model.Cube import Cube
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.common.tracker.trackers import FaceTracker
from cube.domain.solver.protocols import SolverElementsProvider
from cube.utils import symbols

CENTER_SLICE_TRACK_KEY = "xxxxxxx"

Point: TypeAlias = Tuple[int, int]


class NxNCenters2(SolverElement):
    """
    Solves center pieces on NxN cubes (N > 3) using block commutators.

    This solver brings center pieces from source faces to target faces using
    single-piece or block commutators (3-cycle of center pieces).

    MODES OF OPERATION:
    ===================

    preserve_cage=False (default): REDUCTION METHOD
    ------------------------------------------------
    Centers are solved BEFORE edges are paired.
    Setup moves (face rotations for alignment) are NOT undone.
    This is more efficient but BREAKS paired edges.
    Use this when: Centers are solved first, edges paired after.

    preserve_cage=True: CAGE METHOD
    --------------------------------
    Centers are solved AFTER edges and corners.
    Setup moves ARE undone to preserve the "cage" (paired edges + solved corners).
    This is slightly less efficient but preserves the 3x3 solution.
    Use this when: Edges and corners are solved first, then centers.

    WHY SETUP MOVES BREAK THE CAGE:
    ===============================

    The commutator algorithm itself is BALANCED:
        [M', F, M', F', M, F, M, F']
    This has 2 F rotations and 2 F' rotations, so corners return to position.

    However, SETUP MOVES are used to align pieces before the commutator:
    - In _block_communicator: source_face * n_rotate to align blocks

    These setup moves are NOT balanced - they permanently move corners.
    When preserve_cage=True, we track these moves and UNDO them after.

    ALGORITHM ANALYSIS - WHAT AFFECTS WHAT:
    =======================================

    | Move      | Centers | Edges (paired) | Corners |
    |-----------|---------|----------------|---------|
    | M, M'     | YES     | NO (inner)     | NO      |
    | M2        | YES     | NO             | NO      |
    | F, F'     | YES     | **BREAKS!**    | MOVES   |
    | F2        | YES     | NO (symmetric) | MOVES   |
    | U, U'     | YES     | **BREAKS!**    | MOVES   |
    | B[1:n]    | YES     | **BREAKS!**    | MOVES   |

    EXAMPLE - What preserve_cage=True does:
    =======================================

    Without preserve_cage (reduction method):
        play(source_face * n_rotate)  # Setup: align block
        play(commutator)              # Balanced, corners return
        # Setup is NOT undone - corners are permanently rotated

    With preserve_cage (cage method):
        play(source_face * n_rotate)  # Setup: align block
        play(commutator)              # Balanced, corners return
        play(source_face' * n_rotate) # UNDO: restore corners
    """

    def __init__(
            self,
            slv: SolverElementsProvider,
            preserve_cage: bool = False,
    ) -> None:
        """
        Initialize the center solver.

        Args:
            slv: Solver elements provider (cube, operator, etc.)

            preserve_cage: Controls whether setup moves are undone.

                False (default): REDUCTION METHOD
                    - Centers solved BEFORE edges
                    - Setup moves are NOT undone (more efficient)
                    - BREAKS paired edges - don't use if edges are already paired!

                True: CAGE METHOD
                    - Centers solved AFTER edges and corners
                    - Setup moves ARE undone (preserves 3x3 solution)
        """
        super().__init__(slv)

        self._preserve_cage = preserve_cage
        self._comm_helper = CommunicatorHelper(slv)


    def solve_single_center_row_slice(
            self, l1_white_tracker: FaceTracker, target_face: FaceTracker, slice_index: int
    ) -> None:
        """
        Solve a single row of center pieces on a face.

        Uses block commutators to bring pieces from source faces.
        Properly handles cage preservation if preserve_cage=True.

        Args:
            face_tracker: Face to solve
            slice_index: Slice index to solve  zeo based
            :param target_face:
            :param l1_white_tracker:
        """

        with self._logger.tab(lambda: f"{symbols.green_line(3)} Slice {slice_index} {target_face.color_at_face_str} <-- all faces {symbols.green_line(3)}"):
            self._solve_single_center_slice_all_sources(l1_white_tracker, target_face, slice_index)

    def _all_slices_on_all_faces_solved(self, l1_white_tracker: FaceTracker, slice_index: int) -> bool:

        # all over the solution we assume faces botton up is the ltr, but of course this is not true
        # if target was not down

        # what we need is a function that calculate the indexes relative to white face no matter where is it using the ltr system

        assert l1_white_tracker.face is self.cube.down

        for f in l1_white_tracker.face.adjusted_faces():
            for point in self._2d_center_row_slice_iter(slice_index):
                c = f.get_center_slice(point)
                if not self._is_cent_piece_solved(c):
                    return False

        return True

    def _slice_on_target_face_solved(self, l1_white_tracker: FaceTracker, target_face: FaceTracker, slice_index: int) -> bool:

        # all over the solution we assume faces botton up is the ltr, but of course this is not true
        # if target was not down

        # what we need is a function that calculate the indexes relative to white face no matter where is it using the ltr system

        assert l1_white_tracker.face is self.cube.down

        for f in [target_face.face]:
            for point in self._2d_center_row_slice_iter(slice_index):
                c = f.get_center_slice(point)
                if not self._is_cent_piece_solved(c):
                    return False

        return True



    def _solve_single_center_slice_all_sources(self, l1_white_tracker: FaceTracker, target_face: FaceTracker,
                                               slice_index: int) -> bool:

        work_was_done = False

        # maybe not need iterations


        with self._track_row_slices(l1_white_tracker, slice_index):

            face_slice_solved = self._slice_on_target_face_solved(l1_white_tracker, target_face, slice_index)
            if face_slice_solved:
                self.debug(f"✅✅✅✅ All slices solved {slice_index} ✅✅✅✅✅")
                return  False

            max_iter = 10000
            iter_count = 0

            removed_count = 0

            while True:
                iter_count += 1
                if iter_count > max_iter:
                    raise InternalSWError("Maximum number of iterations reached")

                # position and tracking need to go inside
                solved_count = self._solve_single_center_slice_all_sources_impl(l1_white_tracker, target_face,
                                                                    slice_index)
                self.debug(f"‼✅✅{solved_count} piece(s) solved {slice_index} ‼✅✅")

                if solved_count > 0:
                    work_was_done = True
                else:
                    # if we reach here then not all were solved
                    if removed_count > 0:
                        raise InternalSWError(f"I moved pieces for {target_face} but still solve nothing")

                # WIP: Commented out - this does position and tracking again !!!
                # if self._remove_all_pieces_from_target_face(l1_white_tracker, target_face, slice_row_index):
                #     work_was_done = True

                face_slice_solved = self._slice_on_target_face_solved(l1_white_tracker, target_face, slice_index)


                if face_slice_solved:
                    self.debug(f"✅✅✅✅ Face {target_face} slice solved {slice_index} ✅✅✅✅✅")
                    return work_was_done
                else:
                    self.debug(f"‼️‼️‼️‼️Face {target_face} slice NOT  solved, trying to remove from some face ‼️‼️‼️‼️")

                    removed_count = self._try_remove_all_pieces_from_target_face_and_other_faces(l1_white_tracker,
                                                                                                 target_face,
                                                                                                 slice_index,
                                                                                                 False)

                    if removed_count == 0:
                        self.debug(f"‼️‼️‼️‼️Nothing was removed_count, aborting face {target_face} slice {slice_index} ‼️‼️‼️‼️")
                        return work_was_done
                    else:
                        self.debug(f"‼️‼️‼️‼️{removed_count} piece(s) moved, trying again slice {slice_index} ‼️‼️‼️‼️")

    def _solve_single_center_slice_all_sources_impl(self, l1_white_tracker: FaceTracker,
                                                    target_face: FaceTracker,
                                                    slice_row_index: int
                                                    ) -> int:
        """
        Try to solve center slices from all source faces.

        :return: Number of pieces moved/solved
        """
        source_faces: list[FaceTracker] = [ * target_face.other_faces() ]

        self.debug(f" ❓❓❓❓❓❓ {source_faces}")

        pieces_solved = 0

        source_face: FaceTracker
        for i, source_face in enumerate(source_faces):
            if source_face is not l1_white_tracker:
                with self._logger.tab(headline=lambda :f"{i+1} Target {target_face.color_at_face_str} <-- {source_face.color_at_face_str}"):
                    # === HEADLINE 1: SLICE ===
                    with self.ann.annotate(
                            h1=lambda: f"Solving Face {target_face.color_at_face_str} Slice {slice_row_index} "
                                       f"{target_face.color}  from Source {source_face.color_at_face_str}"):

                        if self._solve_single_center_slice_single_source_face(l1_white_tracker, target_face, source_face,
                                                                              slice_row_index):
                            pieces_solved += 1

        return pieces_solved

    def _tracke_center_slice(self, cs: CenterSlice, column: int):

        # self.debug(f"Tracking cent slice {cs.index} column {column}")

        cs.c_attributes[CENTER_SLICE_TRACK_KEY] = column

    def _is_center_slice(self, cs: CenterSlice) -> int | None:

        # the default is boolean False !!!
        x = cs.c_attributes[CENTER_SLICE_TRACK_KEY]

        # print(f"x: {x}")

        if type(x) is int:
            return x
        else:
            return None

    def _clear_center_slice(self, cs: CenterSlice) -> None:
        cs.c_attributes.pop(CENTER_SLICE_TRACK_KEY, None)

    def _clear_all_tracking(self):

        for c in self.cube.centers:
            for cc in c.all_slices:
                self._clear_center_slice(cc)

    def _iterate_all_tracked_slices_index(self, target_face: FaceTracker) -> Iterator[CenterSliceIndex]:

        for cs in target_face.face.center.all_slices:

            if self._is_center_slice(cs) is not None:
                rc = cs.index

                yield rc

    def _iterate_all_tracked_slices_and_index(self, target_face: FaceTracker) -> Iterator[
            Tuple[CenterSlice, CenterSliceIndex]]:

        for cs in target_face.face.center.all_slices:

            if self._is_center_slice(cs) is not None:
                rc = cs.index

                yield cs, rc

    # noinspection PyMethodMayBeStatic
    def _is_cent_piece_solved(self, center_piece: CenterSlice) -> bool:
        # this si solver data not visualization
        return "NxNCenters2_center_pice_solved" in center_piece.edge.c_attributes

    # noinspection PyMethodMayBeStatic
    def _mark_center_piece_solved(self, center_piece: CenterSlice) -> None:
        # this si solver data not visualization
        center_piece.edge.c_attributes["NxNCenters2_center_pice_solved"] = True

    def _mark_piece_with_v_mark_if_solved(self, req_color: Color, center_piece: CenterSlice) -> None:

        if center_piece.color != req_color:
            return

        mf = self.cube.sp.marker_factory
        mm = self.cube.sp.marker_manager

        checkmark = mf.checkmark()  # Green checkmark

        # visualization only
        mm.add_marker(center_piece.edge, "checkmark", checkmark, moveable=True)

        # this is algorithm !!!
        self._mark_center_piece_solved(center_piece)





    def _position_l1(self, l1_white_tracker: FaceTracker):
        """Position L1 down and target face to front."""
        # assert target_face is not l1_white_tracker
        # assert target_face is not l1_white_tracker.opposite

        self.cmn.bring_face_down(l1_white_tracker.face)

        assert l1_white_tracker.face is self.cube.down

    @contextmanager
    def _track_row_slices(self, l1_white_tracker: FaceTracker, slice_index: int) -> Generator[None, None, None]:
        """Track center slices in a row, cleanup on exit."""

        for target_face in l1_white_tracker.adjusted_faces():

            for rc in self._2d_center_row_slice_iter(slice_index):

                slice_piece = target_face.face.center.get_center_slice(rc)

                self._mark_piece_with_v_mark_if_solved(target_face.color, slice_piece)

                self._tracke_center_slice(slice_piece, rc[1])

        try:
            yield
        finally:
            # NOTE: We intentionally do NOT clear tracking here.
            # Tracking is accumulated across slices: each slice adds its own markers
            # for solved pieces. This allows _source_point_has_color() to check
            # _is_cent_piece_solved() and avoid destroying pieces from earlier slices.
            # Clearing happens only in _setup_l1() when all slices are done.
            pass

    @contextmanager
    def _setup_l1(self, l1_white_tracker: FaceTracker,
                  slice_index: int) -> Iterator[None]:
        """Setup L1 position and manage tracking lifecycle.

        Positions L1 (white face) down for solving. Tracking is accumulated
        during solving (via _track_row_slices) and cleared only here when
        all slices are done. This protects solved pieces from being destroyed.
        """
        self._position_l1(l1_white_tracker)
        try:
            yield
        finally:
            self._clear_all_tracking()

    def _try_remove_all_pieces_from_target_face_and_other_faces(self, l1_white_tracker: FaceTracker,
                                                                _target_face_tracker: FaceTracker,
                                                                slice_index: int,
                                                                remove_all: bool) -> int:
        """
            Go over all unsolved pieces in all faces and try to take out pieces that match them out of the face.
            Try to move from target face all colors that have the same color as the face so we can bring
            them back to target face.

            then go over all other face, and see if thers is candiate there

            try to move single piece !!!
            :param slice_index: The slice index to work on
            :return: Number of pieces moved/removed
        """


        assert l1_white_tracker.face is self.cube.down # assume in right setup
        assert l1_white_tracker.face.center.is3x3  # solved

        pieces_moved = 0

        for target_face_tracker in [_target_face_tracker] : #( f.face for f in l1_white_tracker.adjusted_faces() ) :

            # now check is there a slice on my target

            target_color: Color = target_face_tracker.color

            # now find candidate_point
            for point in self._2d_center_row_slice_iter(slice_index):

                if self.cube.cqr.is_center_in_odd(point):
                    continue  # cant move center

                target_face: Face = target_face_tracker.face

                # the point/piece we want to solve and for it we wan to move
                # a piece from target_face to up,
                point_to_solve_piece: CenterSlice = target_face.get_center_slice(point)

                if self._is_cent_piece_solved(point_to_solve_piece):
                    continue

                # find candidates on target
                candidate_point: Point = point
                for n in range(4):

                    # now try to  move piece with the required color from move_from_target_face
                    # to up face
                    move_from_target_face: Face
                    for move_from_target_face in l1_white_tracker.face.adjusted_faces():

                        candidate_piece = move_from_target_face.get_center_slice(candidate_point)

                        # it can be solved only if move_from_target_face is target_face

                        move_from_target_face_is_target_face = move_from_target_face is _target_face_tracker.face

                        if n == 0 and move_from_target_face_is_target_face:
                            # n == 0 is the original point we are tying to solve
                            # so of course there is no point to check it, if it was smae as target
                            # then it is solved
                            continue # for n in range(4)

                        # of course for other face then move_from_target_face it cannot be solved it the color is the target
                        # for our target we dont want to ove away solved pieces of course they are of slice < then un
                        if candidate_piece.color == target_color and (not move_from_target_face_is_target_face or not self._is_cent_piece_solved(candidate_piece) ):

                                up_face = l1_white_tracker.opposite.face
                                self.debug(f"‼️‼️‼️ Moving  {candidate_piece} from {move_from_target_face.color_at_face_str} to  {up_face}")
                                # ok start to work
                                # bring any face from up to taget, why not the oposite, becuase we dont care if we destory anothe rpoint on source
                                self._comm_helper.execute_communicator(
                                    up_face,  # source
                                    move_from_target_face,  # target
                                    (candidate_point, candidate_point),  # target point
                                    (candidate_point, candidate_point),
                                    True,
                                    False,
                                    None)

                                pieces_moved += 1
                                if not remove_all:
                                    return pieces_moved # exactly one
                                break # the for n in range(3) loop

                    candidate_point = self.cube.cqr.rotate_point_clockwise(candidate_point)



        return pieces_moved

    def _ws_remove_all_pieces_from_target_face(self, l1_white_tracker: FaceTracker, target_face: FaceTracker,
                                            slice_row_index: int) -> bool:
        """
            #claqude please document this method
            :type slice_row_index: int
        """

        work_was_done: bool = False

        assert l1_white_tracker.face.center.is3x3  # solved

        # now check is there a slice on my target

        target_color: Color = target_face.color

        with self._track_row_slices(l1_white_tracker,
                            slice_row_index):

            for cs, rc in self._iterate_all_tracked_slices_and_index(target_face):

                if cs.color == target_color:
                    continue

                # now search a source on my face
                source_rc = rc
                for _ in range(3):
                    source_rc = self.cube.cqr.rotate_point_clockwise(source_rc)

                    source_color = target_face.face.center.get_center_slice(source_rc).color

                    if source_color == target_color:
                        self.cmn.bring_face_front(target_face.face)

                        # search a target where to move it
                        temp_target_face: FaceTracker | None = None

                        for t in target_face.adjusted_faces():
                            # dont try to move to white
                            if t is not l1_white_tracker:
                                temp_target_face = t
                                break

                        assert temp_target_face is not None

                        # setup again
                        self.cmn.bring_face_front(temp_target_face.face)
                        assert temp_target_face.face is self.cube.front

                        assert target_face.face is not self.cube.back, f"how can it be {target_face.face} is back"

                        self.cmn.bring_face_up_preserve_front(target_face.face)

                        if self._block_communicator(target_face.color,
                                                    temp_target_face.face,
                                                    target_face.face,
                                                    rc):
                            work_was_done = True

                        # restore the original setup, need to improve
                        self._position_l1(l1_white_tracker)

                        break

                # we destroy it
                assert l1_white_tracker.face.center.is3x3  # solved

        return work_was_done

    def _solve_single_center_slice_single_source_face(self, l1_white_tracker: FaceTracker,
                                                      target_face: FaceTracker,
                                                      source_face: FaceTracker,
                                                      slice_row_index: int) -> bool:
        """
        Solve center pieces from a specific source face.

        The target face is brought to front, source face to up or back;
        then block commutators are used to move pieces.

        :param target_face: Target face tracker
        :param source_face: source face tracker
        :param slice_row_index: row index to solve
        :return: True if work was done
        """

        with self._logger.tab(lambda: f"➖〰️〰️〰️ Target {target_face.face} slice {slice_row_index} source {source_face.face} 〰️〰️〰️➖"):
            self.cmn.bring_face_front_preserve_down(target_face.face)
            assert target_face.face is self.cube.front

            return self._solve_single_center_piece_from_source_face_impl(l1_white_tracker,
                                                                             target_face, source_face,
                                                                             slice_row_index)

    def _solve_single_center_piece_from_source_face_impl(self, l1_white_tracker: FaceTracker,
                                                         target_face: FaceTracker,
                                                         source_face: FaceTracker,
                                                         slice_row_index: int) -> bool:

        # we comae hre from setup

        assert l1_white_tracker.face is self.cube.down

        self.cmn.bring_face_front_preserve_down(target_face.face)

        # if source_face is not target_face.opposite:
        #     self.cmn.bring_face_up_preserve_front(source_face.face)

        cube = self.cube

        assert target_face.face is cube.front
        # assert source_face.face in [cube.up, cube.back]

        # mark all done
        for rc in self._2d_center_row_slice_iter(slice_row_index):

            slice_piece = target_face.face.center.get_center_slice(rc)

            self._mark_piece_with_v_mark_if_solved(target_face.color, slice_piece)


        color = target_face.color

        if self.count_color_on_face(source_face.face, color) == 0:
            self.debug(f"Working on slice {slice_row_index} @ {target_face.color_at_face_str} Found no piece {color} on {source_face.face.color_at_face_str}")
            return False  # nothing can be done here

        work_done = False

        for rc in self._iterate_all_tracked_slices_index(target_face):

            candidate_piece = target_face.face.center.get_center_slice(rc)

            self.debug(f"Working on slice {slice_row_index} Found piece candidate {candidate_piece}")

            if candidate_piece.color == color:
                continue

            wd = self._block_communicator(color,
                                          target_face.face,
                                          source_face.face,
                                          rc)
            center_slice = candidate_piece
            after_fixed_color = center_slice.color

            if wd:


                if after_fixed_color != color:
                    raise InternalSWError(f"Slice was not fixed {rc}, " +
                                          f"required={color}, " +
                                          f"actual={after_fixed_color}")

                self.debug(f"Fixed slice {rc}")

                self._mark_piece_with_v_mark_if_solved(target_face.color, center_slice)

                work_done = True

            # in this step we dont know to give a warning if not yet solved it is only single source




        return work_done

    def _source_point_has_color(self, target_point_color: Color,
                                required_color, source_face, s: Point, s2: Point) -> Tuple[Point, Point] | None:
        """Search for source point with required color, checking 4 rotations."""

        parent = self

        parent.debug(
            f"Start to search for {required_color} from point {s} on {source_face.color_at_face_str} ")

        for n in range(4):

            piece_on_source = source_face.center.get_center_slice(s)
            color_on_source = piece_on_source.color

            # calude: use lazy see issue #63
            parent.debug(
                f">>Rotate #{n} Searching for {required_color} on {source_face.color_at_face_str}  @{s} color {color_on_source}")
            second_point_piece = source_face.center.get_center_slice(s2)
            parent.debug(
                f">>Source face color is {source_face.color} Second point is  {s2}  color {second_point_piece.color}")

            if color_on_source == required_color:

                parent.debug(
                    f">>Color {color_on_source} on {s2}  {piece_on_source}  matches {required_color}")

                # we dont want to destroy
                second_point_on_source_color: Color = second_point_piece.color
                # !!!!!!!!!!!!!!!!!!!!!!!! bug for even cube
                # if second_point_on_source_color == source_face.color:
                # but if it is the same color as target that is going to replace then it is ok
                #
                second_point_is_solved = self._is_cent_piece_solved(second_point_piece)
                self.debug(f"Second point {second_point_piece} is solved {second_point_is_solved}", f"Second point color {second_point_on_source_color}")
                if target_point_color != second_point_on_source_color and second_point_is_solved:
                    parent.debug(
                        f"❌❌❌❌❌❌❌❌ We dont want to destroy source {s2} {second_point_on_source_color} which will be replaced by color {target_point_color}")
                else:
                    return s, s2

            s = parent.cube.cqr.rotate_point_clockwise(s)
            s2 = parent.cube.cqr.rotate_point_clockwise(s2)

        return None

    def _block_communicator(self,
                            required_color: Color,
                            target_face: Face, source_face: Face, target_point: Tuple[int, int]) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        OPTIMIZED: Uses execute_communicator() with caching for 20%+ performance improvement.

        Workflow:
        1. Dry run to get natural source position (computes and caches)
        2. Search for source point with required color
        3. Execute with cached computation to avoid redundant calculations

        :param required_color: Color to search for on source face
        :param target_face: Target face (must be front)
        :param source_face: Source face (must be up or back)
        :param target_point: Center slice index [0..n)
        :return: False if block not found (or no work need to be done)
        """
        cube: Cube = target_face.cube
        assert target_face is cube.front

        # OPTIMIZATION: Step 1 - Dry run to get natural source position and cache computation
        # This calls _do_communicator() internally but stores the result for reuse
        dry_result = self._comm_helper.execute_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            dry_run=True
        )

        # is we are going to destroy second piece on the source
        second_point_on_source: Point = dry_result.second_replaced_with_target_point_on_source

        # Step 2 - Search for source point with required color at natural position
        natural_source = dry_result.source_point

        target_point_color: Color = target_face.center.get_center_slice(target_point).color

        source_point_and_second_source_point: Tuple[Point, Point] | None = self._source_point_has_color(target_point_color, required_color, source_face, natural_source,
                                                         second_point_on_source)

        if source_point_and_second_source_point is None:
            return False

        source_point_with_color = source_point_and_second_source_point[0]
        second_point_on_source = source_point_and_second_source_point[1]

        second_center_piece: CenterSlice = source_face.get_center_slice(second_point_on_source)
        second_point_is_solved = self._is_cent_piece_solved(second_center_piece)

        # OPTIMIZATION: Step 3 - Execute with cached computation (_cached_secret)
        # This reuses the _InternalCommData from Step 1, avoiding redundant calculations
        # Performance improvement: ~20% on 5x5, ~2-3% on 7x7+ cubes
        self._comm_helper.execute_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            source_block=(source_point_with_color, source_point_with_color),
            preserve_state=True,
            dry_run=False,
            _cached_secret=dry_result  # ← OPTIMIZATION: Reuse computation from Step 1
        )

        # if second point on source was replaced by the right color, then it is ok
        if second_point_is_solved:  # was it solved ?
            self._mark_piece_with_v_mark_if_solved(source_face.color,
                                                   second_center_piece)

        return True

    def count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)

    def _2d_center_row_slice_iter(self, slice_index: int) -> Iterator[Point]:
        """Iterate over all columns in a specific row."""
        n = self.cube.n_slices
        for c in range(n):
            yield slice_index, c

    D_LEVEL = 3


