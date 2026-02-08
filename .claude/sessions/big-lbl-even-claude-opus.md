# Big LBL Even Cube Support - Session Notes

## Branch: `big-lbl-even-claude-opus`

## Goal
Add even cube (4x4, 6x6, 8x8) support to the Big LBL solver. On even cubes, there is no fixed center piece, so `Face.color` is unreliable during solving.

## Solution Architecture
1. **FacesColorsProvider** protocol — overrides `Face.color` with tracker-assigned colors
2. **Cube.with_faces_color_provider()** context manager — sets provider on all 6 faces
3. **FacesTrackerHolder** already implements `get_face_color()` — now explicitly inherits `FacesColorsProvider`
4. **Wired in LBL solver** — `_solve_impl2` wraps solve body with both `FacesTrackerHolder` and `with_faces_color_provider`
5. **Fixed `_create_f5_pred`** — replaced recalculating BOY predicate with one-time BOY check + MarkedFaceTracker
6. **Commutator wrapping** — `preserve_physical_faces()` around commutator calls to restore tracker markers

## Files Modified
| File | Change |
|------|--------|
| `src/cube/domain/model/FacesColorsProvider.py` | **NEW** — Protocol with `get_face_color()` |
| `src/cube/domain/model/Face.py` | Added `_color_provider` support to `color` property |
| `src/cube/domain/model/Cube.py` | Added `with_faces_color_provider()` context manager |
| `src/cube/domain/tracker/FacesTrackerHolder.py` | Inherits `FacesColorsProvider` |
| `src/cube/domain/tracker/_factory.py` | Replaced `_create_f5_pred` with `_create_tracker_on_face` + one-time BOY check |
| `src/cube/domain/solver/common/big_cube/NxNCenters.py` | Added `tracker_holder` param + `_preserve_trackers()` + `_execute_commutator()` |
| `src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py` | Added required `tracker_holder` + wrapped commutator calls |
| `src/cube/domain/solver/direct/lbl/_LBLSlices.py` | Changed to `_create_centers(th)` on demand instead of field |
| `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` | Pass `tracker_holder=th` to NxNCenters |
| `tests/solvers/wip/big_lbl/test_lbl_big_cube_solver.py` | Changed `test_lbl_slices_ctr` to `CUBE_SIZES_ALL` |

## Current Status
- **L1 Centers on 4x4: ALL 14 PASSED** (14/14)
- L1 Centers on odd cubes: still passing
- L2 Slices on even cubes: NOT YET TESTED (likely will hit separate NxNEdges edge-counting bug)
- Static checks: ruff passes on modified files

## Pending
- User review of all changes
- Run full L2 slices test on even cubes (will likely reveal NxNEdges bug)
- Run full check suite (ruff, mypy, pyright, all tests)
- Fix NxNEdges edge-counting bug for even cubes (separate issue)
- Commit after user approval
