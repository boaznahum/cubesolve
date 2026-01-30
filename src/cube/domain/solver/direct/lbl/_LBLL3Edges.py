"""
L3 Edge solver for NxN cubes using layer-by-layer approach.

This helper solves L3 edges (last layer edges) without disturbing
L1 or middle layer edges. Uses commutator-based algorithms.

See: .planning/L3_EDGES_DIAGRAMS.md for algorithm details.
"""
from typing import cast

from cube.domain.algs import Alg, Algs, SeqAlg
from cube.domain.model import EdgeWing, Edge
from cube.domain.model._part import EdgeName
from cube.domain.solver import SolveStep
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.direct.lbl._LBLNxNEdges import _LBLNxNEdges
from cube.domain.solver.protocols import SolverElementsProvider
from cube.domain.tracker import FacesTrackerHolder
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

    @property
    def _parent(self):
        from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
        return cast(LayerByLayerNxNSolver, self._solver)

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
                        self._solve_left_edge(l3_tracker.parent)

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

    def _solve_left_edge(self, th:FacesTrackerHolder) -> None:
        """Solve all wings on the left edge (FL) of front face."""
        cube = self.cube
        n_slices = cube.n_slices

        for slice_index in range(n_slices):
                self._solve_left_edge_slice(th, slice_index)

    def _solve_left_edge_slice(self, th:FacesTrackerHolder, target_index: int) -> None:
        """
        Solve a single wing on FL edge at given index.

        Args:
            target_index: Wing index on FL edge to solve.
        """
        cube = self.cube
        target_wing = cube.fl.get_slice(target_index)

        with self._logger.tab(f"Solving left edge Slice {target_wing.parent_name_index_colors_position}"):

            # Skip if already solved
            if target_wing.match_faces:
                self.debug(f"Wing {target_wing.parent_name_index_position} already solved")
                return

            # Find all matching source wings (may be 1 or 2)
            source_wings = self._find_sources_for_target(target_wing)

            self.debug(f"Found {len(source_wings)} sources for {target_wing.parent_name_and_index}")

            # Try each source until one works
            for source_wing in source_wings:
                self._dispatch_to_case_handler(th, source_wing, target_wing)

                if target_wing.match_faces:
                    self.debug(f"✅✅✅ Wing {target_wing.parent_name_index_colors_position} solved")
                else:
                    self.debug(f"‼️‼️‼️  Wing {target_wing.parent_name_index_colors_position} was solved")

                # After handling, the target should be solved
                # (future: could check and try next source if failed)
                break  # For now, just use the first one

    def _dispatch_to_case_handler(self, th:FacesTrackerHolder, source_wing: EdgeWing, target_wing: EdgeWing) -> None:
        """Dispatch to appropriate case handler based on source edge position."""
        cube = self.cube
        source_edge = source_wing.parent
        front = cube.front

        if source_edge is front.edge_right:  # FR ✅`with  flip ✅
            self._handle_fr_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_top:  # FU ✅`no flip
            self._handle_fu_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_bottom:  # FD
            self._handle_fd_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_left:  # FL
            self._handle_fl_to_fl(source_wing, target_wing)
        else:
            from cube.domain.exceptions.InternalSWError import InternalSWError
            raise InternalSWError(f"Unexpected source edge: {source_edge.name}")

        self._assert_all_edges_below_l3_are_ok(th)

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

        sources: list[EdgeWing] = []
        for edge in cube.edges:
            for wing in edge.all_slices:
                # Skip already solved
                if wing.match_faces:
                    continue

                # Check colors match
                if wing.colors_id != target_colors:
                    continue

                assert edge.on_face(front)

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

        # Map source index to target edge coordinate system
        mapped_si = self._map_wing_index_by_wing(source_wing, target_wing.parent)

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
        cube = source.cube

        assert target.parent is cube.front.edge_left

        with self._logger.tab(f"Case FR→FL: source={source.index}, target={ti}"):
            with source.tracker() as src_t:
                # 1. Setup: Bring FD to BU (doesn't affect FL/FR/FU)
                protect_bu_alg = self._protect_bu()

                # 2. (Right CM)': FR → FU ✅
                si = src_t.slice.index
                fu_target = self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FU)
                self._right_cm_prime(
                    source_index=si,
                    target_index=fu_target
                )

                assert src_t.parent is cube.front.edge_top
                # 3. Check orientation + flip if needed
                flip_alg = self._flip_fu_if_needed(src_t.slice)

                # 4. Left CM: FU → FL
                si = src_t.slice.index
                self._left_cm(
                    source_index=si,
                    target_index=self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FL)
                )

                # 5. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(protect_bu_alg.prime)

    def _handle_fu_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 2: Source on FU → Target on FL.

        Path: FU → FL (Left CM)
        Target position FL is not affected by protect_bu.
        """

        with self._logger.tab(f"Case FU→FL: source={source.parent_name_index_colors}, target={target.parent_name_index_colors_position}"):
            with source.tracker() as src_t:
                # 1. Setup: Bring FD to BU (doesn't affect FL/FU)
                protect_bu_alg = self._protect_bu()

                # 2. Check orientation + flip if needed
                flip_alg = self._flip_fu_if_needed(src_t.slice)

                # 3. Left CM: FU → FL
                si = src_t.slice.index
                self._left_cm(
                    source_index=si,
                    target_index=self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FL)
                )

                # 4. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(protect_bu_alg.prime)

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
                protect_bu_alg = self._protect_bu()

                # 3. (Left CM)': FL → FU
                si = src_t.slice.index
                self._left_cm_prime(
                    source_index=si,
                    target_index=self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FU)
                )

                # 4. F' - undo F rotation, source goes FU → FL
                self.op.play(Algs.F.prime)

                # 5. Check orientation + flip if needed (on FL now)
                flip_alg = self._flip_fl_if_needed(target)

                # 6. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(protect_bu_alg.prime)

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
                protect_bu_alg = self._protect_bu()

                # 2. First Left CM: FL → BU
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_index=self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FU),
                    target_index=wing_idx
                )

                # 3. Second Left CM: BU → FU
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_index=self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FU),
                    target_index=wing_idx
                )

                # 4. Flip FU (always required for this case)
                flip_alg = self._flip_fu()

                # 5. Third Left CM: FU → FL
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_index=wing_idx,
                    target_index=self._map_wing_index_to_wing_name(src_t.slice, EdgeName.FL)
                )

                # 6. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(protect_bu_alg.prime)

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
        expected = self._map_wing_index_by_name(EdgeName.FU, EdgeName.FL, source_index)
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
        expected = self._map_wing_index_by_name(EdgeName.FL, EdgeName.FU, source_index)
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
        expected = self._map_wing_index_by_name(EdgeName.FU, EdgeName.FR, source_index)
        assert target_index == expected, \
            f"Right CM: expected target={expected}, got {target_index}"

        alg = self._get_right_cm_alg(source_index)
        self.op.play(alg)

    def _get_right_cm_alg(self, source_index: int) -> SeqAlg:
        k = source_index + 1
        alg = Algs.seq(
            Algs.U, Algs.R,
            Algs.U.prime, Algs.M[k].prime,
            Algs.U, Algs.R.prime,
            Algs.U.prime, Algs.M[k]
        )
        return alg

    def _right_cm_prime(self, source_index: int, target_index: int) -> None:
        """
        Right Commutator Inverse: 3-cycle FU → BU → FR → FU
        (Reverse direction: FR → FU)

        FR[source_index] → FU[target_index]

        Args:
            source_index: Wing index on FR (source position)
            target_index: Wing index on FU (target position)
        """

        expected = self._map_wing_index_by_name(EdgeName.FR, EdgeName.FU, source_index)
        assert target_index == expected, \
            f"Right CM': expected target={expected}, got {target_index}"


        # claude: the CM index is detreimned by the taget of FU !!!
        # the index is detrimnd by the index on FU, and in this case it is the target!!!
        # so i changed to target


        alg = self._get_right_cm_alg(target_index)
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

    def _get_flip_fu_alg(self) -> Alg:

        alg = Algs.parse_multiline("""                                                                                                              
                    # flip FU, U edges are swapped , UL->UR->UB->Ul
                    # front edges are untouched,
                    # other edges swapped, not intersting
                    U2  B'   R'  U   R
                    
                    # These were swapped UL->UR->UB->UL
                    # we only intersing in bringing UB to place it is the one that touched by comminacor abont FU
                    #  and FR/FL
                    # bring FU to FR,
                    U'
                    # swap UL and FU
                    R U R' U R U2 R' U
                    
                    #bring FU back
                    U
                    
                    
                                                                                                                                
             """)
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
        alg = self._get_flip_fu_alg()
        self.op.play(alg)
        return alg

    def _flip_fu_if_needed(self, source_on_fu: EdgeWing) -> Alg:
        """Flip FU wing if orientation is wrong. Returns alg or noop."""
        cube = self.cube

        assert source_on_fu.parent is cube.front.edge_top
        l3_color = cube.front.color

        if source_on_fu.get_face_edge(cube.front).color != l3_color:
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


    def _map_wing_index_to_wing_name(self, from_wing: EdgeWing, to_edge_name: EdgeName) -> int:

        from_edge_name: EdgeName = from_wing.parent.name

        index = from_wing.index

        return self._map_wing_index_by_name(from_edge_name, to_edge_name, index)

    def _map_wing_index_by_wing(self, from_wing: EdgeWing, to_edge: Edge) -> int:

        from_edge_name: EdgeName = from_wing.parent.name
        to_edge_name: EdgeName = to_edge.name

        index = from_wing.index


        assert from_wing.parent.single_shared_face(to_edge) is not None

        return self._map_wing_index_by_name(from_edge_name, to_edge_name, index)


    def _map_wing_index_by_name(self, from_edge_name: EdgeName,
        to_edge_name: EdgeName, index: int) -> int:

        """
        Map wing index from one edge to another on the front face.

        Both edges must be on the front face. For non-adjacent edges,
        chains through intermediate edges.

        Args:
            from_edge_name: Source edge (EdgeName.FL, FU, FR, FD)
            to_edge_name: Target edge (EdgeName.FL, FU, FR, FD)
            index: Wing index on source edge

        Returns:
            Corresponding wing index on target edge
        """
        cube = self.cube


        if from_edge_name == to_edge_name:
            return index

        # Adjacent edge mappings
        # True = same index, False = inverted index
        # Verified by chaining: FL→FU→FR→FD→FL = same (i → i)
        _SAME = True
        _INV = False
        adjacent_map: dict[tuple[EdgeName, EdgeName], bool] = {
            # FL ↔ FU: same
            (EdgeName.FL, EdgeName.FU): _SAME,
            (EdgeName.FU, EdgeName.FL): _SAME,
            # FU ↔ FR: inv
            (EdgeName.FU, EdgeName.FR): _INV,
            (EdgeName.FR, EdgeName.FU): _INV,
            # FR ↔ FD: same
            (EdgeName.FR, EdgeName.FD): _SAME,
            (EdgeName.FD, EdgeName.FR): _SAME,
            # FD ↔ FL: inv
            (EdgeName.FD, EdgeName.FL): _INV,
            (EdgeName.FL, EdgeName.FD): _INV,
        }

        key = (from_edge_name, to_edge_name)

        if key in adjacent_map:
            return index if adjacent_map[key] else cube.inv(index)

        # Non-adjacent: chain through intermediate edge
        # FL <-> FR: chain through FU
        # FU <-> FD: chain through FL
        if from_edge_name == EdgeName.FL and to_edge_name == EdgeName.FR:
            mid_index = self._map_wing_index_by_name(from_edge_name, EdgeName.FU, index)
            return self._map_wing_index_by_name(EdgeName.FU, to_edge_name, mid_index)
        elif from_edge_name == EdgeName.FR and to_edge_name == EdgeName.FL:
            mid_index = self._map_wing_index_by_name(from_edge_name, EdgeName.FU, index)
            return self._map_wing_index_by_name(EdgeName.FU, to_edge_name, mid_index)
        elif from_edge_name == EdgeName.FU and to_edge_name == EdgeName.FD:
            mid_index = self._map_wing_index_by_name(from_edge_name, EdgeName.FL, index)
            return self._map_wing_index_by_name(EdgeName.FL, to_edge_name, mid_index)
        elif from_edge_name == EdgeName.FD and to_edge_name == EdgeName.FU:
            mid_index = self._map_wing_index_by_name(from_edge_name, EdgeName.FL, index)
            return self._map_wing_index_by_name(EdgeName.FL, to_edge_name, mid_index)

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
        for edge in l3_face.edges:
            for wing in edge.all_slices:
                if wing.match_faces:
                    count += 1
        return count

    def _assert_all_edges_below_l3_are_ok(self, th:FacesTrackerHolder):

        assert self._parent.is_solved_phase_with_tracker(th, SolveStep.LBL_L3_CENTER)
