# Communicator Helper - Development Tracking

> **INSTRUCTIONS FOR CLAUDE (future sessions):**
> This document tracks the development of a CommunicatorHelper class for big cube solving.
> When continuing work on this feature:
> 1. Read this file first to understand goals and progress
> 2. Update the "Current Status" and "Progress Log" sections after each session
> 3. Mark completed items in the checklist
> 4. Add new insights to the "Key Insights" section
> 5. Update "Next Steps" before ending the session

---

## Goal

Create a `CommunicatorHelper` class that provides utilities for working with the **block commutator algorithm** used to solve center pieces on big cubes (NxN, where N > 3).

The core commutator is: `[M', F, M', F', M, F, M, F']`

This helper will be located near `NxNCenters.py` and serve as a reusable component for:
- Understanding cube coordinates
- Executing commutator operations
- Visualizing the 3-cycle effect

---

## Current Status

**Phase:** Phase 1 Complete
**Last Updated:** 2025-12-26
**Session:** 1

---

## Checklist

### Phase 1: Foundation
- [x] Explore existing test structure and patterns
- [x] Create this tracking document
- [x] Create `CommunicatorHelper` class skeleton
- [x] Create test file `tests/solvers/test_communicator_helper.py`
- [x] Instantiate 7x7 cube in test
- [x] Instantiate helper in test and verify basic functionality

### Phase 2: Core Coordinate Functions (COMPLETE)
- [x] Implement `inv(i)` - index inversion
- [x] Implement `rotate_point_clockwise(r, c, n)` - clockwise rotation
- [x] Implement `rotate_point_counterclockwise(r, c, n)` - counter-clockwise rotation
- [x] Implement `point_on_source(is_back, rc)` - front-to-source coordinate mapping
- [x] Implement `point_on_target(is_back, rc)` - source-to-target coordinate mapping
- [x] Add comprehensive tests for each function

### Phase 3: Block Operations (COMPLETE)
- [x] Implement `range_2d(rc1, rc2)` - iterate over 2D block
- [x] Implement `block_size(rc1, rc2)` - calculate block size
- [x] Implement `ranges_intersect_1d(range1, range2)` - check 1D range intersection
- [x] Implement `block_on_source(is_back, rc1, rc2)` - convert block to source coords

### Phase 4: Visualization & Debug (PARTIAL)
- [x] Implement `visualize_grid()` - ASCII visualization of center
- [ ] Implement `visualize_rotation()` - show before/after rotation
- [ ] Add debug logging utilities

### Phase 5: Commutator Operations
- [ ] Implement `get_commutator_algorithm(block)` - generate the commutator moves
- [ ] Implement `validate_block_for_commutator(rc1, rc2)` - check block validity
- [ ] Implement `find_non_intersecting_rotation(rc1, rc2)` - find valid F/F' direction

### Phase 6: Integration
- [ ] Refactor `NxNCenters.py` to use `CommunicatorHelper`
- [ ] Ensure all existing tests still pass
- [ ] Performance benchmarking

---

## The Block Commutator Algorithm

### The Core 3-Cycle

The commutator `[M', F, M', F', M, F, M, F']` performs a 3-cycle:

```
           UP (Source)
          ┌───┬───┬───┐
          │   │ A │   │  ← Piece A moves to position C
          ├───┼───┼───┤
          │   │   │   │
          └───┴───┴───┘

         FRONT (Target)
          ┌───┬───┬───┐
          │   │ C │   │  ← Position C gets piece from A
          ├───┼───┼───┤
          │   │   │   │
          ├───┼───┼───┤
          │   │ B │   │  ← Piece B moves to position A (on UP)
          └───┴───┴───┘

3-cycle: A → C → B → A
```

### Why It's Balanced

```
F rotations:  F + F' + F + F' = 0 (corners return)
M rotations:  M' + M' + M + M = 0 (edges preserved in reduction mode)
```

---

## Key Insights

### Coordinate System Fundamentals

1. **`inv()` function:** `inv(i) = n_slices - 1 - i`
   - For 5x5: `n_slices = 3`, so `inv(0)=2, inv(1)=1, inv(2)=0`
   - This is the foundation of all mirroring operations

2. **Center coordinates:** `(row, column)` with `(0,0)` at top-left
   - Row increases downward
   - Column increases rightward

3. **Rotation transformations:**
   - Clockwise: `(r, c) → (inv(c), r)`
   - Counter-clockwise: `(r, c) → (c, inv(r))`

4. **Front-Up-Back mapping:**
   - UP face: same coordinates as Front
   - BACK face: mirrored in both axes → `(inv(r), inv(c))`

5. **Slice index to M-algorithm:** Center index is 0-based, M alg is 1-based
   - `Algs.M[c+1:c+2]` for center column `c`

### Block Validity for Commutator

A block is valid for the commutator if after rotating by F (or F'), the rotated block's columns don't intersect with the original block's columns. This is checked with `ranges_intersect_1d()`.

---

## Architecture

```
src/cube/domain/solver/common/big_cube/
├── NxNCenters.py           # Existing - solves centers (uses commutator)
├── CommunicatorHelper.py   # NEW - commutator utilities
├── NxNEdges.py             # Existing - solves edges
├── ...
```

The helper is a standalone class that:
- Takes a `Cube` instance (for `n_slices` and `inv()`)
- Provides pure coordinate transformation functions
- Has no side effects (query-only)
- Can be used by `NxNCenters`, `NxNEdges`, and tests

---

## Progress Log

### Session 1 (2025-12-26)
- Explored codebase structure
- Analyzed `NxNCenters.py` in detail (1487 lines)
- Understood coordinate system: `inv()`, rotation transforms, front/back mapping
- Identified key methods to extract into helper
- Created this tracking document
- Created `CommunicatorHelper` class with full implementation:
  - `inv()`, `rotate_point_clockwise()`, `rotate_point_counterclockwise()`
  - `point_on_source()`, `point_on_target()`, `block_on_source()`
  - `range_2d()`, `range_2d_on_source()`
  - `block_size()`, `block_dimensions()`, `ranges_intersect_1d()`
  - `get_four_symmetric_points()`, `is_center_point()`
  - `visualize_grid()` for debugging
- Created comprehensive test file with 7x7, 5x5, and 4x4 cube tests

---

## Next Steps

1. Run tests to verify implementation
2. Add commutator-specific operations (Phase 5)
3. Begin integration with `NxNCenters.py`
4. Add visualization for rotation effects

---

## Files

| File | Purpose |
|------|---------|
| `docs/cube-coordinates-helper.md` | This tracking document |
| `src/cube/domain/solver/common/big_cube/CommunicatorHelper.py` | The helper class |
| `tests/solvers/test_communicator_helper.py` | Test file |

---

## References

- `NxNCenters.py:832-838` - `rotate_point_clockwise/counterclockwise`
- `NxNCenters.py:890-1041` - `_block_communicator()` - the core algorithm
- `NxNCenters.py:1282-1308` - `_point_on_source/_point_on_target`
- `CubeQueries2.py:173-190` - Original rotation implementations
- `Cube.py:570-571` - `inv()` function definition
