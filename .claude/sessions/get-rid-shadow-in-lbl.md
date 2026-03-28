# Get Rid of Shadow Cube in Big LBL Solver

**Branch:** `get-rid-shadow-in-lbl`
**Issue:** #148
**Status:** Not started

## Background: What Was Done in Cage Solver (#145)

The Cage solver used to create a **shadow 3x3 cube** + **DualOperator** to solve corners.
This was eliminated by using the **color provider** pattern instead.

### Before (shadow approach):
```python
# CageNxNSolver._solve_corners() — OLD
shadow_cube = self._shadow_helper.create_shadow_cube_from_faces_and_cube(th)
dual_op = DualOperator(shadow_cube, self._op)
solver_3x3 = Solvers3x3.beginner(dual_op, ...)
solver_3x3.solve_3x3()
```

### After (color provider approach):
```python
# CageNxNSolver._solve_corners() — NEW (current code)
from cube.domain.solver.Solvers3x3 import Solvers3x3

with self._cube.with_faces_color_provider(tracker_holder, center_3x3_mode=True):
    solver_3x3 = Solvers3x3.by_name(solver_name, self._op, self._logger)
    solver_3x3.solve_3x3()
```

### Why it works:
1. `with_faces_color_provider(tracker_holder, center_3x3_mode=True)` sets a color provider on each **Center** (via Face → Center delegation)
2. `Center.color` returns the **tracker-assigned** color instead of reading from center stickers
3. `center_3x3_mode=True` makes `Center.is3x3` short-circuit to `True` — the 3x3 solver sees reduced centers
4. The 3x3 solver only uses **outer face moves** (R, L, U, D, F, B) and **whole cube rotations** — these don't move inner slices, so the color provider stays valid

### Architecture (after cage refactor):
```
Cube.with_faces_color_provider(provider, center_3x3_mode)
  └── ExitStack enters Face.with_color_provider() for each face
        └── Face delegates to Center.with_color_provider()
              └── Center saves/restores _color_provider and _center_3x3_mode

Center.color:
  if _color_provider is not None:
      return _color_provider.get_face_color(self.name)  # tracker color
  else:
      return self.edg().color  # actual sticker color

Center.is3x3:
  if _center_3x3_mode:
      return True  # short-circuit
  # ... normal check: all center slices same color
```

## The Problem in Big LBL Solver

The Big LBL solver (`DirectLayerByLayerNxNSolver`) uses the **same shadow cube pattern** we just removed from the cage solver. It's in **`_solve_layer1_with_shadow()`** (line ~533):

```python
# DirectLayerByLayerNxNSolver._solve_layer1_with_shadow() — CURRENT
shadow_cube = self._shadow_helper.create_shadow_cube_from_faces_and_cube(th)
dual_op = DualOperator(shadow_cube, self._op)
shadow_solver = Solvers3x3.beginner(dual_op, self._logger, forced_start_color=self.cmn.white)
self._run_child_solver(cast(Solver, shadow_solver), what)
```

This is called from 4 places:
- `_solve_layer1_cross(th)` → `_solve_layer1_with_shadow(th, SolveStep.L1x)`
- `_solve_layer1_corners(th)` → `_solve_layer1_with_shadow(th, SolveStep.L1)`
- `_solve_layer3_cross(th)` → `_solve_layer1_with_shadow(th, SolveStep.L3x)`
- `_solve_layer3_corners(th)` → `_solve_layer1_with_shadow(th, SolveStep.L3)`

### Additional Challenge: Edges

In the cage solver, edges are already **fully paired** before corners are solved. So when the color provider is active, `Edge.is3x3` naturally returns `True` for all edges.

In the Big LBL solver, **edges may NOT be paired yet** during L1/L3 solving. The shadow cube handles this by **fixing non-3x3 edges** with fake valid color-pairs (see `ShadowCubeHelper` lines 73-77):

```python
# ShadowCubeHelper — fixes un-paired edges on shadow cube
if self._cube.is_even and fix_non_3x3_edges:
    modified = modified.with_fixed_non_3x3_edges(
        cube=self._cube,
        reference_scheme=self._cube.original_scheme
    )
```

So eliminating the shadow cube in Big LBL requires **also providing edge colors** to make `Edge.is3x3` return `True`.

## Proposed Solution

Extend the `with_faces_color_provider` context manager on `Cube` to also accept an **optional edge color provider** and an **edge_3x3_mode** flag, following the same pattern as centers.

### Step 1: Add edge_3x3_mode to Edge (like center_3x3_mode on Center)

```python
# Edge.py — add fields + context manager (same pattern as Center)
class Edge(Part):
    __slots__ = (..., "_edge_3x3_mode")

    def __init__(self, ...):
        ...
        self._edge_3x3_mode: bool = False

    @property
    def is3x3(self) -> bool:
        if self._edge_3x3_mode:
            return True  # short-circuit, same as Center
        # ... existing check

    @contextmanager
    def with_edge_3x3_mode(self, mode: bool) -> Generator[None, None, None]:
        prev = self._edge_3x3_mode
        self._edge_3x3_mode = mode
        try:
            yield
        finally:
            self._edge_3x3_mode = prev
```

### Step 2: Extend Cube.with_faces_color_provider

Add optional `edge_3x3_mode` parameter:

```python
# Cube.py
@contextmanager
def with_faces_color_provider(
    self,
    provider: "FacesColorsProvider",
    center_3x3_mode: bool = False,
    edge_3x3_mode: bool = False,    # NEW
) -> Generator[None, None, None]:
    with ExitStack() as stack:
        for f in self.faces:
            stack.enter_context(f.with_color_provider(provider, center_3x3_mode))
        if edge_3x3_mode:
            for e in self.edges:
                stack.enter_context(e.with_edge_3x3_mode(True))
        self.reset_after_faces_changes()
        yield
    self.reset_after_faces_changes()
```

### Step 3: Replace shadow cube in Big LBL

```python
# DirectLayerByLayerNxNSolver — NEW
def _solve_layer1_with_color_provider(self, th: FacesTrackerHolder, what: SolveStep) -> None:
    from cube.domain.solver.Solvers3x3 import Solvers3x3

    with self._cube.with_faces_color_provider(th, center_3x3_mode=True, edge_3x3_mode=True):
        solver_3x3 = Solvers3x3.beginner(self._op, self._logger, forced_start_color=self.cmn.white)
        self._run_child_solver(cast(Solver, solver_3x3), what)
```

### Step 4: Verify and clean up

- Run all solver tests (especially Big LBL with sizes 2-8)
- Remove `_solve_layer1_with_shadow` method
- Check if `ShadowCubeHelper` and `DualOperator` can be removed entirely (or if other code still uses them)

## Key Files to Modify

| File | Change |
|------|--------|
| `src/cube/domain/model/Edge.py` | Add `_edge_3x3_mode`, `with_edge_3x3_mode()` context manager, short-circuit in `is3x3` |
| `src/cube/domain/model/Cube.py` | Add `edge_3x3_mode` param to `with_faces_color_provider` |
| `src/cube/domain/solver/direct/lbl/DirectLayerByLayerNxNSolver.py` | Replace `_solve_layer1_with_shadow` with color provider approach |

## Key Files to Read First

- `src/cube/domain/solver/direct/cage/CageNxNSolver.py:425-457` — reference implementation (cage solver, working)
- `src/cube/domain/solver/direct/lbl/DirectLayerByLayerNxNSolver.py:533-595` — current shadow approach (to replace)
- `src/cube/domain/model/Center.py:52-56,138-150` — `center_3x3_mode` pattern to copy for Edge
- `src/cube/domain/model/Edge.py:85-116` — current `is3x3` to add short-circuit

## Important Notes

- The `forced_start_color=self.cmn.white` parameter is important — without it the beginner solver may pick a different face. Keep this.
- The Big LBL solver calls `_run_child_solver(cast(Solver, shadow_solver), what)` with a `SolveStep` — the new approach should preserve this (solve only L1x, L1, L3x, or L3, not the whole cube).
- WORKAROUND (#147): Even cubes may need beginner solver instead of CFOP (same as cage solver).
- Don't forget to handle the `forced_start_color` parameter — when using the color provider, the solver operates on the **real cube**, so `self.cmn.white` should already be correct.