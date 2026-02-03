"""
L3 Edge solver for NxN cubes using layer-by-layer approach.

This helper solves L3 edges (last layer edges) without disturbing
L1 or middle layer edges. Uses commutator-based algorithms.

See: L3_EDGES_DIAGRAMS.md (same directory) for full algorithm details.
"""
from typing import cast

from cube.domain.algs import Alg, Algs, SeqAlg
from cube.domain.model import EdgeWing, Edge
from cube.domain.model._part import EdgeName
from cube.domain.solver import SolveStep
from cube.domain.solver.common.big_cube.commun.E2ECommutator import E2ECommutator
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

    Front Face Edge Layout::

            ┌─────────┐
            │   FU    │  (front-up edge)
            │ 0  1  2 │  (wing indices for 5x5)
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │ 0     │  FRONT  │     0 │
        │ 1     │  FACE   │     1 │
        │ 2     │  (L3)   │     2 │
        └───────┼─────────┼───────┘
            │ 0  1  2 │
            │   FD    │  (front-down edge)
            └─────────┘

    Commutators Reference::

        LEFT CM:   FU → FL → BU → FU  (3-cycle)
                   Alg: U' L' U M[k]' U' L U M[k]

        RIGHT CM:  FU → FR → BU → FU  (3-cycle)
                   Alg: U R U' M[k]' U R' U' M[k]

        (LEFT CM)':  FU → BU → FL → FU  (reverse)
        (RIGHT CM)': FU → BU → FR → FU  (reverse)

    Case Summary:

        | Case | Source | Steps |
        |------|--------|-------|
        | 1 | FR | Setup → (Right CM)' → [Flip?] → Left CM → Rollback |
        | 2 | FU | Setup → [Flip?] → Left CM → Rollback |
        | 3 | FD | F → Setup → (Left CM)' → F' → [Flip FL?] → Rollback |
        | 4 | FL | Setup → Left CM x2 → Flip → Left CM → Rollback |
    """

    D_LEVEL = 3

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "_LBLL3Edges")
        self._logger.set_level(_LBLL3Edges.D_LEVEL)

        # Composition: reuse existing edge methods
        self._nxn_edges = _LBLNxNEdges(slv)
        self._e2e_comm = E2ECommutator(slv)

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

            # we have for edges  Left A  Bottom B Right C  Top D
            # Start from A, solving it, B is buttonis destroyes
            # move A to right, A->Right C Right->Left,
            # B and D swapped not D on Button, it is destroyes
            # Solve Left C
            # if it solved, it means on top / botton there only top / button colors so
            # we can use RF' method to solve then

            for _ in range(2): # i still dont know why 2
                with self._logger.tab(lambda : "Solving first edge"):
                    self._solve_left_edge(l3_tracker)

                self.op.play(Algs.Z * 2)
                with self._logger.tab(lambda : "Solving second opposite edge"):
                    self._solve_left_edge(l3_tracker)

                self.op.play(Algs.Z * 2)

            #now i ready to second phase, solving by RF' algorithm


    # =========================================================================
    # Left Edge Solving
    # =========================================================================

    def _solve_left_edge(self, l3t:FaceTracker) -> None:
        """Solve all wings on the left edge (FL) of front face."""
        cube = self.cube
        n_slices = cube.n_slices

        for slice_index in range(n_slices):
                self._solve_left_edge_slice(l3t, slice_index)

        left = cube.front.edge_left
        if self._is_edge_solved(left):
            self.debug(lambda : f"✅✅💚💚 {left.name} is solved 💚💚💚")



    def _solve_left_edge_slice(self, l3t:FaceTracker, target_index: int) -> None:
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
                self._dispatch_to_case_handler(l3t, source_wing, target_wing)

                if target_wing.match_faces:
                    self.debug(f"✅✅✅ Wing {target_wing.parent_name_index_colors_position} solved")
                else:
                    self.debug(f"‼️‼️‼️  Wing {target_wing.parent_name_index_colors_position} was solved")

                # After handling, the target should be solved
                # (future: could check and try next source if failed)
                break  # For now, just use the first one

    def _dispatch_to_case_handler(self, l3t:FaceTracker, source_wing: EdgeWing, target_wing: EdgeWing) -> None:
        """Dispatch to appropriate case handler based on source edge position."""
        cube = self.cube
        source_edge = source_wing.parent
        front = cube.front

        if source_edge is front.edge_right:  # FR ✅`with  flip ✅
            self._handle_fr_to_fl(l3t, source_wing, target_wing)
        elif source_edge is front.edge_top:  # FU ✅`no flip
            self._handle_fu_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_bottom:  # FD
            self._handle_fd_to_fl(source_wing, target_wing)
        elif source_edge is front.edge_left:  # FL
            self._handle_fl_to_fl(source_wing, target_wing)
        else:
            from cube.domain.exceptions.InternalSWError import InternalSWError
            raise InternalSWError(f"Unexpected source edge: {source_edge.name}")

        self._assert_all_edges_below_l3_are_ok(l3t.parent)

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
        mapped_si = self.cube.sized_layout.map_wing_index_by_wing(source_wing, target_wing.parent)

        if needs_flip:
            return mapped_si == cube.inv(ti)
        else:
            return mapped_si == ti

    # =========================================================================
    # Case Handlers
    # =========================================================================

    def _handle_fr_to_fl(self, l3t: FaceTracker, source: EdgeWing, target: EdgeWing) -> None:
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
                fu_target = self.cube.sized_layout.map_wing_index_to_edge_name(src_t.slice, EdgeName.FU)
                self._right_cm_prime(
                    source_wing_index=si,
                    target_wing_index=fu_target
                )

                self._asser_more_aggressive_all_other_edges_ok(l3t)

                assert src_t.parent is cube.front.edge_top
                # 3. Check orientation + flip if needed
                flip_alg = self._flip_fu_if_needed(src_t.slice)
                self._asser_more_aggressive_all_other_edges_ok(l3t)

                # 4. Left CM: FU → FL
                si = src_t.slice.index
                self._left_cm(
                    source_wing_index=si,
                    target_wing_index=self.cube.sized_layout.map_wing_index_to_edge_name(src_t.slice, EdgeName.FL)
                )
                self._asser_more_aggressive_all_other_edges_ok(l3t)

                # 5. Rollback
                self.op.play(flip_alg.prime)
                self._asser_more_aggressive_all_other_edges_ok(l3t)
                self.op.play(protect_bu_alg.prime)
                self._asser_more_aggressive_all_other_edges_ok(l3t)

    def _handle_fu_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 2: Source on FU → Target on FL.

        Initial State::

                ┌─────────┐
                │   FU    │
                │   [S]   │  ← Source already on top!
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [T]  │  FRONT  │   ?   │
        └───────┼─────────┼───────┘
                │   FD    │
                │   [H]   │  ← H=Helper
                └─────────┘

        Steps:
        1. protect_bu: FD[H] → BU         (preserves FL/FU)
        2. flip FU if needed              (preserves FL)
        3. Left CM: FU[S] → FL            (work - moves to target)
        4. Rollback: undo flip, undo protect_bu

        Final State::

                ┌─────────┐
                │   FU    │
                │   [H]   │
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [S]  │  FRONT  │   ?   │  ← Source at target! ✓
        └───────┼─────────┼───────┘
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
                    source_wing_index=si,
                    target_wing_index=self.cube.sized_layout.map_wing_index_to_edge_name(src_t.slice, EdgeName.FL)
                )

                # 4. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(protect_bu_alg.prime)

    def _handle_fd_to_fl(self, _source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 3: Source on FD → Target on FL.

        Note: _source is prefixed with underscore because we track it via tracker.
        The source wing moves during rotations, so we use src_t.slice to get
        its current position after each move.

        Initial State::

                ┌─────────┐
                │   FU    │
                │    ?    │
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [T]  │  FRONT  │   ?   │
        └───────┼─────────┼───────┘
                │   FD    │
                │   [S]   │  ← Source on bottom
                └─────────┘

        Algorithm Steps:
        1. F rotation: FD[S] → FL, FL[T] → FU  (source now on FL, target on FU)
        2. protect_bu: FD → BU                 (save FD to BU, FD is now free)
        3. flip_fl_if_needed: fix orientation  (flip source on FL if wrong color facing front)
        4. (Left CM)': FL[S] → FU              (move source from FL to FU via commutator)
        5. Undo flip                           (restore orientation setup)
        6. Undo protect_bu                     (restore BU → FD)
        7. F' rotation: FU[S] → FL             (source arrives at target position!)

        After F rotation (step 1)::

                ┌─────────┐
                │   FU    │
                │   [T]   │  ← Target wing moved here temporarily
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [S]  │  FRONT  │   ?   │  ← Source now here!
        └───────┼─────────┼───────┘
                │   FD    │
                │   [?]   │  ← FD is now FREE
                └─────────┘

        Final State (after F' in step 7)::

                ┌─────────┐
                │   FU    │
                │   [?]   │
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [S]  │  FRONT  │   ?   │  ← Source at target position! ✓
        └───────┼─────────┼───────┘
        """

        with self._logger.tab(f"Case FD→FL: source={_source.parent_name_index_colors_position}, target={target.parent_name_index_position}"):
            # source is moved around !!
            with _source.tracker() as src_t:
                # 1. F rotation - moves source FD → FL, target FL → FU
                self.op.play(Algs.F)

                # 2. Setup: Bring FD to BU (FD is now free, doesn't affect FL/FU)
                protect_bu_alg = self._protect_bu()

                # 5. Check orientation + flip if needed (on FL now)
                flip_alg = self._flip_fl_if_needed(src_t.slice)


                # 3. (Left CM)': FL → FU
                si = src_t.slice.index
                self._left_cm_prime(
                    source_wing_index=si,
                    target_wing_index=self.cube.sized_layout.map_wing_index_to_edge_name(src_t.slice, EdgeName.FU)
                )

                self.op.play(flip_alg.prime)


                # 6. Rollback
                self.op.play(protect_bu_alg.prime)

                # 4. F' - undo F rotation, source goes FU → FL
                self.op.play(Algs.F.prime)



    def _handle_fl_to_fl(self, source: EdgeWing, target: EdgeWing) -> None:
        """
        Case 4: Source on FL → Target on FL (same edge, different index).

        Source is at inv(ti), always needs flip.
        Left CM is a 3-cycle: FU → FL → BU → FU (all use same M[k] slice)

        Initial State::

                ┌─────────┐
                │   FU    │
                │    ?    │
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │[T][S] │  FRONT  │   ?   │  ← Both on same edge!
        │       │         │       │    T at index ti
        └───────┼─────────┼───────┘    S at index inv(ti)
                │   FD    │
                │   [H]   │
                └─────────┘

        Steps:
        1. protect_bu: FD[H] → BU
        2. Left CM (1st): FL[S] → BU       (S leaves FL)
        3. Left CM (2nd): BU[S] → FU       (S now on top)
        4. flip FU (always needed)
        5. Left CM (3rd): FU[S] → FL       (S to target!)
        6. Rollback: undo flip, undo protect_bu

        After Left CM x2::

                ┌─────────┐
                │   FU    │
                │   [S]   │  ← Source now on top!
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [H]  │  FRONT  │   ?   │
        └───────┼─────────┼───────┘

        Final State::

                ┌─────────┐
                │   FU    │
                │   [?]   │
        ┌───────┼─────────┼───────┐
        │  FL   │         │  FR   │
        │  [S]  │  FRONT  │   ?   │  ← Source at target! ✓
        └───────┼─────────┼───────┘
        """
        ti = target.index
        si = source.index

        with self._logger.tab(f"Case FL→FL: source={si}, target={ti}"):
            with source.tracker() as src_t:
                # 1. Setup: Bring FD to BU (doesn't affect FL)
                protect_bu_alg = self._protect_bu()

                # 2. First Left CM: FU(destroying) -> FL → BU -> FU
                # now source  is on BU
                wing_idx = src_t.slice.index
                source_index_on_fu = self.cube.sized_layout.map_wing_index_to_edge_name(src_t.slice, EdgeName.FU)
                target_index_on_fl = self.cube.sized_layout.map_wing_index_by_name(EdgeName.FU, EdgeName.FL, source_index_on_fu)
                self._left_cm(
                    source_wing_index=source_index_on_fu,
                    target_wing_index=target_index_on_fl
                )

                # 3. Second Left CM: FU -> FL -> BU → FU
                # now source is On FU
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_wing_index=source_index_on_fu,
                    target_wing_index=target_index_on_fl
                )

                # 4. Flip FU (always required for this case)
                flip_alg = self._flip_fu()

                # 5. Third Left CM: FU → FL -> BU -> FU
                wing_idx = src_t.slice.index
                self._left_cm(
                    source_wing_index=wing_idx,
                    target_wing_index=self.cube.sized_layout.map_wing_index_to_edge_name(src_t.slice, EdgeName.FL)
                )

                # 6. Rollback
                self.op.play(flip_alg.prime)
                self.op.play(protect_bu_alg.prime)

    # =========================================================================
    # Commutator Algorithms (delegate to E2ECommutator)
    # =========================================================================

    def _left_cm(self, source_wing_index: int, target_wing_index: int) -> None:
        """
        Left Commutator: 3-cycle FU → FL → BU → FU

        FU[source_wing_index] → FL[target_wing_index]

        Delegates to E2ECommutator which handles validation, algorithm, and annotation.

        Args:
            source_wing_index: Wing index on FU (source position)
            target_wing_index: Wing index on FL (target position)
        """
        self._e2e_comm.do_left_commutator(source_wing_index, target_wing_index)

    def _left_cm_prime(self, source_wing_index: int, target_wing_index: int) -> None:
        """
        Left Commutator Inverse: 3-cycle FU → BU → FL → FU
        (Reverse direction: FL → FU)

        FL[source_wing_index] → FU[target_wing_index]

        Delegates to E2ECommutator which handles validation, algorithm, and annotation.

        Args:
            source_wing_index: Wing index on FL (source position)
            target_wing_index: Wing index on FU (target position)
        """
        self._e2e_comm.do_left_commutator_prime(source_wing_index, target_wing_index)

    def _right_cm(self, source_wing_index: int, target_wing_index: int) -> None:
        """
        Right Commutator: 3-cycle FU → FR → BU → FU

        FU[source_wing_index] → FR[target_wing_index]

        Delegates to E2ECommutator which handles validation, algorithm, and annotation.

        Args:
            source_wing_index: Wing index on FU (source position)
            target_wing_index: Wing index on FR (target position)
        """
        self._e2e_comm.do_right_commutator(source_wing_index, target_wing_index)

    def _right_cm_prime(self, source_wing_index: int, target_wing_index: int) -> None:
        """
        Right Commutator Inverse: 3-cycle FU → BU → FR → FU
        (Reverse direction: FR → FU)

        FR[source_wing_index] → FU[target_wing_index]

        Delegates to E2ECommutator which handles validation, algorithm, and annotation.

        Args:
            source_wing_index: Wing index on FR (source position)
            target_wing_index: Wing index on FU (target position)
        """
        self._e2e_comm.do_right_commutator_prime(source_wing_index, target_wing_index)

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

    # Class-level cache for flip_FU algorithm (computed once, reused)
    _FLIP_FU_ALG: Alg | None = None

    @staticmethod
    def _get_flip_fu_alg() -> Alg:
        """
        Get the flip_FU algorithm (cached).

        This algorithm flips the edge wing on FU in place while preserving
        FL and other L3 edges. The algorithm is parsed once and cached at
        class level for performance.

        Returns:
            The flip_FU algorithm.
        """
        if _LBLL3Edges._FLIP_FU_ALG is None:
            _LBLL3Edges._FLIP_FU_ALG = Algs.parse_multiline("""                                                                                                              
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


        return _LBLL3Edges._FLIP_FU_ALG

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

        Uses conjugation with flip_FU algorithm:
            flip_FL = F + flip_FU + F'

        This works because:
        1. F moves FL → FU (wing to flip is now on FU)
        2. flip_FU flips the wing in place
        3. F' moves FU → FL (flipped wing back to original position)

        Returns:
            The algorithm used (for .prime undo).
        """
        alg = self._get_flip_fl_alg()
        self.op.play(alg)
        return alg

    @staticmethod
    def _get_flip_fl_alg() -> SeqAlg:
        """Build flip_FL algorithm via conjugation: F + flip_FU + F'."""
        return Algs.F + _LBLL3Edges._get_flip_fu_alg() + Algs.F.prime

    def _flip_fl_if_needed(self, source: EdgeWing) -> Alg:
        """
        Flip FL wing if orientation is wrong.

        Checks if the source wing (which must be on FL) has the correct
        L3 color (front face color) facing the front face. If not, flips it.

        Args:
            source: EdgeWing that must be on FL (asserted).

        Returns:
            The flip algorithm if orientation was wrong, Algs.NOOP otherwise.
            Caller can use .prime to undo the flip.
        """
        cube = self.cube

        assert source.parent is cube.front.edge_left, \
            f"source must be on FL, got {source.parent.name}"

        l3_color = cube.front.color

        if source.get_face_edge(cube.front).color != l3_color:
            return self._flip_fl()
        return Algs.NOOP

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

    def _is_edge_solved(self, edge: Edge) -> int:
        """

        Count number of solved edge wings on L3 face.

        Args:
            l3_tracker: Tracker for L3 face (can be anywhere on cube).

        Returns:
            Number of wings with matching colors on L3 edges.
        """
        for wing in edge.all_slices:
            if not wing.match_faces:
                return False

        return True

    def _assert_all_edges_below_l3_are_ok(self, th:FacesTrackerHolder):

        assert self._parent.is_solved_phase_with_tracker(th, SolveStep.LBL_L3_CENTER)

    def _more_aggressive_all_other_edges_ok(self, l3_tracker: FaceTracker) -> Edge | None:

        cube = self.cube

        l3_color = l3_tracker.face.color

        edges: set[Edge] = set()

        e: Edge
        for e in cube.edges:
            s: EdgeWing
            for s in e.all_slices:
                if l3_color not in s.colors:
                    edges.add(e)

        for edge in edges:
            if not edge.is3x3:
                return edge

        return None

    def _asser_more_aggressive_all_other_edges_ok(self, l3_tracker: FaceTracker) -> None:

        assert self._more_aggressive_all_other_edges_ok(l3_tracker) is None

        return None



