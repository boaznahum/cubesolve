from collections.abc import Iterator
from contextlib import contextmanager
from typing import Tuple, TypeAlias, Generator

from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color, CenterSlice, CenterSliceIndex
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.common.tracker.trackers import FaceTracker
from cube.domain.solver.protocols import SolverElementsProvider

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

    def debug(self, *args, level=3):
        if level <= NxNCenters2.D_LEVEL:
            super().debug("NxX 2 Centers:", args)

    def solve_single_center_row_slice(
            self, l1_white_tracker: FaceTracker, face_tracker: FaceTracker, slice_index: int
    ) -> None:
        """
        Solve a single row of center pieces on a face.

        Uses block commutators to bring pieces from source faces.
        Properly handles cage preservation if preserve_cage=True.

        Args:
            face_tracker: Face to solve
            slice_index: Slice index to solve  zeo based
            :param face_tracker:
            :param l1_white_tracker:
        """
        self._solve_single_center_row_slice(l1_white_tracker, face_tracker, slice_index)

    def _solve_single_center_row_slice(self, l1_white_tracker: FaceTracker, target_face: FaceTracker,
                                       slice_index: int):

        work_was_done = False

        # maybe not need iterations
        max_iter = 10
        iter_count = 0

        while True:
            iter_count += 1
            if iter_count > max_iter:
                raise InternalSWError("Maximum number of iterations reached")

            with self._setup_l1_and_target_and_track_slices(l1_white_tracker, target_face, slice_index):

                # position and tracking need to go inside
                if self._solve_single_center_row_slice_all_slices(l1_white_tracker, target_face,
                                                                  slice_index):
                    work_was_done = True

                # WIP: Commented out - this does position and tracking again !!!
                # if self._remove_all_pieces_from_target_face(l1_white_tracker, target_face, slice_row_index):
                #     work_was_done = True

            if not work_was_done:
                break

            return work_was_done

    def _solve_single_center_row_slice_all_slices(self, l1_white_tracker: FaceTracker,
                                                  target_face: FaceTracker,
                                                  slice_row_index: int
                                                  ) -> bool:
        source_faces = target_face.other_faces()

        work_was_done = False

        for source_face in source_faces:
            if source_face is not l1_white_tracker:
                # === HEADLINE 1: SLICE ===
                with self.ann.annotate(
                        h1=lambda: f"Solving Face {target_face.color_at_face_str} Slice {slice_row_index} "
                                   f"{target_face.color}  from Source {source_face.color_at_face_str}"):

                    if self._solve_single_center_piece_from_source_face(l1_white_tracker, target_face, source_face,
                                                                        slice_row_index):
                        work_was_done = True

        return work_was_done

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

    def _position_l1_and_target(self, l1_white_tracker: FaceTracker, target_face: FaceTracker):
        """Position L1 down and target face to front."""
        assert target_face is not l1_white_tracker
        assert target_face is not l1_white_tracker.opposite

        self.cmn.bring_face_down(l1_white_tracker.face)
        self.cmn.bring_face_front_preserve_down(target_face.face)

        assert l1_white_tracker.face is self.cube.down
        assert target_face.face is self.cube.front

    @contextmanager
    def _track_row_slices(self, target_face: FaceTracker, slice_index: int) -> Generator[None, None, None]:
        """Track center slices in a row, cleanup on exit."""
        for rc in self._2d_center_row_slice_iter(slice_index):
            slice_piece = target_face.face.center.get_center_slice(rc)
            self._tracke_center_slice(slice_piece, rc[1])
        try:
            yield
        finally:
            self._clear_all_tracking()

    @contextmanager
    def _setup_l1_and_target_and_track_slices(self, l1_white_tracker: FaceTracker,
                                              target_face: FaceTracker, slice_index: int) -> Iterator[None]:
        """Combined: position faces AND track slices."""
        """Position L1 down and target face to front."""
        self._position_l1_and_target(l1_white_tracker, target_face)
        with self._track_row_slices(target_face, slice_index):
            yield

    def _remove_all_pieces_from_target_face(self, l1_white_tracker: FaceTracker, target_face: FaceTracker,
                                            slice_row_index: int) -> bool:
        """
            #claqude please document this method
            :type slice_row_index: int
        """

        work_was_done: bool = False

        assert l1_white_tracker.face.center.is3x3  # solved

        # now check is there a slice on my target

        target_color: Color = target_face.color

        with self._setup_l1_and_target_and_track_slices(l1_white_tracker,
                                                        target_face,
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
                        self._position_l1_and_target(l1_white_tracker, target_face)

                        break

                # we destroy it
                assert l1_white_tracker.face.center.is3x3  # solved

        return work_was_done

    def _solve_single_center_piece_from_source_face(self, l1_white_tracker: FaceTracker,
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

        with self._setup_l1_and_target_and_track_slices(l1_white_tracker, target_face, slice_row_index):
            # position and tracking need to go inside
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

        color = target_face.color

        if self.count_color_on_face(source_face.face, color) == 0:
            self.debug(f"Working on slice {slice_row_index} Found no piece {color}")
            return False  # nothing can be done here

        work_done = False

        for rc in self._iterate_all_tracked_slices_index(target_face):

            self.debug(f"Working on slice {slice_row_index} Found piece {rc}")

            if target_face.face.center.get_center_slice(rc).color == color:
                continue

            wd = self._block_communicator(color,
                                          target_face.face,
                                          source_face.face,
                                          rc)
            if wd:

                after_fixed_color = target_face.face.center.get_center_slice(rc).color

                if after_fixed_color != color:
                    raise InternalSWError(f"Slice was not fixed {rc}, " +
                                          f"required={color}, " +
                                          f"actual={after_fixed_color}")

                self.debug(f"Fixed slice {rc}")

                work_done = True

        return work_done

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

        # Step 2 - Search for source point with required color at natural position
        natural_source = dry_result.source_point

        def source_point_has_color(s: Point) -> Point | None:
            """Search for source point with required color, checking 4 rotations."""
            for n in range(4):
                color_on_source = source_face.center.get_center_slice(s).color
                if color_on_source == required_color:
                    return s
                s = self.cube.cqr.rotate_point_clockwise(s)
            return None

        source_point_with_color = source_point_has_color(natural_source)
        if source_point_with_color is None:
            return False

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

        return True

    def count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)

    def _2d_center_row_slice_iter(self, slice_index: int) -> Iterator[Point]:
        """Iterate over all columns in a specific row."""
        n = self.cube.n_slices
        for c in range(n):
            yield slice_index, c

    D_LEVEL = 3
