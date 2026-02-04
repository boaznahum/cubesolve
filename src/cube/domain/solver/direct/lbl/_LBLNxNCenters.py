from collections.abc import Iterator
from contextlib import contextmanager
from typing import Generator, Tuple

from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.geometry_types import Block, Point
from cube.domain.model import Color, CenterSlice, Face
from cube.domain.model.Cube import Cube
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.commutator.CommutatorHelper import CommutatorHelper
from cube.domain.solver.direct.lbl import _common
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
    - In _block_commutator: source_face * n_rotate to align blocks

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

        # Try block-based solving first (multi-cell commutators)
        work_done = self._try_blocks_from_target(
            color, target_face, source_face.face
        )

        if True:
            # Fall back to piece-by-piece for remaining positions
            for rc in _iterate_all_tracked_center_slices_index(target_face):

                candidate_piece = target_face.face.center.get_center_slice(rc)

                self.debug(f"Working on slice {slice_row_index} Found piece candidate {candidate_piece}")

                if candidate_piece.color == color:
                    continue

                wd = self._block_commutator(color,
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

                    mark_slice_and_v_mark_if_solved(center_slice)

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
                second_point_is_solved = _is_cent_piece_marked_solved(second_point_piece)
                self.debug(f"Second point {second_point_piece} is solved {second_point_is_solved}", f"Second point color {second_point_on_source_color}")
                if target_point_color != second_point_on_source_color and second_point_is_solved:
                    parent.debug(
                        f"❌❌❌❌❌❌❌❌ We dont want to destroy source {s2} {second_point_on_source_color} which will be replaced by color {target_point_color}")
                else:
                    return s, s2

            s = Point(*parent.cube.cqr.rotate_point_clockwise(s))
            s2 = Point(*parent.cube.cqr.rotate_point_clockwise(s2))

        return None

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
            if _is_cent_piece_marked_solved(second_piece):
                # Would destroy a solved piece - not safe
                return False

        return True

    def _find_target_blocks(
        self,
        required_color: Color,
        target_face_tracker: FaceTracker
    ) -> list[Block]:
        """
        Find potential target blocks from tracked positions that need solving.

        Searches among tracked positions (the row being solved) for contiguous
        blocks that need solving (color != required_color).

        Args:
            required_color: Color pieces should be (target face color)
            target_face_tracker: Target face tracker

        Returns:
            List of target blocks (largest first), containing only tracked
            positions that need solving.
        """
        target_face = target_face_tracker.face
        n = self.cube.n_slices

        # Collect all tracked positions that need solving
        unsolved_positions: set[Point] = set()
        for pt in _iterate_all_tracked_center_slices_index(target_face_tracker):
            piece = target_face.center.get_center_slice(pt)
            if piece.color != required_color:
                unsolved_positions.add(pt)

        if not unsolved_positions:
            return []

        # Build blocks from unsolved positions
        # Try to find rectangular blocks
        blocks: list[Block] = []

        # For each unsolved position, try to extend horizontally and vertically
        checked: set[Point] = set()
        for start_pt in sorted(unsolved_positions):  # Process in order
            if start_pt in checked:
                continue

            # Find the maximum block starting from this position
            # that only contains unsolved, tracked positions
            max_r, max_c = start_pt[0], start_pt[1]

            # Extend right (column direction)
            while max_c + 1 < n:
                next_pt = Point(start_pt[0], max_c + 1)
                if next_pt in unsolved_positions:
                    max_c += 1
                else:
                    break

            # Extend down (row direction), checking entire width
            while max_r + 1 < n:
                # Check if entire row can be extended
                can_extend = True
                for c in range(start_pt[1], max_c + 1):
                    next_pt = Point(max_r + 1, c)
                    if next_pt not in unsolved_positions:
                        can_extend = False
                        break
                if can_extend:
                    max_r += 1
                else:
                    break

            block = Block(start_pt, Point(max_r, max_c))
            block_size = block.size

            if block_size > 1 and self._comm_helper.is_valid_block(block[0], block[1]):
                blocks.append(block)
                # Mark positions as checked
                for r in range(start_pt[0], max_r + 1):
                    for c in range(start_pt[1], max_c + 1):
                        checked.add(Point(r, c))

        # Sort by size descending
        blocks.sort(key=lambda b: b.size, reverse=True)
        return blocks

    def _try_blocks_from_target(
        self,
        required_color: Color,
        target_face_tracker: FaceTracker,
        source_face: Face
    ) -> bool:
        """
        Try block-based solving by finding target blocks first, then checking source.

        This method:
        1. Finds target blocks from tracked positions that need solving
        2. For each target block, does a dry_run to find the natural source block
        3. Checks if the natural source block has the required color (NO rotation)
        4. Executes the block commutator if valid

        IMPORTANT: For multi-cell blocks, we do NOT search rotations because
        rotating block coordinates changes the block's SHAPE. The commutator's
        slice algorithm depends on the target block's shape, so source must match.

        Args:
            required_color: Color to move (target face color)
            target_face_tracker: Target face tracker
            source_face: Source face

        Returns:
            True if any work was done, False otherwise
        """
        target_face = target_face_tracker.face
        work_done = False

        # Find target blocks from tracked positions
        target_blocks = self._find_target_blocks(required_color, target_face_tracker)

        self.debug(lambda : f"target_blocks: {target_blocks}")

        for target_block in target_blocks:
            block_size = target_block.size
            # if block_size <= 1:
            #     continue  # Only multi-cell blocks

            with self._logger.tab(lambda : f"‼️‼️‼️‼️‼️‼️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ Working on block {target_block} size {block_size}"):

                # Do dry run to find the natural source block
                dry_result = self._comm_helper.execute_commutator(
                    source_face=source_face,
                    target_face=target_face,
                    target_block=target_block,
                    dry_run=True
                )

                natural_source_block = dry_result.natural_source_block
                second_block = dry_result.second_block

                assert natural_source_block
                assert second_block

                # Verify natural_source_block has same dimensions as target_block
                # Face-to-face translation might change orientation!
                target_dims = target_block.dim
                source_dims = natural_source_block.dim
                if target_dims != source_dims:
                    self.debug(f"Target block {target_block} skipped - shape mismatch: "
                               f"target {target_dims} vs source {source_dims}")
                    assert False
                    continue

                # Re-verify is_valid_block for the target (should have been checked in _find_target_blocks)
                if not self._comm_helper.is_valid_block(target_block[0], target_block[1]):
                    self.debug(f"ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ℹ️ Target block {target_block} skipped - invalid block (would self-intersect)")
                    assert False, "It was checked above"
                    continue

                # Check if natural source block has required colors (NO rotation search)
                # For multi-cell blocks, rotation would change shape which breaks the algorithm
                if not self._source_block_has_color_no_rotation(
                    required_color, source_face, natural_source_block, second_block
                ):
                    self.debug(f"‼️‼️‼️‼️‼️‼️‼️‼️ Target block {target_block} skipped - natural source doesn't have required colors")
                    continue

                # Execute the block commutator (source_block = natural_source_block, no rotation needed)

                self.debug(
                    f"💕💕💕💕💕💕💕💕 execute_commutator Target block {target_block} ")
                self._comm_helper.execute_commutator(
                    source_face=source_face,
                    target_face=target_face,
                    target_block=target_block,
                    source_block=natural_source_block,  # Use natural position, no rotation
                    preserve_state=True,
                    dry_run=False,
                    _cached_secret=dry_result
                )

                # Verify that ALL pieces in target block were actually solved
                all_solved = True
                for pt in self._block_iter(target_block):
                    piece = target_face.center.get_center_slice(pt)
                    if piece.color != required_color:
                        all_solved = False
                        self.debug(f"⚠️ Block {target_block} piece at {pt} has wrong color "
                                   f"{piece.color} != {required_color}")

                        assert False
                        break

                if not all_solved:
                    # Block commutator failed - don't mark work_done
                    # Let piece-by-piece fallback handle this
                    self.debug(f"❌ Block commutator FAILED for {target_block}")
                    assert False
                    continue

                # Mark solved pieces on target only
                # NOTE: Do NOT mark second_block pieces! Those are on the source face,
                # and marking them would prevent future block commutators from using
                # those positions for their second_block (3-cycle intermediate).
                for pt in target_block.cells:
                    piece = target_face.center.get_center_slice(pt)
                    mark_slice_and_v_mark_if_solved(piece)

                self.debug(f"✅ Block commutator solved {block_size} pieces: {target_block}")
                work_done = True

        return work_done

    def _block_commutator(self,
                            required_color: Color,
                            target_face: Face, source_face: Face, target_point: Tuple[int, int]) -> bool:
        """
        Execute block commutator to move pieces from source to target.

        OPTIMIZED: Uses execute_commutator() with caching for 20%+ performance improvement.

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
        # This calls _do_commutator() internally but stores the result for reuse
        target_pt = Point(*target_point)
        dry_result = self._comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=Block(target_pt, target_pt),
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
        second_point_is_solved = _is_cent_piece_marked_solved(second_center_piece)

        # OPTIMIZATION: Step 3 - Execute with cached computation (_cached_secret)
        # This reuses the _InternalCommData from Step 1, avoiding redundant calculations
        # Performance improvement: ~20% on 5x5, ~2-3% on 7x7+ cubes
        self._comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=Block(target_pt, target_pt),
            source_block=Block(source_point_with_color, source_point_with_color),
            preserve_state=True,
            dry_run=False,
            _cached_secret=dry_result  # ← OPTIMIZATION: Reuse computation from Step 1
        )

        # if second point on source was replaced by the right color, then it is ok
        if second_point_is_solved:  # was it solved ?
            mark_slice_and_v_mark_if_solved(second_center_piece)

        return True

    def _count_color_on_face(self, face: Face, color: Color) -> int:
        return self.cqr.count_color_on_face(face, color)


