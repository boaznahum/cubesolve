from collections.abc import Iterator
from contextlib import contextmanager
from typing import Generator

from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.geometry_types import Block, Point
from cube.domain.model import Color, Face
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.commutator.CommutatorHelper import CommutatorHelper
from cube.domain.solver.direct.lbl import _common
from cube.domain.solver.direct.lbl import _lbl_config
from cube.domain.tracker.trackers import FaceTracker
from cube.domain.solver.direct.lbl._common import (
    _is_cent_piece_marked_solved, mark_slice_and_v_mark_if_solved, _track_center_slice,
    _iterate_all_tracked_center_slices_index,
)
from cube.domain.solver.protocols import SolverElementsProvider
from cube.utils import symbols


class NxNCenters2(SolverHelper):
    """
    claude: # in these files row_index is the distance between l1_face, no metter on which orientation
    go over all methods and checkit match the definition asked me if you are not sue

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
    - source_face * n_rotate to align blocks

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
        super().__init__(slv, "NxNCenters2")

        self._preserve_cage = preserve_cage
        self._comm_helper = CommutatorHelper(slv)

        # Statistics: count of blocks solved by size
        self._block_stats: dict[int, int] = {}

    def reset_statistics(self) -> None:
        """Reset block solving statistics."""
        self._block_stats = {}

    def get_statistics(self) -> dict[int, int]:
        """Get block solving statistics (size -> count)."""
        return self._block_stats.copy()

    def _record_block_solved(self, block_size: int) -> None:
        """Record that a block of given size was solved."""
        self._block_stats[block_size] = self._block_stats.get(block_size, 0) + 1


    def solve_single_center_face_row(
            self, l1_white_tracker: FaceTracker, target_face: FaceTracker, face_row: int
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

        with self._logger.tab(lambda: f"{symbols.green_line(3)} Slice {face_row} {target_face.color_at_face_str} <-- all faces {symbols.green_line(3)}"):
            self._solve_single_center_slice_all_sources(l1_white_tracker, target_face, face_row)

    def _slice_on_target_face_solved(self, l1_white_tracker: FaceTracker, target_face: FaceTracker, face_row: int) -> bool:
        #del _target_face  # Unused - checks all faces, not just target

        # all over the solution we assume faces botton up is the ltr, but of course this is not true
        # if target was not down

        # what we need is a function that calculate the indexes relative to white face no matter where is it using the ltr system

        assert l1_white_tracker.face is self.cube.down

        # claud: why just marked solved why not solved ?
        for c in _common.get_center_row_pieces(self.cube, l1_white_tracker, target_face, face_row):
            if not _is_cent_piece_marked_solved(c):
                return False

        return True



    def _solve_single_center_slice_all_sources(self, l1_white_tracker: FaceTracker, target_face: FaceTracker,
                                               face_row: int) -> bool:

        work_was_done = False

        # maybe not need iterations


        with self._track_row_center_slices_nad_mark_if_solved(l1_white_tracker, face_row):

            face_slice_solved = self._slice_on_target_face_solved(l1_white_tracker, target_face, face_row)
            if face_slice_solved:
                self.debug(f"✅✅✅✅ All slices solved on face {target_face.face} row {face_row} ✅✅✅✅✅")
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
                                                                                face_row)
                self.debug(f"‼✅✅{solved_count} piece(s) solved {face_row} ‼✅✅")

                if solved_count > 0:
                    work_was_done = True
                else:
                    # if we reach here then not all were solved
                    if removed_count > 0:
                        raise InternalSWError(f"I moved pieces for {target_face} but still solve nothing")

                face_slice_solved = self._slice_on_target_face_solved(l1_white_tracker, target_face, face_row)


                if face_slice_solved:
                    self.debug(f"✅✅✅✅ Face {target_face} slice solved {face_row} ✅✅✅✅✅")
                    return work_was_done
                else:
                    self.debug(f"‼️‼️‼️‼️Face {target_face} slice NOT  solved, trying to remove from some face ‼️‼️‼️‼️")

                    removed_count = self._try_remove_all_pieces_from_target_face_and_other_faces(l1_white_tracker,
                                                                                                 target_face,
                                                                                                 face_row,
                                                                                                 False)

                    if removed_count == 0:
                        self.debug(f"‼️‼️‼️‼️Nothing was removed_count, aborting face {target_face} slice {face_row} ‼️‼️‼️‼️")
                        return work_was_done
                    else:
                        self.debug(f"‼️‼️‼️‼️{removed_count} piece(s) moved, trying again slice {face_row} ‼️‼️‼️‼️")

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

    @contextmanager
    def _track_row_center_slices_nad_mark_if_solved(self, l1_white_tracker: FaceTracker, face_row: int) -> Generator[None, None, None]:
        """Track center slices in a row, cleanup on exit."""

        for target_face in l1_white_tracker.adjusted_faces():

            for slice_piece in _common.get_center_row_pieces(self.cube, l1_white_tracker, target_face, face_row):

                mark_slice_and_v_mark_if_solved(slice_piece)

                _track_center_slice(slice_piece)

        try:
            yield
        finally:
            # NOTE: We intentionally do NOT clear tracking here.
            # Tracking is accumulated across slices: each slice adds its own markers
            # for solved pieces. This allows _source_point_has_color() to check
            # _is_cent_piece_solved() and avoid destroying pieces from earlier slices.
            # Clearing happens only in _setup_l1() when all slices are done.
            pass

    def _try_remove_all_pieces_from_target_face_and_other_faces(self, l1_white_tracker: FaceTracker,
                                                                _target_face_tracker: FaceTracker,
                                                                face_row: int,
                                                                remove_all: bool) -> int:
        """
            Go over all unsolved pieces in all faces and try to take out pieces that match them out of the face.
            Try to move from target face all colors that have the same color as the face so we can bring
            them back to target face.

            then go over all other face, and see if thers is candiate there

            try to move single piece !!!
            :param face_row: The face row disatnce from white
            :return: Number of pieces moved/removed
        """


        assert l1_white_tracker.face is self.cube.down # assume in right setup
        assert l1_white_tracker.face.center.is3x3  # solved

        pieces_moved = 0

        for target_face_tracker in [_target_face_tracker] : #( f.face for f in l1_white_tracker.adjusted_faces() ) :

            # now check is there a slice on my target

            target_color: Color = target_face_tracker.color

            # now find candidate_point
            for point_to_solve_piece in _common.get_center_row_pieces(self.cube, l1_white_tracker, target_face_tracker, face_row):

                point: tuple[int, int] = point_to_solve_piece.index

                if self.cube.cqr.is_center_in_odd(point):
                    continue  # cant move center

                if _is_cent_piece_marked_solved(point_to_solve_piece):
                    continue

                # Search for pieces with target_color on OTHER faces (not target face).
                # We rotate through 4 positions to find pieces at different orientations.
                # BUG FIX: The original code also operated on target_face at rotated positions,
                # which caused wrong rows to be solved. Now we ALWAYS skip the target face.
                candidate_point: Point = Point(*point)

                for _ in range(4):
                    # try to move piece with the required color from other faces to up face
                    move_from_target_face: Face
                    for move_from_target_face in l1_white_tracker.face.adjusted_faces():

                        # ALWAYS skip the target face - operating on it at any position
                        # would solve pieces in wrong rows
                        if move_from_target_face is _target_face_tracker.face:
                            continue

                        candidate_piece = move_from_target_face.get_center_slice(candidate_point)

                        # Look for pieces with target_color on other faces that we can move out
                        if candidate_piece.color == target_color and not _is_cent_piece_marked_solved(candidate_piece):

                            up_face = l1_white_tracker.opposite.face
                            self.debug(f"Moving {candidate_piece} from {move_from_target_face.color_at_face_str} to {up_face}")
                            # Move piece from up to this face, pushing the target_color piece to up
                            self._comm_helper.execute_commutator(
                                up_face,  # source
                                move_from_target_face,  # target
                                Block(candidate_point, candidate_point),  # target point
                                Block(candidate_point, candidate_point),
                                True,
                                False,
                                None)

                            pieces_moved += 1
                            if not remove_all:
                                return pieces_moved  # exactly one
                            break  # break inner loop, continue rotation

                    candidate_point = Point(*self.cube.cqr.rotate_point_clockwise(candidate_point))



        return pieces_moved

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

        cube = self.cube

        assert target_face.face is cube.front
        # assert source_face.face in [cube.up, cube.back]

        # mark all done
        for slice_piece in _common.get_center_row_pieces(cube, l1_white_tracker, target_face, slice_row_index):

            mark_slice_and_v_mark_if_solved(slice_piece)


        color = target_face.color

        if self._count_color_on_face(source_face.face, color) == 0:
            self.debug(f"Working on slice {slice_row_index} @ {target_face.color_at_face_str} Found no piece {color} on {source_face.face.color_at_face_str}")
            return False  # nothing can be done here


        work_done = False

        max_block_size = _lbl_config.LBL_MAX_BLOCK_SIZE

        # Unified approach: iterate piece-by-piece, try blocks starting at each position
        for rc in _iterate_all_tracked_center_slices_index(target_face):

            candidate_piece = target_face.face.center.get_center_slice(rc)

            # Skip if already correct color
            if candidate_piece.color == color:
                continue

            # Skip if already solved by a previous block in this iteration
            if _is_cent_piece_marked_solved(candidate_piece):
                continue

            self.debug(f"Working on slice {slice_row_index} Found piece candidate {candidate_piece}")

            # Search for blocks starting at rc (size controlled by config)
            blocks = self._search_blocks_starting_at(
                rc, target_face, color, max_size=max_block_size
            )

            # Try blocks largest first
            solved_block = False
            for block in blocks:
                if self._try_solve_block(
                    block, color, target_face.face, source_face.face
                ):
                    work_done = True
                    solved_block = True
                    break  # Move to next rc

            if not solved_block and len(blocks) > 0:
                # All blocks failed - this shouldn't happen for 1x1 blocks
                # but may happen for larger blocks if source doesn't have colors
                self.debug(f"No block starting at {rc} could be solved")

        return work_done

    def _search_blocks_starting_at(
        self,
        start_point: Point,
        target_face: FaceTracker,
        required_color: Color,
        max_size: int = 1
    ) -> list[Block]:
        """
        Search for valid blocks starting at start_point that need solving.

        Returns blocks sorted by size descending (largest first).
        If max_size=1, only returns the 1x1 block at start_point.

        Args:
            start_point: Point where block must start
            target_face: Target face tracker
            required_color: Color that pieces should have (target face color)
            max_size: Maximum block size (1 = single piece only)

        Returns:
            List of valid blocks, largest first. Always includes 1x1 if point needs solving.
        """
        face = target_face.face
        blocks: list[Block] = []

        # Always include the 1x1 block (single piece)
        blocks.append(Block(start_point, start_point))

        if max_size <= 1:
            return blocks

        # Try to extend to larger blocks
        n = self.n_slices

        # Find all unsolved positions in the tracked row
        unsolved_positions: set[Point] = set()
        for pt in _iterate_all_tracked_center_slices_index(target_face):
            piece = face.center.get_center_slice(pt)
            if piece.color != required_color and not _is_cent_piece_marked_solved(piece):
                unsolved_positions.add(pt)

        # Generate blocks starting at start_point
        for end_row in range(start_point[0], min(n, start_point[0] + max_size)):
            for end_col in range(start_point[1], min(n, start_point[1] + max_size)):
                end_point = Point(end_row, end_col)

                # Skip the 1x1 block (already added)
                if end_point == start_point:
                    continue

                # Check all positions in rectangle are unsolved
                all_unsolved = True
                for r in range(start_point[0], end_row + 1):
                    for c in range(start_point[1], end_col + 1):
                        if Point(r, c) not in unsolved_positions:
                            all_unsolved = False
                            break
                    if not all_unsolved:
                        break

                if not all_unsolved:
                    continue

                block = Block(start_point, end_point)

                # Check block is valid (won't self-intersect during commutator)
                if not self._comm_helper.is_valid_block(block[0], block[1]):
                    continue

                blocks.append(block)

        # Sort by size descending (largest first)
        blocks.sort(key=lambda b: b.size, reverse=True)
        return blocks

    def _try_solve_block(
        self,
        block: Block,
        required_color: Color,
        target_face: Face,
        source_face: Face
    ) -> bool:
        """
        Try to solve a block using block commutator.

        Unified code path for ALL block sizes (1x1, 2x1, etc.).

        Args:
            block: Block to solve (any size including 1x1)
            required_color: Color that pieces should have
            target_face: Target face
            source_face: Source face

        Returns:
            True if block was successfully solved, False otherwise
        """
        # Do dry run to find the natural source block
        dry_result = self._comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=block,
            dry_run=True
        )

        natural_source_block = dry_result.natural_source_block
        second_block = dry_result.second_block

        # Check if natural source block has required colors (with rotation search)
        valid_source = self._source_block_has_color_with_rotation(
            required_color, source_face, natural_source_block, second_block
        )

        if valid_source is None:
            self.debug(f"Block {block} skipped - source doesn't have required colors")
            return False

        # Execute the block commutator
        self._comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=block,
            source_block=valid_source,
            preserve_state=True,
            dry_run=False,
            _cached_secret=dry_result
        )

        # Verify all pieces in block were solved
        for pt in block.cells:
            piece = target_face.center.get_center_slice(pt)
            if piece.color != required_color:
                self.debug(f"Block {block} failed - piece at {pt} has wrong color")
                return False
            mark_slice_and_v_mark_if_solved(piece)

        self.debug(f"✅ Block {block} solved ({block.size} pieces)")
        self._record_block_solved(block.size)
        return True

    @staticmethod
    def _block_iter(block: Block) -> Iterator[Point]:
        """Iterate over all cells in a block."""

        return block.cells


    def _source_block_has_color_no_rotation(
        self,
        required_color: Color,
        source_face: Face,
        source_block: Block,
        second_block: Block
    ) -> bool:
        """
        Check if source block has required color WITHOUT rotation search.

        For multi-cell blocks, we cannot search rotations because rotating
        block coordinates changes the block's SHAPE (e.g., 1x3 horizontal
        becomes 3x1 vertical). The commutator's slice algorithm is computed
        based on the target block's shape, so the source block must have
        the same shape.

        For single-cell blocks, use _source_point_has_color which can search
        rotations since 1x1 shape is rotation-invariant.

        Args:
            required_color: Color required for all cells in source block
            source_face: Face to check
            source_block: Block to check (natural source position)
            second_block: Block that will be displaced

        Returns:
            True if source_block has required colors AND second_block is safe
        """
        # Check if ALL cells in source block have required color
        all_match = all(
            source_face.center.get_center_slice(pt).color == required_color
            for pt in self._block_iter(source_block)
        )

        if not all_match:
            return False

        # Check that second_block won't destroy solved pieces
        for pt in self._block_iter(second_block):
            second_piece = source_face.center.get_center_slice(pt)

            if _common.is_slice_solved_and_marked_solve(second_piece):
                # Would destroy a solved piece - not safe
                return False

        return True

    def _source_block_has_color_with_rotation(
        self,
        required_color: Color,
        source_face: Face,
        source_block: Block,
        second_block: Block
    ) -> Block | None:

        for _ in range(4):
            if self._source_block_has_color_no_rotation(required_color, source_face, source_block, second_block):
                return source_block

            source_block = source_block.rotate_clockwise(self.n_slices)
            second_block = second_block.rotate_clockwise(self.n_slices)

        return None

    def _count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)


