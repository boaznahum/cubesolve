# Solver TODOs

## Completed Cleanup (2025-12-16)

### Dead code removed:
- Removed `detect_edge_parity()` and `detect_corner_parity()` from:
  - `Solver3x3Protocol` (never called)
  - `BeginnerSolver3x3` (never called)
  - `CFOP3x3` (never called, and would never return True anyway since OLL/PLL silently fix)
  - `Kociemba3x3` (never called, always returned None)
- Removed error-masking fallback code in `NxNSolverOrchestrator` (lines 287-290)
  - Now properly raises `InternalSWError` if edge parity detected twice
- Deleted stale `__branch_state.md` WIP documentation

---

## CFOP parity detection (TODO)

CFOP doesn't detect and raise parity exceptions like BeginnerSolver3x3 does:
- **Edge parity (OLL):** CFOP silently fixes it in `OLL._check_and_do_oll_edge_parity()`
  instead of raising `EvenCubeEdgeParityException`
- **Corner parity (PLL):** Similar issue - CFOP fixes instead of raising
  `EvenCubeCornerSwapException`

For now, the orchestrator uses BeginnerSolver3x3 as the parity detector.
To use CFOP as parity detector, it needs to be modified to raise exceptions
instead of silently fixing parity.

See: `OLL.py` lines 108-126 (`_check_and_do_oll_edge_parity`)

---

## Why `solve` vs `solve_3x3`? (ANSWERED - by design)

| Method | Purpose |
|--------|---------|
| `solve()` | Public API with animation wrapper - what users call |
| `solve_3x3()` | Protocol method for orchestrator - called in query/restore mode |

The orchestrator needs `solve_3x3()` to call the solver in query mode
(with `with_query_restore_state()` context) where animation must be off.
The `solve()` method wraps `solve_3x3()` with animation context management.

Same pattern for `status` vs `status_3x3`:
- `status()` - Solver ABC property, for orchestrator returns reduction + 3x3 status
- `status_3x3()` - Protocol method, returns pure 3x3 layer progress

---

## Why parity detector is needed (ANSWERED)

For solvers that can't detect parity (Kociemba), the orchestrator uses
BeginnerSolver3x3 as a "parity detector" in query mode:
1. Run BeginnerSolver3x3 in `with_query_restore_state()` context
2. If it throws parity exception, catch it and fix parity
3. State is restored, then let actual solver (Kociemba) solve

For solvers that CAN detect parity (BeginnerSolver3x3, CFOP), no detector needed.

---

## Corner parity position assumption (INVESTIGATED - NOT A BUG)

In `NxNSolverOrchestrator`, when using parity detector, the `fix_corner_parity()`
call was thought to assume specific cube orientation.

**Investigation (2025-12-16):** Tested by adding a Y rotation before `fix_corner_parity()`.
Result: The solve still succeeds.

**Why it works:** The corner swap algorithm swaps **diagonal corners** on the U face.
Corner parity just needs ANY diagonal swap to fix it - it doesn't matter which specific
diagonal pair. After Y rotation:
1. Yellow is still up (Y rotates around up axis)
2. Different corners are in R-side positions, so different diagonal pair gets swapped
3. But any diagonal swap flips corner permutation parity from odd to even

**Conclusion:** NOT a bug. The algorithm is robust to Y rotations. The only requirement
is that yellow face stays up, which is always true in L3 position.

---

## Corner swap vs edge parity asymmetry (COMPLETED - 2025-12-16)

The user noted: "why we need different behaviour for corner swap and edge,
it seems that detector can simply raise the exception and reducer can fix it exactly
like in edge parity"

### Unified Pattern (Implemented)

| Parity Type | Who Detects | Who Fixes | Pattern |
|-------------|-------------|-----------|---------|
| **Edge** | L3Cross | Orchestrator → Reducer | Throw → Catch → Fix |
| **Corner** | L3Corners | Orchestrator → Reducer | Throw → Catch → Fix |

Both parities now follow the same consistent pattern:
1. Detector raises exception (L3Cross / L3Corners)
2. Orchestrator catches exception
3. Reducer fixes parity (`fix_edge_parity()` / `fix_corner_parity()`)
4. Re-reduce and retry solve

### Changes Made

1. **L3Corners.py**: Removed `_do_corner_swap()` call before throwing exception
2. **NxNSolverOrchestrator.py**: Always calls `reducer.fix_corner_parity()` when catching exception
3. **Cube.py**: Removed `dont_fix_corner_parity` flag and `with_dont_fix_corner_parity()` context manager

### Benefits Achieved

- Consistent pattern for both parities
- Simpler L3Corners (just detects and throws)
- Eliminated the `dont_fix_corner_parity` flag entirely
- Clearer separation of concerns (detection vs fixing)

---

# new enties

i dont like facades 

class BeginnerReducer(ReducerProtocol):
    """
    Standard NxN to 3x3 reducer using beginner method.

    Reduces an NxN cube (4x4, 5x5, etc.) to a virtual 3x3 by:
    1. Solving centers (grouping center pieces by color)
    2. Solving edges (pairing edge pieces)

    Supports both basic and advanced edge parity algorithms.

    Inherits from ReducerProtocol to satisfy the project's convention
    of implementations inheriting from protocols.
    """

    __slots__ = ["_op", "_solver_facade", "_nxn_centers", "_nxn_edges", "_l3_corners"]

    def __init__(
        self,
        op: OperatorProtocol,
        advanced_edge_parity: bool = False
    ) -> None:
        """
        Create a BeginnerReducer.

        Args:
            op: Operator for cube manipulation
            advanced_edge_parity: If True, use advanced R/L-slice parity algorithm.
                                  If False, use simple M-slice parity algorithm.
        """
        self._op = op

        # Create minimal solver facade for NxNCenters/NxNEdges/L3Corners
        self._solver_facade = _ReducerSolverFacade(op)

        # Import here to avoid circular imports
        from cube.domain.solver.beginner.NxNCenters import NxNCenters
        from cube.domain.solver.beginner.NxNEdges import NxNEdges
        from cube.domain.solver.beginner.L3Corners import L3Corners

        self._nxn_centers = NxNCenters(self._solver_facade)
        self._nxn_edges = NxNEdges(self._solver_facade, advanced_edge_parity)
        self._l3_corners = L3Corners(self._solver_facade)
