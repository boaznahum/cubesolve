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

                n_solved_before = self._count_solved_l3_wings(l3_tracker)

                # Rotate 4 times around front face, solve left edge each time
                for rotation_i in range(4):
                    with self._logger.tab(f"Rotation {rotation_i + 1}/4"):
                        self._solve_left_edge()

                        # Rotate cube around front center (z rotation)
                        if rotation_i < 3:  # Don't rotate after last iteration
                            self.op.play(Algs.Z)

                n_solved_after = self._count_solved_l3_wings(l3_tracker)

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

        # Find all matching source wings (may be 1 or 2)
        source_wings = self._find_sources_for_target(target_wing)

        self.debug(f"Found {len(source_wings)} sources for {target_wing.parent_name_and_index}")

        # Try each source until one works
        for source_wing in source_wings:
            self._dispatch_to_case_handler(source_wing, target_wing)
            # After handling, the target should be solved
            # (future: could check and try next source if failed)
            break  # For now, just use the first one

    def _dispatch_to_case_handler(self, source_wing: EdgeWing, target_wing: EdgeWing) -> None:
        """Dispatch to appropriate case handler based on source edge position."""
        cube = self.cube
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

    def _find_sources_for_target(self, target_wing: EdgeWing) -> list[EdgeWing]:
        """
        Find all source wings that can solve the target.

        Matching criteria:
        - colors_id matches target.position_id
        - index is target_index or inv(target_index)
        - Not already solved
        - On front face (L3)

        Returns:
            List of matching source wings (never empty - asserts if none found).
        """
        cube = self.cube
        target_colors = target_wing.position_id
        target_index = target_wing.index
        required_indices = [target_index, cube.inv(target_index)]

        # Search ONLY front face edges (L3)
        front = cube.front
        front_edges = [front.edge_left, front.edge_top, front.edge_right, front.edge_bottom]

        sources: list[EdgeWing] = []
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

                # Check if usable based on orientation
                if self._is_source_usable(wing, target_wing):
                    sources.append(wing)

        # There must always be at least one source
        assert sources, f"No source found for {target_wing.parent_name_and_index} - this is a bug"

        return sources

    def _is_source_usable(self, source_wing: EdgeWing, target_wing: EdgeWing) -> bool:
        """
        Check if source wing can solve target based on orientation.

        Maps source index to target edge coordinate system, then checks:
        - Color on front == L3 color AND mapped_si == ti, OR
        - Color on front != L3 color AND mapped_si == inv(ti)
        """
        cube = self.cube
        l3_color = cube.front.color

        source_color_on_front = source_wing.get_face_edge(cube.front).color
        needs_flip = (source_color_on_front != l3_color)

        ti = target_wing.index
        si = source_wing.index

        # Map source index to target edge coordinate system
        source_edge_name = source_wing.parent.name.value
        target_edge_name = target_wing.parent.name.value
        mapped_si = self._map_wing_index(source_edge_name, target_edge_name, si)

        if needs_flip:
            return mapped_si == cube.inv(ti)
        else:
            return mapped_si == ti

    # =========================================================================
    # Case Handlers
    # =========================================================================

    def _handle_fr_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 1: Source on FR → Target on FL.

        Diagram:
        ```
                ┌─────────┐
                │   FU    │
                │   [?]   │
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [T]  │  FRONT  │  [S]  │  ← S=Source, T=Target
        └───────┼─────────┼───────┘
                │   FD    │
                │   [H]   │  ← H=Helper (goes to BU)
                └─────────┘
        ```

        Steps:
        1. protect_bu: FD[H] → BU         (preserves FL/FR/FU)
        2. (Right CM)': FR[S] → FU        (preserves FL)
        3. flip FU if needed              (preserves FL)
        4. Left CM: FU[S] → FL            (work - moves to target)
        5. Rollback: undo flip, undo protect_bu
        """
        ti = target.index  # Target position index (recalculate if target edge moves)

        with self._logger.tab(f"Case FR→FL: source={source.index}, target={ti}"):
            with source.tracker() as src_t:
                # 1. Setup: Bring FD to BU (doesn't affect FL/FR/FU)
                setup_alg = self._protect_bu()

                # 2. (Right CM)': FR → FU
                si = src_t.slice.index
                self._right_cm_prime(
                    source_index=si,
                    target_index=self._map_wing_index("FR", "FU", si)
                )

                # 3. Check orientation + flip if needed
                flip_alg = self._flip_fu_if_needed(target)

                # 4. Left CM: FU → FL
                si = src_t.slice.index
                self._left_cm(
                    source_index=si,
                    target_index=self._map_wing_index("FU", "FL", si)
                )

                # 5. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(setup_alg.prime)

    def _handle_fu_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 2: Source on FU → Target on FL.

        Path: FU → FL (Left CM)
        Target position FL is not affected by protect_bu.
        """
        ti = target.index

        with self._logger.tab(f"Case FU→FL: source={source.index}, target={ti}"):
            with source.tracker() as src_t:
                # 1. Setup: Bring FD to BU (doesn't affect FL/FU)
                setup_alg = self._protect_bu()

                # 2. Check orientation + flip if needed
                flip_alg = self._flip_fu_if_needed(target)

                # 3. Left CM: FU → FL
                si = src_t.slice.index
                self._left_cm(
                    source_index=si,
                    target_index=self._map_wing_index("FU", "FL", si)
                )

                # 4. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(setup_alg.prime)

    def _handle_fd_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 3: Source on FD → Target on FL.

        Path: FD → FL (F) → FU ((Left CM)') → FL (F')
        F rotation moves target: FL → FU
        F' moves target back: FU → FL
        """
        ti = target.index

        with self._logger.tab(f"Case FD→FL: source={source.index}, target={ti}"):
            with source.tracker() as src_t:
                # 1. F rotation - moves source FD → FL, target FL → FU
                self.op.play(Algs.F)

                # 2. Setup: Bring FD to BU (FD is now free, doesn't affect FL/FU)
                setup_alg = self._protect_bu()

                # 3. (Left CM)': FL → FU
                si = src_t.slice.index
                self._left_cm_prime(
                    source_index=si,
                    target_index=self._map_wing_index("FL", "FU", si)
                )

                # 4. F' - undo F rotation, source goes FU → FL
                self.op.play(Algs.F.prime)

                # 5. Check orientation + flip if needed (on FL now)
                flip_alg = self._flip_fl_if_needed(target)

                # 6. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(setup_alg.prime)

    def _handle_fl_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 4: Source on FL → Target on FL (same edge, different index).

        Path: FL → BU (Left CM) → FU (Left CM) → flip → FL (Left CM)
        Source is at inv(ti), always needs flip.

        Left CM is a 3-cycle: FU → FL → BU → FU (all use same M[k] slice)
        """
        ti = target.index
        si = source.index

        with self._logger.tab(f"Case FL→FL: source={si}, target={ti}"):
            with source.tracker() as src_t:
                # 1. Setup: Bring FD to BU (doesn't affect FL)
                setup_alg = self._protect_bu()

                # 2. First Left CM: FL → BU
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_index=self._map_wing_index("FL", "FU", wing_idx),
                    target_index=wing_idx
                )

                # 3. Second Left CM: BU → FU
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_index=self._map_wing_index("FL", "FU", wing_idx),
                    target_index=wing_idx
                )

                # 4. Flip FU (always required for this case)
                flip_alg = self._flip_fu()

                # 5. Third Left CM: FU → FL
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_index=wing_idx,
                    target_index=self._map_wing_index("FU", "FL", wing_idx)
                )

                # 6. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(setup_alg.prime)

    # =========================================================================
    # Commutator Algorithms
    # =========================================================================

    def _left_cm(self, source_index: int, target_index: int) -> None:
        """
        Left Commutator: 3-cycle FU → FL → BU → FU

        FU[source_index] → FL[target_index]

        Alg: U' L' U M[k]' U' L U M[k]

        Args:
            source_index: Wing index on FU (source position)
            target_index: Wing index on FL (target position)
        """
        expected = self._map_wing_index("FU", "FL", source_index)
        assert target_index == expected, \
            f"Left CM: expected target={expected}, got {target_index}"

        k = source_index + 1  # 1-based for M slice
        alg = Algs.seq(
            Algs.U.prime, Algs.L.prime,
            Algs.U, Algs.M[k].prime,
            Algs.U.prime, Algs.L,
            Algs.U, Algs.M[k]
        )
        self.op.play(alg)

    def _left_cm_prime(self, source_index: int, target_index: int) -> None:
        """
        Left Commutator Inverse: 3-cycle FU → BU → FL → FU
        (Reverse direction: FL → FU)

        FL[source_index] → FU[target_index]

        Args:
            source_index: Wing index on FL (source position)
            target_index: Wing index on FU (target position)
        """
        expected = self._map_wing_index("FL", "FU", source_index)
        assert target_index == expected, \
            f"Left CM': expected target={expected}, got {target_index}"

        k = source_index + 1
        alg = Algs.seq(
            Algs.U.prime, Algs.L.prime,
            Algs.U, Algs.M[k].prime,
            Algs.U.prime, Algs.L,
            Algs.U, Algs.M[k]
        )
        self.op.play(alg.prime)

    def _right_cm(self, source_index: int, target_index: int) -> None:
        """
        Right Commutator: 3-cycle FU → FR → BU → FU

        FU[source_index] → FR[target_index]

        Alg: U R U' M[k]' U R' U' M[k]

        Args:
            source_index: Wing index on FU (source position)
            target_index: Wing index on FR (target position)
        """
        expected = self._map_wing_index("FU", "FR", source_index)
        assert target_index == expected, \
            f"Right CM: expected target={expected}, got {target_index}"

        k = source_index + 1
        alg = Algs.seq(
            Algs.U, Algs.R,
            Algs.U.prime, Algs.M[k].prime,
            Algs.U, Algs.R.prime,
            Algs.U.prime, Algs.M[k]
        )
        self.op.play(alg)

    def _right_cm_prime(self, source_index: int, target_index: int) -> None:
        """
        Right Commutator Inverse: 3-cycle FU → BU → FR → FU
        (Reverse direction: FR → FU)

        FR[source_index] → FU[target_index]

        Args:
            source_index: Wing index on FR (source position)
            target_index: Wing index on FU (target position)
        """
        expected = self._map_wing_index("FR", "FU", source_index)
        assert target_index == expected, \
            f"Right CM': expected target={expected}, got {target_index}"

        k = source_index + 1
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

        Alg: D² B²
        Path: FD → BD → BU
        Does NOT touch FL, FR, FU.

        Returns:
            The algorithm used (for .prime undo).
        """
        alg = Algs.seq(
            Algs.D, Algs.D,  # D²
            Algs.B, Algs.B   # B²
        )
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

    def _flip_fu_if_needed(self, target: EdgeWing) -> Alg:
        """Flip FU wing if orientation is wrong. Returns alg or noop."""
        cube = self.cube
        fu_wing = cube.fu.get_slice(target.index)
        l3_color = cube.front.color

        if fu_wing.get_face_edge(cube.front).color != l3_color:
            return self._flip_fu()
        return Algs.NOOP

    def _flip_fl(self) -> Alg:
        """
        Flip the wing on FL (preserves other L3 edges).

        Alg: L² B' U' L U

        Returns:
            The algorithm used (for .prime undo).
        """
        alg = Algs.seq(
            Algs.L, Algs.L,  # L²
            Algs.B.prime,
            Algs.U.prime,
            Algs.L,
            Algs.U
        )
        self.op.play(alg)
        return alg

    def _flip_fl_if_needed(self, target: EdgeWing) -> Alg:
        """Flip FL wing if orientation is wrong. Returns alg or noop."""
        cube = self.cube
        fl_wing = cube.fl.get_slice(target.index)
        l3_color = cube.front.color

        if fl_wing.get_face_edge(cube.front).color != l3_color:
            return self._flip_fl()
        return Algs.NOOP

    # =========================================================================
    # Index Mapping
    # =========================================================================

    def _map_wing_index(self, from_edge_name: str, to_edge_name: str, index: int) -> int:
        """
        Map wing index from one edge to another on the front face.

        Both edges must be on the front face. For non-adjacent edges,
        chains through intermediate edges.

        Args:
            from_edge_name: Source edge ("FL", "FU", "FR", "FD")
            to_edge_name: Target edge ("FL", "FU", "FR", "FD")
            index: Wing index on source edge

        Returns:
            Corresponding wing index on target edge
        """
        cube = self.cube

        if from_edge_name == to_edge_name:
            return index

        # Adjacent edge mappings (hardcoded for now)
        # Format: (from, to) -> "same" or "inv"
        # User-verified values (2025-01-29):
        adjacent_map: dict[tuple[str, str], str] = {
            ("FL", "FU"): "same",
            ("FU", "FL"): "inv",
            ("FL", "FD"): "inv",
            ("FD", "FL"): "same",  # Fixed: was "inv"
            ("FU", "FR"): "inv",   # Fixed: was "same"
            ("FR", "FU"): "inv",
            ("FR", "FD"): "same",
            ("FD", "FR"): "inv",
        }

        key = (from_edge_name, to_edge_name)

        if key in adjacent_map:
            if adjacent_map[key] == "same":
                return index
            else:
                return cube.inv(index)

        # Non-adjacent: chain through intermediate edge
        # FL <-> FR: chain through FU or FD
        # FU <-> FD: chain through FL or FR
        if key == ("FL", "FR") or key == ("FR", "FL"):
            # Chain through FU
            mid_index = self._map_wing_index(from_edge_name, "FU", index)
            return self._map_wing_index("FU", to_edge_name, mid_index)
        elif key == ("FU", "FD") or key == ("FD", "FU"):
            # Chain through FL
            mid_index = self._map_wing_index(from_edge_name, "FL", index)
            return self._map_wing_index("FL", to_edge_name, mid_index)

        from cube.domain.exceptions.InternalSWError import InternalSWError
        raise InternalSWError(f"Unknown edge pair: {from_edge_name} -> {to_edge_name}")

    # =========================================================================
    # Helpers
    # =========================================================================

    def _count_solved_l3_wings(self, l3_tracker: FaceTracker) -> int:
        """
        Count number of solved edge wings on L3 face.

        Args:
            l3_tracker: Tracker for L3 face (can be anywhere on cube).

        Returns:
            Number of wings with matching colors on L3 edges.
        """
        count = 0
        l3_face = l3_tracker.face
        for edge in [l3_face.edge_left, l3_face.edge_top, l3_face.edge_right, l3_face.edge_bottom]:
            for wing in edge.all_slices:
                if wing.match_faces:
                    count += 1
        return count
