# TODO Comments in Source Code

Updated: 2025-12-23 (after cleanup)

This file tracks TODO comments in source code with assigned IDs for better tracking.

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Tracked TODOs (TC1-TC6) | 6 | Need attention |
| Cleaned up | 22 | Removed |

---

## Active TODOs

| ID | File | Line | Type | Priority | Description |
|----|------|------|------|----------|-------------|
| TC1 | `Operator.py` | 149 | Architecture | Low | Move single step mode into operator |
| TC2 | `Face.py` | 246 | Documentation | Medium | Unclear why edge copies needed |
| TC3 | `Slice.py` | 202 | **BUG** | Medium | M slice direction inverted |
| TC4 | `NxNCenters.py` | 860 | Incomplete | Low | MM algorithm broken |
| TC5 | `WebAppWindow.py` | 73 | Feature | Medium | Async animation for web backend |
| TC6 | `CageNxNSolver.py` | 111 | Design | Low | Evaluate advanced_edge_parity flag |

---

## Detailed Descriptions

### TC1 - Architecture: Single Step Mode
**File:** `src/cube/application/commands/Operator.py:149`
```python
# TODO [TC1]: Move single step mode handling into operator
```
- **Type:** Architecture improvement
- **Priority:** Low
- **Action:** Refactor single-step mode to be handled within Operator class

### TC2 - Documentation: Edge Copies in Face Rotation
**File:** `src/cube/domain/model/Face.py:246`
```python
# TODO [TC2]: Unclear why these copies are needed - without them front rotation breaks left face colors
```
- **Type:** Code understanding needed
- **Priority:** Medium
- **Action:** Investigate and document why these edge copies are required

### TC3 - BUG: M Slice Direction
**File:** `src/cube/domain/model/Slice.py:202`
```python
# TODO [TC3]: BUG - M slice direction is inverted compared to standard notation
# See: https://alg.cubing.net/?alg=m and https://ruwix.com/the-rubiks-cube/notation/advanced/
```
- **Type:** Bug workaround
- **Priority:** Medium
- **Action:** Fix the underlying M-slice algorithm to match standard notation

### TC4 - Incomplete: MM Algorithm
**File:** `src/cube/domain/solver/common/big_cube/NxNCenters.py:860`
```python
# TODO [TC4]: MM algorithm broken - needs fix before odd cube face swap can work
raise InternalSWError("Need to fix MM")
```
- **Type:** Incomplete implementation
- **Priority:** Low (function raises error if called)
- **Action:** Fix MM algorithm to complete odd cube face swap feature

### TC5 - Feature: Web Backend Animation
**File:** `src/cube/presentation/gui/backends/web/WebAppWindow.py:73`
```python
# TODO [TC5]: Implement async animation support for web backend
app.op.toggle_animation_on(False)
```
- **Type:** Feature implementation
- **Priority:** Medium (if web backend is used)
- **Action:** Implement async animation compatible with web event loop

### TC6 - Design: Edge Parity Flag
**File:** `src/cube/domain/solver/direct/cage/CageNxNSolver.py:111`
```python
# TODO [TC6]: Consider using advanced_edge_parity=True for cage method
# since we want to preserve edge pairing as much as possible.
```
- **Type:** Design evaluation
- **Priority:** Low
- **Action:** Test if advanced_edge_parity=True improves cage solver results

---

## Cleaned Up (22 items removed 2025-12-23)

| File | Line | Reason |
|------|------|--------|
| `_config.py` | 41 | Was just linter suppression note |
| `Center.py` | 27 | Premature optimization |
| `Corner.py` | 100 | Premature optimization |
| `Cube.py` | 1385 | Premature optimization |
| `Edge.py` | 159 | Not needed - code works |
| `Edge.py` | 188 | Not needed - code works |
| `Edge.py` | 198 | Cleaned up docstring |
| `Edge.py` | 428 | Premature optimization |
| `Face.py` | 241 | Outdated |
| `Face.py` | 254 | Premature optimization |
| `Face.py` | 395 | Premature optimization |
| `Face.py` | 458 | Premature optimization |
| `Part.py` | 60 | Removed validation suggestion |
| `Part.py` | 82 | Not needed |
| `Part.py` | 196 | Confusing debug comment |
| `Slice.py` | 60 | Not needed |
| `_part_slice.py` | 514 | Not needed |
| `SimpleAlg.py` | 27 | Legacy refactor idea |
| `optimizer.py` | 4 | Already fixed |
| `SliceAbleAlg.py` | 161 | Complex edge cases noted |
| `CommonOp.py` | 454 | Not needed |
| `NxNEdges.py` | 370 | Premature optimization |
| `CageNxNSolver.py` | 533 | Outdated (phase done) |
| `_L2.py` | 94 | Premature optimization |
| `_board.py` | 33 | Cleaned up |
| `main_g_mouse.py` | 418 | Premature optimization |

## Dead Code Deleted

| File | Reason |
|------|--------|
| `utils/debug.py` | Entire file deleted - functions never called |

---

## Files Modified (2025-12-23 Cleanup)

| File | Changes |
|------|---------|
| `_config.py` | Removed `TODO: fix` from noqa comment |
| `Center.py` | Removed optimization TODO |
| `Corner.py` | Removed optimization TODO |
| `Cube.py` | Removed optimization TODO |
| `Edge.py` | Removed 4 TODOs, cleaned docstring |
| `Face.py` | Removed 3 optimization TODOs, added TC2 ID |
| `Part.py` | Removed 3 TODOs |
| `Slice.py` | Removed TODO, added TC3 ID |
| `_part_slice.py` | Removed type assertion TODO |
| `SimpleAlg.py` | Removed legacy refactor TODO |
| `optimizer.py` | Removed import comment |
| `SliceAbleAlg.py` | Removed optimization TODO |
| `CommonOp.py` | Removed comment TODO |
| `NxNEdges.py` | Removed optimization TODO |
| `NxNCenters.py` | Added TC4 ID |
| `CageNxNSolver.py` | Updated Phase 2 comment, added TC6 ID |
| `_L2.py` | Removed optimization TODO |
| `_board.py` | Cleaned sequence diagram TODO |
| `main_g_mouse.py` | Removed optimization TODO |
| `Operator.py` | Added TC1 ID |
| `WebAppWindow.py` | Added TC5 ID |
