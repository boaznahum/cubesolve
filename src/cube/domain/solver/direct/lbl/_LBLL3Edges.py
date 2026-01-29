"""
L3 Edge solver for NxN cubes using layer-by-layer approach.

This helper solves L3 edges (last layer edges) without disturbing
L1 or middle layer edges. Uses commutator-based algorithms.

See: .planning/L3_EDGES_DIAGRAMS.md for algorithm details.
"""

from cube.domain.algs import Alg, Algs
from cube.domain.model import EdgeWing
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.direct.lbl._LBLNxNEdges import _LBLNxNEdges
from cube.domain.solver.protocols import SolverElementsProvider
from cube.domain.tracker.trackers import FaceTracker


class _LBLL3Edges(SolverHelper):
    """
    L3 Edge solver - pairs edge wings on last layer.

    Invariant: All methods return cube to known state (L3 on front, below L3 intact)
    unless explicitly stated otherwise.

    Uses composition with _LBLNxNEdges to reuse existing commutator methods.
    """

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "_LBLL3Edges")
        self._logger.set_level(_LBLL3Edges.D_LEVEL)

        # Composition: reuse existing edge methods
        self._nxn_edges = _LBLNxNEdges(slv)

    # =========================================================================
    # Main Entry Point
    # =========================================================================

    def do_l3_edges(self, l3_tracker: FaceTracker) -> None:
        """
        Solve all L3 edges (pair edge wings on last layer).

        Args:
            l3_tracker: FaceTracker for L3 face. Will be brought to front.
        """
        with self._logger.tab("Solving L3 edges"):
            # Bring L3 to front
            self.cmn.bring_face_front(l3_tracker.face)

            MAX_ITERATIONS = 20
            n_iteration = 0

            while True:
                n_iteration += 1
                if n_iteration > MAX_ITERATIONS:
                    from cube.domain.exceptions.InternalSWError import InternalSWError
                    raise InternalSWError("L3 edges: Maximum iterations reached")

                n_solved_before = self._count_solved_l3_edges()

                # Rotate 4 times around front face, solve left edge each time
                for rotation_i in range(4):
                    with self._logger.tab(f"Rotation {rotation_i + 1}/4"):
                        self._solve_left_edge()

                        # Rotate cube around front center (z rotation)
                        if rotation_i < 3:  # Don't rotate after last iteration
                            self.op.play(Algs.Z)

                n_solved_after = self._count_solved_l3_edges()

                if n_solved_after == n_solved_before:
                    self.debug(f"No progress, stopping. Solved: {n_solved_after}")
                    break

                self.debug(f"Progress: {n_solved_before} -> {n_solved_after}")

    # =========================================================================
    # Left Edge Solving
    # =========================================================================

    def _solve_left_edge(self) -> None:
        """Solve all wings on the left edge (FL) of front face."""
        cube = self.cube
        n_slices = cube.n_slices

        for slice_index in range(n_slices):
            with self._logger.tab(f"Slice {slice_index}"):
                self._solve_left_edge_slice(slice_index)

    def _solve_left_edge_slice(self, target_index: int) -> None:
        """
        Solve a single wing on FL edge at given index.

        Args:
            target_index: Wing index on FL edge to solve.
        """
        cube = self.cube
        target_wing = cube.fl.get_slice(target_index)

        # Skip if already solved
        if target_wing.match_faces:
            self.debug(f"Wing {target_wing.parent_name_and_index} already solved")
            return

        # Find matching source wing
        source_wing = self._find_source_for_target(target_wing)
        if source_wing is None:
            self.debug(f"No source found for {target_wing.parent_name_and_index}")
            return

        # Assert source is on front face (L3)
        assert source_wing.parent.on_face(cube.front), \
            f"L3 source wing must be on front face, got {source_wing.parent.name}"

        # Dispatch to appropriate case handler
        source_edge = source_wing.parent

        front = cube.front
        if source_edge is front.edge_right:  # FR
            self._handle_fr_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_top:  # FU
            self._handle_fu_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_bottom:  # FD
            self._handle_fd_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_left:  # FL
            self._handle_fl_to_fl(source_wing, target_wing)
        else:
            from cube.domain.exceptions.InternalSWError import InternalSWError
            raise InternalSWError(f"Unexpected source edge: {source_edge.name}")

    # =========================================================================
    # Source Matching
    # =========================================================================

    def _find_source_for_target(self, target_wing: EdgeWing) -> EdgeWing | None:
        """
        Find a source wing that can solve the target.

        Matching criteria:
        - colors_id matches target.position_id
        - index is target_index or inv(target_index)
        - Orientation check determines if flip needed

        Returns:
            Matching source wing, or None if not found.
        """
        cube = self.cube
        target_colors = target_wing.position_id
        target_index = target_wing.index
        required_indices = [target_index, cube.inv(target_index)]

        # Search all edges on front face (L3)
        front = cube.front
        front_edges = [front.edge_left, front.edge_top, front.edge_right, front.edge_bottom]

        for edge in front_edges:
            for wing in edge.all_slices:
                # Skip already solved
                if wing.match_faces:
                    continue

                # Check colors match
                if wing.colors_id != target_colors:
                    continue

                # Check index compatibility
                if wing.index not in required_indices:
                    continue

                # Found a candidate - check orientation
                if self._is_source_usable(wing, target_wing):
                    return wing

        return None

    def _is_source_usable(self, source_wing: EdgeWing, target_wing: EdgeWing) -> bool:
        """
        Check if source wing can solve target based on orientation.

        Returns True if:
        - Color on front == L3 color AND source_index == target_index, OR
        - Color on front != L3 color AND source_index == inv(target_index)
        """
        cube = self.cube
        l3_color = cube.front.color

        source_color_on_front = source_wing.get_face_edge(cube.front).color
        needs_flip = (source_color_on_front != l3_color)

        ti = target_wing.index
        si = source_wing.index

        if needs_flip:
            return si == cube.inv(ti)
        else:
            return si == ti

    # =========================================================================
    # Case Handlers
    # =========================================================================

    def _handle_fr_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """Case 1: Source on FR → Target on FL."""
        with self._logger.tab(f"Case FR→FL: {source.parent_name_and_index}"):
            # 1. Setup: Bring FD to BU
            setup_alg = self._protect_bu()

            # 2. (Right CM)': FR → FU
            self._right_cm_prime(source.index)

            # 3. Check orientation + flip if needed
            flip_alg = self._flip_fu_if_needed(target)

            # 4. Left CM: FU → FL
            self._left_cm(target.index)

            # 5. Rollback
            if flip_alg:
                self.op.play(flip_alg.prime)
            self.op.play(setup_alg.prime)

    def _handle_fu_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """Case 2: Source on FU → Target on FL."""
        with self._logger.tab(f"Case FU→FL: {source.parent_name_and_index}"):
            # 1. Setup: Bring FD to BU
            setup_alg = self._protect_bu()

            # 2. Check orientation + flip if needed
            flip_alg = self._flip_fu_if_needed(target)

            # 3. Left CM: FU → FL
            self._left_cm(target.index)

            # 4. Rollback
            if flip_alg:
                self.op.play(flip_alg.prime)
            self.op.play(setup_alg.prime)

    def _handle_fd_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """Case 3: Source on FD → Target on FL."""
        with self._logger.tab(f"Case FD→FL: {source.parent_name_and_index}"):
            # 1. F rotation - frees up FD
            self.op.play(Algs.F)

            # 2. Setup: Bring FD to BU (FD is now free)
            setup_alg = self._protect_bu()

            # 3. (Left CM)': FL → FU
            self._left_cm_prime(target.index)

            # 4. F' - undo F rotation, source lands at FL
            self.op.play(Algs.F.prime)

            # 5. Check orientation + flip if needed (on FL now)
            flip_alg = self._flip_fl_if_needed(target)

            # 6. Rollback
            if flip_alg:
                self.op.play(flip_alg.prime)
            self.op.play(setup_alg.prime)

    def _handle_fl_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """Case 4: Source on FL → Target on FL (same edge, different index)."""
        with self._logger.tab(f"Case FL→FL: {source.parent_name_and_index}"):
            # 1. Setup: Bring FD to BU
            setup_alg = self._protect_bu()

            # 2. Left CM x2: FL → BU → FU
            self._left_cm(source.index)  # FL → BU
            self._left_cm(source.index)  # BU → FU

            # 3. Flip FU (always required for this case)
            flip_alg = self._flip_fu()

            # 4. Left CM: FU → FL
            self._left_cm(target.index)

            # 5. Rollback
            self.op.play(flip_alg.prime)
            self.op.play(setup_alg.prime)

    # =========================================================================
    # Commutator Algorithms
    # =========================================================================

    def _left_cm(self, wing_index: int) -> None:
        """
        Left Commutator: 3-cycle FU → FL → BU → FU

        Alg: U' L' U M[k]' U' L U M[k]
        """
        k = wing_index + 1  # 1-based for M slice
        alg = Algs.seq(
            Algs.U.prime, Algs.L.prime,
            Algs.U, Algs.M[k].prime,
            Algs.U.prime, Algs.L,
            Algs.U, Algs.M[k]
        )
        self.op.play(alg)

    def _left_cm_prime(self, wing_index: int) -> None:
        """
        Left Commutator Inverse: 3-cycle FU → BU → FL → FU
        (Reverse direction: FL → FU)
        """
        k = wing_index + 1
        alg = Algs.seq(
            Algs.U.prime, Algs.L.prime,
            Algs.U, Algs.M[k].prime,
            Algs.U.prime, Algs.L,
            Algs.U, Algs.M[k]
        )
        self.op.play(alg.prime)

    def _right_cm(self, wing_index: int) -> None:
        """
        Right Commutator: 3-cycle FU → FR → BU → FU

        Alg: U R U' M[k]' U R' U' M[k]
        """
        k = wing_index + 1
        alg = Algs.seq(
            Algs.U, Algs.R,
            Algs.U.prime, Algs.M[k].prime,
            Algs.U, Algs.R.prime,
            Algs.U.prime, Algs.M[k]
        )
        self.op.play(alg)

    def _right_cm_prime(self, wing_index: int) -> None:
        """
        Right Commutator Inverse: 3-cycle FU → BU → FR → FU
        (Reverse direction: FR → FU)
        """
        k = wing_index + 1
        alg = Algs.seq(
            Algs.U, Algs.R,
            Algs.U.prime, Algs.M[k].prime,
            Algs.U, Algs.R.prime,
            Algs.U.prime, Algs.M[k]
        )
        self.op.play(alg.prime)

    # =========================================================================
    # Setup & Flip Algorithms
    # =========================================================================

    def _protect_bu(self) -> Alg:
        """
        Bring FD wing to BU to protect it from CM destruction.

        Returns:
            The algorithm used (for .prime undo).
        """
        # TODO: Implement proper algorithm
        # For now, placeholder - need to determine exact moves
        alg = Algs.seq()  # Placeholder
        self.op.play(alg)
        return alg

    def _flip_fu(self) -> Alg:
        """
        Flip the wing on FU (preserves FL).

        Path: FU → BU → RB → RU → FU
        Alg: U'² B' R' U

        Returns:
            The algorithm used (for .prime undo).
        """
        alg = Algs.seq(
            Algs.U.prime, Algs.U.prime,  # U'²
            Algs.B.prime,
            Algs.R.prime,
            Algs.U
        )
        self.op.play(alg)
        return alg

    def _flip_fu_if_needed(self, target: EdgeWing) -> Alg | None:
        """Flip FU wing if orientation is wrong. Returns alg or None."""
        cube = self.cube
        fu_wing = cube.fu.get_slice(target.index)
        l3_color = cube.front.color

        if fu_wing.get_face_edge(cube.front).color != l3_color:
            return self._flip_fu()
        return None

    def _flip_fl(self) -> Alg:
        """
        Flip the wing on FL (preserves other L3 edges).

        TBD: Algorithm to be defined.

        Returns:
            The algorithm used (for .prime undo).
        """
        # TODO: Define FL flip algorithm
        alg = Algs.seq()  # Placeholder
        self.op.play(alg)
        return alg

    def _flip_fl_if_needed(self, target: EdgeWing) -> Alg | None:
        """Flip FL wing if orientation is wrong. Returns alg or None."""
        cube = self.cube
        fl_wing = cube.fl.get_slice(target.index)
        l3_color = cube.front.color

        if fl_wing.get_face_edge(cube.front).color != l3_color:
            return self._flip_fl()
        return None

    # =========================================================================
    # Helpers
    # =========================================================================

    def _count_solved_l3_edges(self) -> int:
        """Count number of solved edge wings on front face (L3)."""
        cube = self.cube
        count = 0
        front = cube.front
        for edge in [front.edge_left, front.edge_top, front.edge_right, front.edge_bottom]:
            for wing in edge.all_slices:
                if wing.match_faces:
                    count += 1
        return count
