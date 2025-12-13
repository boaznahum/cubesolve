# Branch: abstract-reducer - Current State

## Summary

This branch implements the **Reducer + Orchestrator pattern** for NxN cube solving, separating:
- **Reducer**: NxN → 3x3 reduction (centers + edges)
- **3x3 Solver**: Pure 3x3 solving (L1, L2, L3)
- **Orchestrator**: Composes reducer + solver, handles parity

## Recent Commits (Solver-Related)

1. `ac401e6` - Add with_query_restore_state context manager for parity detection
2. `efb7043` - Add Reducer Protocol and Orchestrator pattern for NxN solving
3. `9e4977e` - Add comprehensive solver test suite
4. `94e13d8` - Add Kociemba near-optimal solver with dynamic color mapping

## Current Architecture

```
NxNSolverOrchestrator
    ├── ReducerProtocol (NxN → 3x3)
    │   └── NxNReducer (implementation)
    └── Solver3x3Protocol (pure 3x3 solving)
        ├── BeginnerSolver3x3
        ├── CFOP3x3
        └── Kociemba3x3
```

## What's Done

### 1. Reducer Protocol (`src/cube/domain/solver/protocols/ReducerProtocol.py`)
- `reduce()` - Full reduction (centers + edges)
- `solve_centers()` - Just centers
- `is_reduced()` - Check if cube is reduced to 3x3
- `fix_edge_parity()` - Fix OLL parity algorithm

### 2. Solver3x3Protocol (`src/cube/domain/solver/protocols/Solver3x3Protocol.py`)
- `solve_3x3()` - Pure 3x3 solving
- `is_solved` - Check if solved
- `status_3x3` - Human-readable status
- `detect_edge_parity()` - Detect OLL parity (WIP - to be removed)
- `detect_corner_parity()` - Detect PLL parity (WIP - to be removed)

### 3. NxNSolverOrchestrator (`src/cube/domain/solver/NxNSolverOrchestrator.py`)
- Composes reducer + 3x3 solver
- Handles parity exceptions with retry loop
- Current parity detection uses helper solver (messy)

### 4. Query Mode Infrastructure (Just Added)
- Renamed `_skip_texture_updates` → `_in_query_mode` (supports nesting)
- Added `with_query_restore_state()` context manager to Operator
- Tests in `tests/solvers/test_query_restore_state.py` (5 passing)

## What's In Progress (WIP)

### Parity Detection Redesign

**Current (messy):**
- `detect_edge_parity()` and `detect_corner_parity()` on Solver3x3Protocol
- Each solver must implement these methods (returns None if can't)
- Orchestrator creates helper BeginnerSolver3x3 for solvers that can't detect

**Target design (cleaner):**
- Solver just declares `can_handle_parity() -> bool`
- If True: solver handles parity via exceptions (Beginner, CFOP)
- If False: orchestrator owns parity detection:
  1. Use `with_query_restore_state()` context
  2. Create CFOP3x3, solve L1+L2
  3. Count oriented edges (1 or 3 = edge parity)
  4. Exit context (auto-rollback)
  5. Apply OLL parity fix if needed
  6. Repeat for corner parity (after L3 cross)
  7. Let solver finish

## Files Modified (Staged/Committed)

### Core Query Mode:
- `src/cube/domain/model/Cube.py` - `_in_query_mode` flag
- `src/cube/domain/model/CubeQueries2.py` - nesting support in rotate_and_check
- `src/cube/domain/model/Face.py` - check `_in_query_mode`
- `src/cube/domain/model/Slice.py` - check `_in_query_mode`
- `src/cube/application/commands/Operator.py` - `with_query_restore_state()`
- `src/cube/domain/solver/protocols/OperatorProtocol.py` - protocol signature

### Solver Files (WIP - parity redesign pending):
- `src/cube/domain/solver/protocols/Solver3x3Protocol.py`
- `src/cube/domain/solver/NxNSolverOrchestrator.py`
- `src/cube/domain/solver/beginner/BeginnerSolver3x3.py`
- `src/cube/domain/solver/CFOP/CFOP3x3.py`
- `src/cube/domain/solver/kociemba/Kociemba3x3.py`

## How to Continue

### Step 1: Update Solver3x3Protocol
```python
# Replace detect_edge_parity() and detect_corner_parity() with:
def can_handle_parity(self) -> bool:
    """True = handles parity via exceptions, False = needs orchestrator help."""
    ...
```

### Step 2: Update Each Solver
- `BeginnerSolver3x3.can_handle_parity()` → `True` (uses exceptions)
- `CFOP3x3.can_handle_parity()` → `True` (uses exceptions)
- `Kociemba3x3.can_handle_parity()` → `False` (can't detect, needs help)

### Step 3: Move Parity Detection to Orchestrator
```python
def _detect_and_fix_parity(self):
    if self._solver_3x3.can_handle_parity():
        return  # Solver handles it

    # Orchestrator detects edge parity
    with self._op.with_query_restore_state():
        cfop = CFOP3x3(self._op)
        cfop.l1_cross.solve()
        cfop.l1_corners.solve()
        cfop.l2.solve()
        has_edge_parity = self._count_oriented_edges() in (1, 3)

    if has_edge_parity:
        self._reducer.fix_edge_parity()

    # Detect corner parity (must re-check after edge fix!)
    with self._op.with_query_restore_state():
        cfop = CFOP3x3(self._op)
        cfop.l1_cross.solve()
        cfop.l1_corners.solve()
        cfop.l2.solve()
        cfop.l3_cross.solve()
        has_corner_parity = self._count_positioned_corners() == 2

    if has_corner_parity:
        self._fix_corner_parity()
```

### Step 4: Implement Counting Methods
- `_count_oriented_edges()` - count yellow edges facing up on top face
- `_count_positioned_corners()` - count corners in correct position

### Step 5: Test
```bash
.venv\Scripts\python.exe -m pytest tests/solvers/ -v
```

## Key Design Decisions

1. **Orchestrator owns parity detection** for solvers that can't handle it
2. **Query mode** via `with_query_restore_state()` for stateless detection
3. **CFOP3x3** used as helper for L1+L2 solving during detection
4. **Edge parity checked first**, then corner (since edge fix can affect corners)

## Running Tests

```bash
# All solver tests
.venv\Scripts\python.exe -m pytest tests/solvers/ -v

# Just query restore state tests
.venv\Scripts\python.exe -m pytest tests/solvers/test_query_restore_state.py -v

# All tests (non-GUI)
.venv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/gui -m "not slow"
```
