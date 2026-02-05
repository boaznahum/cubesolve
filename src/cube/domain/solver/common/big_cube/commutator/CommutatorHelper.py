"""
Commutator Helper for NxN Big Cubes.

See docs/design/commutator.md for full documentation with theory and diagrams.

Provides the block commutator algorithm for any source/target face pair.
Unlike NxNCenters which only supports Front as target and Up/Back as source,
this helper supports all 30 face pair combinations.

Coordinate system: Bottom-Up, Left-to-Right (BULR/LTR)
- (0,0) is at bottom-left
- Y increases upward (ltr_y)
- X increases rightward (ltr_x)
"""
import sys
from collections.abc import Collection, Iterable, Iterator
from dataclasses import dataclass
from typing import Tuple

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.algs import Algs, Alg
from cube.domain.algs.SliceAlg import SliceAlg
from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator, FaceTranslationResult, SliceAlgorithmResult
from cube.domain.geometric.geometry_types import Block, CLGColRow, Point
from cube.domain.model import FaceName, Cube, CenterSlice
from cube.domain.model.Color import Color
from cube.domain.model.Face import Face
from cube.domain.model.SliceName import SliceName
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.common.big_cube.commutator._supported_faces import _get_supported_pairs
from cube.domain.solver.protocols import SolverElementsProvider


@dataclass(frozen=True)
class _InternalCommData:
    natural_source_coordinate: Point  # point on the source from where commutator will bring the data, before source setup alg
    natural_source_block: Block  # full block on source (for multi-cell blocks)
    trans_data: FaceTranslationResult


@dataclass(frozen=True)
class CommutatorResult:
    """Result of execute_commutator method.

    Contains both computed data (for dry_run) and execution algorithm (for actual execution).
    This result can be cached and reused to avoid redundant calculations.

    THE 3-CYCLE:
    ============
    The commutator performs: s1 → t → s2 → s1
    - natural_source_block (s1): Source block - pieces move TO target
    - target_block (t): Target block - receives pieces from source
    - second_block (s2): Intermediate block - temporarily holds target's pieces

    For 1x1 blocks, use .as_point to get the Point coordinate.

    Attributes:
        slice_name: Slice used in the commutator algorithm
        algorithm: The algorithm to execute (None if dry_run=True)
        natural_source_block: Source block (s1) in the 3-cycle
        target_block: Target block (t) in the 3-cycle
        second_block: Intermediate block (s2) in the 3-cycle
        _secret: Internal cache for optimization (avoid re-computation on second call)
    """
    slice_name: SliceName
    algorithm: Alg
    natural_source_block: Block
    target_block: Block
    second_block: Block
    _secret: _InternalCommData | None = None


class CommutatorHelper(SolverHelper):
    """
    Helper for the block commutator algorithm on NxN cubes.

    Supports any source/target face pair (30 combinations).
    Executes the commutator WITHOUT first positioning faces.
    Optionally preserves cube state (cage preservation).

    PUBLIC API USES LTR COORDINATES:
    ================================
    All public methods accept LTR (Left-to-Right) coordinates:
    - (0, 0) is at bottom-left corner
    - Y (first value) increases upward
    - X (second value) increases rightward

    The helper handles all coordinate translations internally.
    Clients should NOT use index coordinates directly.

    Key methods:
    - do_commutator(): Execute commutator with LTR block coordinates
    - get_expected_source_ltr(): Map target LTR to source LTR
    - rotate_ltr_on_face(): Rotate LTR on a face (physical rotation)
    - ltr_to_index() / index_to_ltr(): Coordinate translation
    """

    # Class variable for test iteration over multiple translation results.
    # For opposite faces, there are 2 valid results; tests can iterate both.
    _test_result_index: int = 0

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver, "CommutatorHelper")

    @property
    def n_slices(self) -> int:
        return self.cube.n_slices

    @classmethod
    def _select_translation_result(
        cls, results: list[FaceTranslationResult]
    ) -> FaceTranslationResult:
        """Select one translation result from multiple valid results.

        For opposite faces (F↔B, U↔D, L↔R), there are TWO valid translation
        results - one for each axis that connects them. For adjacent faces,
        there is only ONE result.

        WHY WE SORT BY SLICE NAME:
        ==========================
        The Face2FaceTranslator may return results in arbitrary order depending
        on internal iteration order. To ensure DETERMINISTIC behavior:
        1. dry_run and actual execution must use the SAME result
        2. Tests must be able to iterate ALL results to verify correctness

        By sorting by slice name (E, M, S alphabetically), we guarantee:
        - Same input always produces same output (deterministic)
        - _test_result_index can iterate results in predictable order
        - No hidden bugs from lucky ordering

        Args:
            results: List of valid FaceTranslationResult (1 for adjacent, 2 for opposite)

        Returns:
            Single FaceTranslationResult selected by _test_result_index % len(results)
        """
        # Sort by slice name for deterministic order (E < M < S alphabetically)
        sorted_results = sorted(
            results,
            key=lambda r: r.slice_algorithm.whole_slice_alg.slice_name.name
        )
        # Use modulo to handle both adjacent (1 result) and opposite (2 results)
        index = cls._test_result_index % len(sorted_results)
        return sorted_results[index]

    # =========================================================================
    # Coordinate Translation: LTR <-> Index
    # =========================================================================

    def ltr_to_index(self, face: Face, ltr_y: int, ltr_x: int) -> Point:
        """
        Translate LTR coordinates to center index coordinates.

        Args:
            face: The face to translate for
            ltr_y: Y in LTR system (0 = bottom, increases upward)
            ltr_x: X in LTR system (0 = left, increases rightward)

        Returns:
            (idx_row, idx_col) for use with face.center.get_center_slice()
        """
        idx_row = face.edge_left.get_edge_slice_index_from_face_ltr_index(face, ltr_y)
        idx_col = face.edge_bottom.get_edge_slice_index_from_face_ltr_index(face, ltr_x)
        return Point(idx_row, idx_col)

    def index_to_ltr(self, face: Face, idx_row: int, idx_col: int) -> Point:
        """
        Translate center index coordinates to LTR coordinates.

        Args:
            face: The face to translate for
            idx_row: Row index from get_center_slice()
            idx_col: Column index from get_center_slice()

        Returns:
            (ltr_y, ltr_x) in LTR system
        """
        ltr_y = face.edge_left.get_face_ltr_index_from_edge_slice_index(face, idx_row)
        ltr_x = face.edge_bottom.get_face_ltr_index_from_edge_slice_index(face, idx_col)
        return Point(ltr_y, ltr_x)

    def ltr_block_to_index(self, face: Face, ltr_block: Block) -> Block:
        """Translate an LTR block to index coordinates."""
        p1 = self.ltr_to_index(face, ltr_block[0][0], ltr_block[0][1])
        p2 = self.ltr_to_index(face, ltr_block[1][0], ltr_block[1][1])
        return Block(p1, p2)

    def get_natural_source_ltr(
            self, source: Face, target: Face, target_ltr: Point
    ) -> Point:
        """

        For debug only, it is done by the commutator

        Get the expected source LTR position for a given target LTR.

        Given a target LTR return the source on target that a single slice movemnt brinngs
        into target without source setup.

        Before the commutator do the source setup algorithm

        This is where the source piece should be (before rotation) to move
        to the target position.

        Args:
            source: Source face
            target: Target face
            target_ltr: Target position in LTR

        Returns:
            Expected source position in LTR on source face
        """

        data = self._do_commutator(source, target, Block(target_ltr, target_ltr))

        return data.natural_source_coordinate

    def execute_commutator(
            self,
            source_face: Face,
            target_face: Face,
            target_block: Block,
            source_block: Block | None = None,
            preserve_state: bool = True,
            dry_run: bool = False,
            _cached_secret: CommutatorResult | None = None
    ) -> CommutatorResult:
        """
        Unified commutator execution method with optional dry_run and optimization.

        This is the PRIMARY API for commutator operations. It combines the functionality
        of get_natural_source_ltr() and do_commutator() into a single method.

        MULTI-CELL BLOCK SUPPORT:
        =========================
        This method supports blocks of any valid size (not just 1x1). For multi-cell
        blocks, all pieces in the block cycle together as a unit. The result includes:
        - natural_source_block: Full block on source face (all cells)
        - target_block: Full block on target face (all cells)
        - second_block: Full block for the intermediate position (all cells)

        Block validity is determined by is_valid_block(), which checks that the
        block won't self-intersect after rotation during the commutator pattern.

        THE 3-CYCLE PATTERN:
        ===================
        The block commutator moves exactly 3 pieces (or blocks) in a cycle: s1 → t → s2 → s1

        ```
        SOURCE FACE          TARGET FACE
        ┌─────────┐         ┌─────────┐
        │  s1 ←─┐ │         │  ↓      │
        │       │ │         │  t      │
        │     s2→ │         │  ↑      │
        └─────────┘         └─────────┘

        Three-step cycle:
        1. s1 → t  (via slice move + target face rotation)
        2. t → s2  (target piece moves to intermediate position on source)
        3. s2 → s1 (intermediate piece moves back to original s1 position)

        S2 Derivation:
        - s2 is always on the SOURCE face
        - s2 position is determined by the target point rotation:
          • If CW rotation: s2 = rotate_clockwise(t) on SOURCE
          • If CCW rotation: s2 = rotate_counterclockwise(t) on SOURCE
        - The rotation type is determined by an intersection check
        ```

        WORKFLOW WITH DRY_RUN OPTIMIZATION:
        ===================================

        Step 1: Dry run to get natural source position and 3-cycle points
            >>> result = helper.execute_commutator(
            ...     source_face=cube.up,
            ...     target_face=cube.front,
            ...     target_block=((1,1), (1,1)),
            ...     dry_run=True
            ... )
            >>> # For 1x1 blocks, use .as_point to get the Point coordinate
            >>> natural_source = result.natural_source_block.as_point
            >>> print(f"Natural source: {natural_source}")
            >>> print(f"3-cycle: s1={result.natural_source_block}, t={result.target_block}, s2={result.second_block}")
            >>> assert result.algorithm is None  # No algorithm in dry_run

        Step 2: Manipulate/search the source position (e.g., rotate to find color)
            >>> source_point = natural_source
            >>> for rotation in range(4):
            ...     color = cube.up.center.get_center_slice(source_point).color
            ...     if color == required_color:
            ...         break
            ...     source_point = cube.cqr.rotate_point_clockwise(source_point)

        Step 3: Execute with cached computation (reuse the dry_run result)
            >>> final_result = helper.execute_commutator(
            ...     source_face=cube.up,
            ...     target_face=cube.front,
            ...     target_block=((1,1), (1,1)),
            ...     source_block=(source_point, source_point),
            ...     preserve_state=True,
            ...     dry_run=False,
            ...     _cached_secret=result  # OPTIMIZATION: reuse dry_run computation!
            ... )
            >>> algorithm = final_result.algorithm
            >>> # Execute the algorithm on the cube

        PARAMETERS:
        ===========
        source_face: Source face (where pieces come from)
        target_face: Target face (where pieces go to)
        target_block: Block coordinates on target face ((y0,x0), (y1,x1))
        source_block: Block coordinates on source face, defaults to target_block
        preserve_state: If True, preserve cube state (edges and corners return)
        dry_run: If True, return only computed source position (no execution)
        _cached_secret: CommutatorResult from previous dry_run call (optimization)

        RETURNS:
        ========
        CommutatorResult containing:
            - source_point: The computed source LTR position (first corner)
            - algorithm: The algorithm (None if dry_run=True)
            - natural_source: Source point (s1) - NATURAL SOURCE position for 3-cycle
            - target_point: Target point (t) - target block first corner
            - second_replaced_with_target_point_on_source: Intermediate point (s2)

            For multi-cell blocks (new fields):
            - natural_source_block: Block(s1_start, s1_end) - full source block
            - target_block: Block(t_start, t_end) - full target block
            - second_block: Block(s2_start, s2_end) - full intermediate block

            - _secret: Internal cache for optimization (do not use directly)

        NOTE on natural_source vs source_block parameter:
        - source_block parameter: input position for source face setup/rotation only
        - natural_source in result: the ACTUAL point in the 3-cycle (natural source position)
        - These may differ if source_block was provided for setup purposes

        RAISES:
        =======
        ValueError: If source and target are the same, face
        NotImplementedError: If face pair is not supported
        """
        if source_face is target_face:
            raise ValueError("Source and target must be different faces")

        # todo: check in center of even is in source or target, raise exception

        if source_block is None:
            source_block = target_block

        # Multi-cell blocks are now supported - no 1x1 assertion needed
        # Validation is done by is_valid_block() during search

        # Check if this pair is supported
        if not self.is_supported(source_face, target_face):
            raise NotImplementedError(
                f"Face pair ({source_face}, {target_face}) not yet implemented"
            )

        # Get source point from input
        #xsource_point: Point = source_block[0]

        # OPTIMIZATION: Use cached secret from dry_run to avoid recomputation
        # if _cached_secret is not None and _cached_secret._secret is not None:
        #     internal_data = _cached_secret._secret
        # else:

        internal_data = self._do_commutator(source_face, target_face, target_block)

        # Compute the 3-cycle points (s1, t, s2)
        # CRITICAL: These are the ACTUAL points in the 3-cycle after any source setup rotation
        # s1 is ALWAYS the natural source position where the commutator actually operates
        # The input source_point is only for source face SETUP, not the cycle itself
        natural_source_block: Block = internal_data.natural_source_block  # Natural source position

        # Compute xp (s2) using correct algorithm:
        # xp = su'(translator(tf, sf, f(tp)))

        # Step 1: Get tp (target point) - for multi-cell blocks, process both corners
        tp_begin: Point = target_block[0]
        tp_end: Point = target_block[1]

        # Step 2: Apply f (face rotation on target) to tp
        on_front_rotate_n, target_block_after_rotate = self._compute_rotate_on_target(
            self.cube, target_face.name,
            internal_data.trans_data.slice_algorithm.whole_slice_alg.slice_name,
            target_block
        )

        # Apply f(tp): rotate tp by on_front_rotate_n on the target face
        # the second point on target that will be moved to source
        cqr = self.cube.cqr
        xpt_begin = cqr.rotate_point_clockwise(tp_begin, on_front_rotate_n)  # supports negative
        xpt_end = cqr.rotate_point_clockwise(tp_end, on_front_rotate_n) if tp_begin != tp_end else xpt_begin

        # Step 3: xpt is on target_face, find where it maps to on source_face translate_target_from_source(
        # source_face, target_face, coord) finds where coord on target_face goes on source_face
        slice_name = internal_data.trans_data.slice_algorithm.whole_slice_alg.slice_name
        xpt_on_source_begin = Face2FaceTranslator.translate_target_from_source(
            target_face, source_face, xpt_begin, slice_name
        )
        xpt_on_source_end = Face2FaceTranslator.translate_target_from_source(
            target_face, source_face, xpt_end, slice_name
        ) if tp_begin != tp_end else xpt_on_source_begin

        # Step 4: Apply su' (inverse setup) to get final xp in original coordinates
        source_setup_n_rotate = self._find_rotation_idx(source_block, natural_source_block)

        # undo the setup - supports negative
        xpt_on_source_after_un_setup = Point(*cqr.rotate_point_clockwise(xpt_on_source_begin,
                                                                  -source_setup_n_rotate))
        xpt_on_source_after_un_setup_end = Point(*cqr.rotate_point_clockwise(xpt_on_source_end,
                                                                  -source_setup_n_rotate)) if tp_begin != tp_end else xpt_on_source_after_un_setup

        # Build the full second_block for multi-cell blocks
        second_block_result = Block(xpt_on_source_after_un_setup, xpt_on_source_after_un_setup_end).normalize

        # Build the natural_source_block (accounting for source setup rotation)
        # The natural_source_block is the block AFTER source setup rotation
        natural_source_block_result = internal_data.natural_source_block
        # # su' rotates counterclockwise by source_setup_n_rotate (inverse of clockwise)
        # for _ in range(source_setup_n_rotate):
        #     xpt_on_source_after_un_setup = cqr.rotate_point_counterclockwise(xpt_on_source_after_un_setup)

        # Build and execute the full algorithm (same as original do_commutator)

        source_setup_alg = Algs.of_face(
            source_face.name) * source_setup_n_rotate if source_setup_n_rotate else Algs.NOOP

        # E, S, M
        slice_alg_data: SliceAlgorithmResult = internal_data.trans_data.slice_algorithm
        slice_base_alg: SliceAlg = slice_alg_data.whole_slice_alg

        on_front_rotate: Alg = Algs.of_face(target_face.name) * on_front_rotate_n

        # Build the commutator
        inner_slice_alg: Alg = self._get_slice_alg(slice_base_alg, target_block, target_face.name) * slice_alg_data.n
        second_inner_slice_alg: Alg = self._get_slice_alg(slice_base_alg, target_block_after_rotate,
                                                          target_face.name) * slice_alg_data.n

        cum = Algs.seq_alg(None,
                           inner_slice_alg,
                           on_front_rotate,
                           second_inner_slice_alg,
                           on_front_rotate.prime,
                           inner_slice_alg.prime,
                           on_front_rotate,
                           second_inner_slice_alg.prime,
                           on_front_rotate.prime
                           )

        if not dry_run:

            # Helper to iterate over all cells in a block
            def _block_iter(block: Block) -> Iterator[Point]:
                """Iterate over all cells in a block."""
                r1, c1 = block[0]
                r2, c2 = block[1]
                if r1 > r2:
                    r1, r2 = r2, r1
                if c1 > c2:
                    c1, c2 = c2, c1
                for r in range(r1, r2 + 1):
                    for c in range(c1, c2 + 1):
                        yield Point(r, c)

            # Animation annotation helpers - iterate over ALL cells in each block
            def _ann_target() -> Iterator[CenterSlice]:
                """Yield ALL target CenterSlice objects in the block."""
                for pt in _block_iter(target_block):
                    yield target_face.center.get_center_slice(pt)

            def _ann_source() -> Iterator[CenterSlice]:
                """Yield ALL source CenterSlice objects in the block."""
                for pt in _block_iter(source_block):
                    yield source_face.center.get_center_slice(pt)

            def _h2() -> str:
                """Headline for annotation - block size info."""
                if target_block.size == 1:
                    return ", 1x1 commutator"
                return f", {target_block.dim[0]}x{target_block.dim[1]} block commutator"

            def _ann_s2() -> Iterator[CenterSlice]:
                """Yield ALL s2 CenterSlice objects in the block (lazy - only called if animation enabled)."""
                for pt in _block_iter(second_block_result):
                    yield source_face.center.get_center_slice(pt)

            # Get marker factory for at-risk marker
            mf = self.cube.sp.marker_factory

            # Execute with animation annotations
            # Call the generator functions to create iterators (like _swap_slice does)
            # s2 is passed as additional_marker with at_risk marker
            with self.ann.annotate(
                    (_ann_source(), AnnWhat.Moved),
                    (_ann_target(), AnnWhat.FixedPosition),
                    additional_markers=[(_ann_s2(), AnnWhat.Moved, mf.at_risk)],
                    h2=_h2
            ):
                if source_setup_n_rotate:
                    self.op.play(source_setup_alg)
                self.op.play(cum)

            # CAGE METHOD: Undo source rotation to preserve paired edges
            if preserve_state and source_setup_n_rotate:
                self.op.play(source_setup_alg.prime)

        final_algorithm = (source_setup_alg + cum + source_setup_alg.prime).simplify()

        return CommutatorResult(
            slice_name=slice_name,
            algorithm=final_algorithm,
            natural_source_block=natural_source_block_result,
            target_block=target_block,
            second_block=second_block_result,
            _secret=None  # Don't cache after execution
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _normalize_block(block: Block) -> Block:
        """Normalize block coordinates so min values come first.

        A block is defined by two corner points: (r1, c1) and (r2, c2).
        This method ensures that r1 <= r2 and c1 <= c2 after normalization.

        This is critical for commutator algorithms because:
        1. M-slice selection depends on column ordering
        2. Block iteration assumes normalized coordinates
        3. Intersection checks require consistent ordering

        Args:
            block: Tuple of two points ((r1, c1), (r2, c2))

        Returns:
            Normalized block with r1 <= r2 and c1 <= c2

        See Also:
            cube.domain.geometric.geometry_types.Block.normalize

        """
        return block.normalize

    @staticmethod
    def _1d_intersect(range_1: tuple[int, int], range_2: tuple[int, int]) -> bool:
        """Check if two 1D ranges intersect."""
        x1, x2 = range_1
        x3, x4 = range_2
        if x1 > x2:
            x1, x2 = x2, x1
        if x3 > x4:
            x3, x4 = x4, x3
        return not (x3 > x2 or x4 < x1)

    def _is_inner_position(self, r: int, c: int) -> bool:
        """
        Check if (r, c) is in the inner 2x2 center of an even cube.

        On even cubes, inner 2x2 positions have adjacent M slices that share
        edge wings. These positions need special M slice ordering.

        - 4x4 (n_slices=2): ALL positions are inner (0,0) to (1,1)
        - 6x6 (n_slices=4): inner is (1,1) to (2,2)
        - 8x8 (n_slices=6): inner is (2,2) to (3,3)
        """
        n = self.n_slices
        if n % 2 != 0:
            return False  # Only even cubes have inner 2x2 issues
        # Inner 2x2 is at [n//2 - 1, n//2] for each dimension
        inner_min = n // 2 - 1
        inner_max = n // 2
        return inner_min <= r <= inner_max and inner_min <= c <= inner_max

    def _get_slice_alg(self, base_slice_alg: SliceAlg,
                       target_block: Block, on_face: FaceName):

        """Get slice algorithm for block position.

        Args:
            base_slice_alg: Base slice algorithm (M, E, or S)
            target_block: Block coordinates on target face
            on_face: Target face name

        Returns:
            Slice algorithm covering the block's column/row range
        """

        def exc(point: Point) -> int:
            # extract column
            return point[1]

        def exr(point: Point) -> int:
            # extract row
            return point[0]

        slice_name = base_slice_alg.slice_name
        slice_layout = self.cube.layout.get_slice(slice_name)
        if slice_layout.does_slice_cut_rows_or_columns(on_face) == CLGColRow.ROW:
            # cut rows so we extract columns
            ex = exc
        else:
            ex = exr

        slice_match_face_ltr = slice_layout.does_slice_of_face_start_with_face(on_face)

        #   index is from left to right, L is from left to right,
        # so we don't need to invert

        v1 = ex(target_block[0])  # begin
        v2 = ex(target_block[1])

        if not slice_match_face_ltr:
            v1 = self.cube.inv(v1)
            v2 = self.cube.inv(v2)

        if v1 > v2:
            v1, v2 = v2, v1

        # M[n:n] notation works for a single slice at position n
        return base_slice_alg[v1 + 1:v2 + 1]

    def _find_rotation_idx(self, actual_source_block: Block, natural_source_block: Block) -> int:
        """
        Find how many clockwise rotations of source face align actual to expected.

        After rotating source face by n_rotate clockwise, the piece at actual_source_idx
        will move to expected_source_idx.

        Args:
            actual_source_block: Where the piece actually is (index coords)
            natural_source_block: Where commutator expects it (index coords)

        Returns:
            Number of clockwise rotations (0-3)

        Raises:
            ValueError: If positions cannot be mapped by rotation
        """
        rotated = actual_source_block.normalize  # normalize so we can compare
        for n in range(4):
            # After n clockwise rotations, actual moves to rotated
            if rotated == natural_source_block:
                return n
            #normalized !!! so we can compare !!!
            rotated = rotated.rotate_clockwise(self.n_slices)

        raise ValueError(
            f"Cannot align {actual_source_block} to {natural_source_block} by rotation"
        )

    # =========================================================================
    # Supported Pairs
    # =========================================================================

    def get_supported_pairs(self) -> list[tuple[FaceName, FaceName]]:
        """
        Return list of (source, target) face pairs that are currently supported.

        These are the combinations that do_commutator() can handle.
        Other combinations will raise NotImplementedError.

        Returns:
            List of (source_face, target_face) tuples
        """
        return _get_supported_pairs()

    def is_supported(self, source: Face, target: Face) -> bool:
        """
        Check if a source/target face pair is currently supported.

        Args:
            source: Source face
            target: Target face

        Returns:
            True if this combination is implemented, False otherwise
        """
        for src, tgt in self.get_supported_pairs():
            if source.name is src and target.name is tgt:
                return True
        return False

    def _do_commutator(
            self,
            source_face: Face,
            target_face: Face,
            target_block: Block
    ) -> _InternalCommData:
        """
        Execute a block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        Args:
            source_face: Source face (where pieces come from)
            target_face: Target face (where pieces go to)
            target_block: Block coordinates on target face ((y0,x0), (y1,x1))
            source_block: Block coordinates on source face, defaults to target_block
            preserve_state: If True, preserve cube state (edges and corners return)

        Returns:
            True if the commutator was executed, False if not needed

        Raises:
            ValueError: If source and target are the same, face
            ValueError: If blocks cannot be mapped with 0-3 rotations
        """
        if source_face is target_face:
            raise ValueError("Source and target must be different faces")

        # Multi-cell blocks are now supported

        # Check if this pair is supported
        if not self.is_supported(source_face, target_face):
            raise NotImplementedError(
                f"Face pair ({source_face}, {target_face}) not yet implemented"
            )

        target_point_begin: Point = target_block[0]
        target_point_end: Point = target_block[1]

        # translate_source_from_target returns list (1 for adjacent, 2 for opposite faces)
        all_results: list[FaceTranslationResult] = Face2FaceTranslator.translate_source_from_target(
            target_face, source_face, target_point_begin
        )
        # Select one result deterministically (sorted by slice name, indexed by _test_result_index)
        translation_result: FaceTranslationResult = self._select_translation_result(all_results)

        # source_coord is on the slice_algorithm, not directly on FaceTranslationResult
        source_coord_begin = Point(*translation_result.slice_algorithm.source_coord)

        # For multi-cell blocks, translate the second corner as well
        if target_point_begin != target_point_end:
            # Translate the second corner using the same slice
            # We need to find the result that uses the same slice as the first corner
            selected_slice_name = translation_result.slice_algorithm.whole_slice_alg.slice_name
            all_results_end: list[FaceTranslationResult] = Face2FaceTranslator.translate_source_from_target(
                target_face, source_face, target_point_end
            )
            # Find the result with matching slice name
            matching_results = [
                r for r in all_results_end
                if r.slice_algorithm.whole_slice_alg.slice_name == selected_slice_name
            ]
            if not matching_results:
                raise InternalSWError(
                    f"No matching slice for second corner: {target_point_end} with slice {selected_slice_name}"
                )
            source_coord_end = Point(*matching_results[0].slice_algorithm.source_coord)
        else:
            # 1x1 block - both corners are the same
            source_coord_end = source_coord_begin

        natural_source_block = Block(source_coord_begin, source_coord_end).normalize
        return _InternalCommData(source_coord_begin, natural_source_block, translation_result)

    def _compute_rotate_on_target(self, cube: Cube,
                                  face_name: FaceName,
                                  slice_name: SliceName, target_block: Block) -> Tuple[int, Block]:

        """Compute rotation direction on target face to avoid slice intersection.

        Args:
            cube: The cube instance
            face_name: Target face name
            slice_name: The slice used to move pieces from source to target
            target_block: Block coordinates on target face

        Returns:
            Tuple of (rotation_count, target_block_after_rotate):
            - rotation_count: 1 for clockwise, -1 for counter-clockwise
            - target_block_after_rotate: Block coordinates after rotation
        """

        def exc(point: Point) -> int:
            # extract column
            return point[1]

        def exr(point: Point) -> int:
            # extract row
            return point[0]

        slice_layout = cube.layout.get_slice(slice_name)
        if slice_layout.does_slice_cut_rows_or_columns(face_name) == CLGColRow.ROW:
            # cut rows so we extract columns
            ex = exc
        else:
            ex = exr  # cut columns so we extract rows

        target_point_begin = target_block[0]
        target_point_end = target_block[1]

        cqr = cube.cqr
        target_begin_rotated_cw = Point(*cqr.rotate_point_clockwise(target_point_begin))
        target_end_rotated_cw = Point(*cqr.rotate_point_clockwise(target_point_end))

        if self._1d_intersect((ex(target_point_begin), ex(target_point_end)),
                              (ex(target_begin_rotated_cw), ex(target_end_rotated_cw))):

            on_front_rotate = -1
            target_begin_rotated_ccw = Point(*cqr.rotate_point_counterclockwise(target_point_begin))
            target_end_rotated_ccw = Point(*cqr.rotate_point_counterclockwise(target_point_end))

            target_block_after_rotate = Block(target_begin_rotated_ccw, target_end_rotated_ccw)

            if self._1d_intersect((ex(target_point_begin), ex(target_point_end)),
                                  (ex(target_begin_rotated_ccw), ex(target_begin_rotated_ccw))):
                print("Intersection still exists after rotation", file=sys.stderr)
                raise InternalSWError(f"Intersection still exists after rotation "

                                      f"target={target_block}"
                                      f"r={(target_point_begin[1], target_point_end[1])} "
                                      f"rcw{(target_begin_rotated_cw[1], target_end_rotated_cw[1])} "
                                      f"{(target_end_rotated_ccw[1], target_end_rotated_ccw[1])} ")
        else:
            # clockwise is OK
            target_block_after_rotate = Block(target_begin_rotated_cw, target_end_rotated_cw)
            on_front_rotate = 1

        return on_front_rotate, target_block_after_rotate

    def do_commutator(
            self,
            source_face: Face,
            target_face: Face,
            target_block: Block,
            source_block: Block | None = None,
            preserve_state: bool = True
    ) -> Alg:
        """
        Convenience wrapper - delegates to execute_commutator().

        DEPRECATED: Use execute_commutator() for new code with dry_run support.

        Execute a block commutator to move pieces from source to target.

        The commutator is: [M', F, M', F', M, F, M, F']
        This is BALANCED (2 F + 2 F' = 0), so corners return to their position.

        Args:
            source_face: Source face (where pieces come from)
            target_face: Target face (where pieces go to)
            target_block: Block coordinates on target face ((y0,x0), (y1,x1))
            source_block: Block coordinates on source face, defaults to target_block
            preserve_state: If True, preserve cube state (edges and corners return)

        Returns:
            Algorithm to execute

        Raises:
            ValueError: If source and target are the same, face
            NotImplementedError: If face pair is not supported
        """
        result = self.execute_commutator(
            source_face=source_face,
            target_face=target_face,
            target_block=target_block,
            source_block=source_block,
            preserve_state=preserve_state,
            dry_run=False
        )
        return result.algorithm or Algs.NOOP

    # =========================================================================
    # BLOCK SEARCH METHODS
    # Migrated from NxNCenters._search_big_block and related methods.
    # These methods find valid blocks on a face for commutator operations.
    # =========================================================================

    def _2d_center_iter(
        self,
        row_indices: Collection[int] | None = None,
        col_indices: Collection[int] | None = None
    ) -> Iterator[Point]:
        """
        Iterate over points in the center grid, optionally filtered.

        Args:
            row_indices: If provided, only iterate over these row indices.
                         If None, iterate over all rows [0, n_slices).
            col_indices: If provided, only iterate over these column indices.
                         If None, iterate over all columns [0, n_slices).

        Yields:
            Point(row, col) for each position in the filtered grid.
        """
        n = self.n_slices
        rows: Iterable[int] = row_indices if row_indices is not None else range(n)
        cols_range: Collection[int] = col_indices if col_indices is not None else range(n)
        for r in rows:
            for c in cols_range:
                yield Point(r, c)

    def _rotate_point_clockwise(self, r: int, c: int) -> Point:
        """
        Rotate a point 90 degrees clockwise on the center grid.

        For a grid of size n, rotating (r, c) clockwise gives (c, n-1-r).

        Args:
            r: Row coordinate
            c: Column coordinate

        Returns:
            Rotated Point(row, col)
        """
        n = self.n_slices
        return Point(c, n - 1 - r)

    def _rotate_point_counterclockwise(self, r: int, c: int) -> Point:
        """
        Rotate a point 90 degrees counterclockwise on the center grid.

        For a grid of size n, rotating (r, c) counterclockwise gives (n-1-c, r).

        Args:
            r: Row coordinate
            c: Column coordinate

        Returns:
            Rotated Point(row, col)
        """
        n = self.n_slices
        return Point(n - 1 - c, r)

    def is_valid_block(self, rc1: tuple[int, int], rc2: tuple[int, int]) -> bool:
        """
        Check if a block is valid for commutator operations.

        A block is invalid if rotating it by F would cause its columns to
        intersect with the original columns. This is because the commutator
        uses column-based slice moves, and intersection would corrupt the cycle.

        The check tries both clockwise and counterclockwise rotations.
        If both rotations cause intersection, the block is invalid.

        VISUAL EXPLANATION (3x3 center grid, n_slices=3):
        =================================================

        VALID BLOCK - Corner (0,0):
        ```
            col 0   1   2
        row  ┌───┬───┬───┐
          0  │ X │   │ X'│   X = original block at (0,0)
             ├───┼───┼───┤   X'= after CW rotation -> (0,2)
          1  │   │   │   │
             ├───┼───┼───┤   Columns: {0} vs {2} -> NO intersection
          2  │   │   │   │   VALID - can use either rotation
             └───┴───┴───┘
        ```

        INVALID BLOCK - Center (1,1) on odd grid:
        ```
            col 0   1   2
        row  ┌───┬───┬───┐
          0  │   │   │   │
             ├───┼───┼───┤   X = original block at (1,1)
          1  │   │ X │   │   CW rotation: (1,1) -> (1,1) SAME!
             ├───┼───┼───┤   CCW rotation: (1,1) -> (1,1) SAME!
          2  │   │   │   │
             └───┴───┴───┘   Columns: {1} vs {1} -> INTERSECTION
                             INVALID - center maps to itself
        ```

        INVALID BLOCK - Full row (0,0)-(0,2):
        ```
            col 0   1   2
        row  ┌───┬───┬───┐
          0  │ X │ X │ X │   X = original block spans cols {0,1,2}
             ├───┼───┼───┤
          1  │   │   │   │   CW: (0,0)→(0,2), (0,2)→(2,2)
             ├───┼───┼───┤        rotated cols = {2}
          2  │ X'│ X'│ X'│   But full row after CW = cols {0,1,2}
             └───┴───┴───┘
                             Columns: {0,1,2} vs {0,1,2} -> INTERSECTION
                             INVALID - rotated block overlaps original
        ```

        Args:
            rc1: First corner (row, col)
            rc2: Second corner (row, col)

        Returns:
            True if the block is valid, False if it would self-intersect
        """
        r1, c1 = rc1
        r2, c2 = rc2

        # Try clockwise rotation first
        rc1_rotated = self._rotate_point_clockwise(r1, c1)
        rc2_rotated = self._rotate_point_clockwise(r2, c2)

        # Check if columns intersect
        if self._1d_intersect((c1, c2), (rc1_rotated[1], rc2_rotated[1])):
            # Clockwise causes intersection, try counterclockwise
            rc1_rotated = self._rotate_point_counterclockwise(r1, c1)
            rc2_rotated = self._rotate_point_counterclockwise(r2, c2)

            if self._1d_intersect((c1, c2), (rc1_rotated[1], rc2_rotated[1])):
                # Both rotations cause intersection - block is invalid
                return False

        return True

    def _is_block(
        self,
        face: Face,
        color: Color,
        block: Block
    ) -> bool:
        """
        Check if all cells in a block have the specified color.

        Args:
            face: Face to check
            color: Required color for all cells
            block: Block to check

        Returns:
            True if all cells in the block have the specified color
        """
        center = face.center

        for cell in block.cells:
            if center.get_center_slice(cell).color != color:
                return False

        return True

    def _is_valid_and_block_for_search(
        self,
        face: Face,
        color: Color,
        block: Block
    ) -> bool:
        """
        Check if a block is both valid (no self-intersection) and has correct colors.

        Args:
            face: Face to check
            color: Required color for all cells
            block: Block to check

        Returns:
            True if block is valid and all cells have the correct color
        """
        if not self.is_valid_block(block.start, block.end):
            return False

        return self._is_block(face, color, block)

    def search_big_block(
        self,
        face: Face,
        color: Color,
        row_indices: Collection[int] | None = None,
        col_indices: Collection[int] | None = None,
        max_rows: int | None = None,
        max_cols: int | None = None
    ) -> list[tuple[int, Block]]:
        """
        Search for all possible blocks of a color on a face, sorted by size.

        For each matching position, this method:
        1. Adds a 1x1 block starting at that position
        2. Tries to extend the block horizontally (increasing row)
        3. Then extends vertically (increasing col) based on max row reached
        4. Adds the extended block

        Blocks are validated using is_valid_block() to ensure they won't
        self-intersect during commutator operations.

        MIGRATION NOTE: This replicates NxNCenters._search_big_block() exactly.
        Extension order: horizontal (rows) FIRST, then vertical (columns).

        Args:
            face: Face to search on
            color: Color to search for
            row_indices: If provided, only search starting positions in these rows.
                         If None, search all rows.
            col_indices: If provided, only search starting positions in these columns.
                         If None, search all columns.
            max_rows: If provided, limit block height to this many rows.
                      If None, blocks can extend to the full grid height.
            max_cols: If provided, limit block width to this many columns.
                      If None, blocks can extend to the full grid width.

        Returns:
            List of (size, Block) tuples, sorted by size descending.
            Each starting point may yield multiple blocks (1x1 and extended).

        Examples:
            # Current behavior (unchanged)
            blocks = helper.search_big_block(face, color)

            # LBL: Search row 0 only, max height 1 (horizontal strips)
            blocks = helper.search_big_block(face, color, row_indices=[0], max_rows=1)

            # Search column 2 only, max width 1 (vertical strips)
            blocks = helper.search_big_block(face, color, col_indices=[2], max_cols=1)
        """
        center = face.center
        res: list[tuple[int, Block]] = []
        n = self.n_slices

        # Calculate extension limits based on max_rows/max_cols
        # r_limit and c_limit are computed per starting position
        for rc in self._2d_center_iter(row_indices, col_indices):
            if center.get_center_slice(rc).color == color:
                # Collect 1x1 block only if valid (e.g., center on odd cube is invalid)
                if self.is_valid_block(rc, rc):
                    res.append((1, Block(rc, rc)))

                # Calculate row extension limit
                # If max_rows is set, limit to rc[0] + max_rows
                # Otherwise, extend to n
                r_limit = min(n, rc[0] + max_rows) if max_rows else n

                # Try to extend horizontally (over rows)
                r_max: int | None = None
                for r in range(rc[0] + 1, r_limit):
                    if not self._is_valid_and_block_for_search(
                        face, color, Block(rc, Point(r, rc[1]))
                    ):
                        break
                    r_max = r

                if r_max is None:
                    r_max = rc[0]

                # Calculate column extension limit
                # If max_cols is set, limit to rc[1] + max_cols
                # Otherwise, extend to n
                c_limit = min(n, rc[1] + max_cols) if max_cols else n

                # Try to extend vertically (over columns)
                c_max: int | None = None
                for c in range(rc[1] + 1, c_limit):
                    if not self._is_valid_and_block_for_search(
                        face, color, Block(rc, Point(r_max, c))
                    ):
                        break
                    c_max = c

                if c_max is None:
                    c_max = rc[1]

                # Calculate size and add extended block (only if valid)
                b = Block(rc, Point(r_max, c_max))
                if self.is_valid_block(b.start, b.end):
                    size = b.size
                    res.append((size, b))

        # Sort by size descending (largest blocks first)
        res = sorted(res, key=lambda s: s[0], reverse=True)
        return res
