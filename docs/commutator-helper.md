# Commutator Helper - Development Tracking

> **INSTRUCTIONS FOR CLAUDE (future sessions):**
> This document tracks the development of a CommutatorHelper class for big cube solving.
> When continuing work on this feature:
> 1. Read this file first to understand goals and progress
> 2. Update the "Current Status" and "Progress Log" sections after each session
> 3. Mark completed items in the checklist
> 4. Add new insights to the "Key Insights" section
> 5. Update "Next Steps" before ending the session
> 6. **COMMIT AND PUSH FREQUENTLY** after each progress step

---

## Goal

Create a `CommutatorHelper` class that provides utilities for working with the **block commutator algorithm** used to solve center pieces on big cubes (NxN, where N > 3).

The core commutator is: `[M', F, M', F', M, F, M, F']`

---

## User Instructions (Session 2)

### Key Differences: Old vs New Helper

| Aspect | Old (NxNCenters) | New (CommutatorHelper) |
|--------|------------------|--------------------------|
| Target face | Front only | Any face |
| Source face | Up or Back only | Any face (different from target) |
| Coordinate system | Row-column, (0,0) at top-left | **Bottom-up, Left-to-right** |
| Face positioning | Positions faces first, then executes | **NO face positioning** - this is the challenge |
| Cage preservation | Optional via `preserve_cage` flag | Optional - preserves cube state |

### New Helper Requirements

1. **Method signature**: Accepts `source: Face` and `target: Face`
2. **Block specification**:
   - Block on source and destination
   - If source block not given, assumes same coordinates as target block
3. **No face positioning**: The helper does the commutator WITHOUT first rotating to position faces - this is the core challenge
4. **Cage preservation**: If requested, preserve cube state (faces and edges return to original position)
5. **Coordinate system**: **Bottom-up, Left-to-right** - this is important!
6. **Rotation mapping**: If source block cannot be mapped to target block by 0..3 rotations, throw exception

### Test Structure

```python
for source_face in all_cube_faces:
    for target_face in all_cube_faces:
        if source_face == target_face:
            continue

        for y in all_slices:  # bottom-up, left-right
            for x in all_slices:
                for rotation in range(4):  # 4 possible source locations
                    # Get source position by rotating target position
                    sy, sx = rotate_point_clockwise((y, x), rotation)

                    # Block size = 1 (extend later)

                    # Using translation from BULR system to face index:
                    # Put random attribute on source piece (key and value random)

                    # Call the helper

                    # Verify:
                    # 1. New attribute is on target block
                    # 2. Attribute is NO LONGER on source
                    # 3. Cube state is preserved (all edges are 3x3 and in position)
```

### Key Points

- The new helper supports **everything** - any source to any target
- Block coordinates use **bottom-up, left-to-right** coordinate system
- Can copy methods from old helper (`NxNCenters`) as starting point
- There are existing methods to check if edges are in position and cube state preserved

---

## Current Status

**Phase:** Session 5 - ALL 5 sources → Front implemented and working!
**Last Updated:** 2025-12-26
**Session:** 5

---

## Checklist

### Phase 1: Foundation (COMPLETE)
- [x] Explore existing test structure and patterns
- [x] Create this tracking document
- [x] Create `CommutatorHelper` class skeleton
- [x] Create test file `tests/solvers/test_commutator_helper.py`
- [x] Instantiate 7x7 cube in test
- [x] Instantiate helper in test and verify basic functionality

### Phase 2: Understand Coordinate Systems (COMPLETE)
- [x] Study bottom-up, left-to-right coordinate system in existing code
- [x] Understand how to translate BULR to face index
- [x] Document coordinate transformation formulas

### Phase 3: Core Helper Methods (COMPLETE)
- [x] Implement coordinate translation: LTR <-> face index
- [x] Implement rotation point mapping: rotate_ltr_point()
- [x] Implement get_expected_source_ltr() for face pair mapping
- [x] Helper handles all coordinate translations internally

### Phase 4: Commutator Implementation (COMPLETE for Front target)
- [x] Implement main commutator method with LTR coordinates
- [x] Handle Up→Front and Back→Front pairs
- [x] Handle Down→Front pair
- [x] Handle Left→Front and Right→Front pairs (E-based algorithm)
- [x] Validate block can be mapped with 0-3 rotations
- [x] Implement cage preservation option
- [x] All 5 sources → Front working (Up, Down, Back, Left, Right)
- [ ] Handle remaining 25 face pair combinations (other targets)

### Phase 5: Comprehensive Tests (COMPLETE)
- [x] Test iterating all source faces
- [x] Test iterating all target faces
- [x] Test all slice positions (y, x in BULR system)
- [x] Test all 4 rotation positions on source
- [x] Verify attribute moves from source to target
- [x] Verify cube state preserved (edges in position)
- [x] Run tests and verify they fail (helper not implemented)

### Phase 6: Integration
- [ ] Ensure all existing tests still pass
- [ ] Optional: Refactor `NxNCenters.py` to use `CommutatorHelper`

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

### Old Coordinate System (NxNCenters)

1. **`inv()` function:** `inv(i) = n_slices - 1 - i`
2. **Center coordinates:** `(row, column)` with `(0,0)` at top-left
   - Row increases downward
   - Column increases rightward

### New Coordinate System (CommutatorHelper)

**Bottom-Up, Left-to-Right (BULR):**
- `(0,0)` is at **bottom-left**
- Y increases **upward**
- X increases **rightward**

Reference: See `docs/design2/face-slice-rotation.md` for detailed diagrams showing row 0 at bottom.

### Coordinate Translation Methods (CubeQueries2.py:173-190)

```python
# Rotate point clockwise n times: (r, c) -> (inv(c), r)
cube.cqr.rotate_point_clockwise(rc, n)

# Rotate point counter-clockwise n times: (r, c) -> (c, inv(r))
cube.cqr.rotate_point_counterclockwise(rc, n)

# Get all 4 symmetric center points
cube.cqr.get_four_center_points(r, c)
```

**Old helper usage** (NxNCenters._search_block:1461-1466):
```python
# Search for matching block by trying 4 rotations
for n in range(4):
    if self._is_block(source_face, ...):
        return (-n) % 4  # How many rotations needed
    rc1 = cube.cqr.rotate_point_clockwise(rc1)
    rc2 = cube.cqr.rotate_point_clockwise(rc2)
```

### LTR to Center Index Translation

**Key Insight:** Use edge methods to translate between LTR and center index coordinates!

- **edge_left** → translates Y (ltr_y ↔ idx_row)
- **edge_bottom** → translates X (ltr_x ↔ idx_col)

```python
def ltr_to_center_index(face: Face, ltr_y: int, ltr_x: int) -> tuple[int, int]:
  """Translate LTR (y, x) to center index (row, col)."""
  idx_row = face.edge_left.get_edge_slice_index_from_face_ltr_index(face, ltr_y)
  idx_col = face.edge_bottom.get_edge_slice_index_from_face_ltr_index(face, ltr_x)
  return idx_row, idx_col


def center_index_to_ltr(face: Face, idx_row: int, idx_col: int) -> tuple[int, int]:
  """Translate center index (row, col) to LTR (y, x)."""
  ltr_y = face.edge_left.get_face_ltr_index_from_edge_slice_index(face, idx_row)
  ltr_x = face.edge_bottom.get_face_ltr_index_from_edge_slice_index(face, idx_col)
  return ltr_y, ltr_x
```

Reference: `Edge.py:127-191` for the `get_ltr_index_from_slice_index` / `get_slice_index_from_ltr_index` methods.

### Attribute System

To set/get attributes on center pieces that move with the color:
```python
part_edge = face.center.get_center_slice((idx_row, idx_col))
part_edge.c_attributes["test_key"] = value  # Moves with color during rotation
```

### State Checking Methods

From `CageNxNSolver.py`:
```python
# Check if edges are reduced (3x3)
all(e.is3x3 for e in cube.edges)

# Check if edges are in correct position
all(e.match_faces for e in cube.edges)

# Check if corners are in correct position
all(corner.match_faces for corner in cube.corners)
```

### Face Pair Handling

The old helper only handled:
- Front (target) ← Up (source): same coordinates
- Front (target) ← Back (source): mirrored both axes

The new helper must handle ALL 30 face pairs (6 faces × 5 other faces).

---

## Architecture

```
src/cube/domain/solver/common/big_cube/
├── NxNCenters.py           # Old - solves centers (uses commutator)
├── CommutatorHelper.py   # NEW - general commutator utilities
├── NxNEdges.py             # Existing - solves edges
├── ...
```

The helper is a standalone class that:
- Takes a `Cube` instance
- Accepts any source and target Face
- Uses BULR coordinate system
- Performs commutator WITHOUT positioning faces first
- Optionally preserves cage (cube state)

---

## Progress Log

### Session 1 (2025-12-26)
- Explored codebase structure
- Analyzed `NxNCenters.py` in detail (1487 lines)
- Created tracking document
- Created `CommutatorHelper` class skeleton
- Created basic test file

### Session 2 (2025-12-26)
- Received detailed user instructions for new helper requirements
- Key insight: New helper supports ANY source/target face pair
- Key insight: Uses Bottom-Up Left-Right coordinate system
- Key insight: NO face positioning - this is the challenge
- Documented coordinate translation methods from CubeQueries2
- Documented rotation usage from old helper (_search_block pattern)
- **Wrote comprehensive test** `test_commutator_all_face_pairs`:
  - Iterates all 30 face pairs (6×5)
  - Tests all (y, x) positions in LTR coordinates
  - Tests all 4 rotations for source positions
  - Sets unique c_attribute on source, verifies it moves to target
  - Verifies cube state preserved (edges/corners in position)
- Test calls `helper.do_commutator()` which needs to be implemented
- **Key discovery: LTR ↔ Index translation using edge methods!**
  - Use `edge_left` for Y translation
  - Use `edge_bottom` for X translation
  - This leverages existing `get_slice_index_from_ltr_index` / `get_ltr_index_from_slice_index`
- Updated helper to extend `SolverHelper` (standard pattern)
- Updated test to use `cube.faces` iterator instead of custom function
- Added clear variable naming: `ltr_y`, `ltr_x`, `idx_row`, `idx_col`

### Session 3 (2025-12-26)
- **Added helper announcement methods**:
  - `get_supported_pairs()` - returns list of (source, target) face pairs
  - `is_supported(source, target)` - checks if a specific pair is supported
- **Implemented do_commutator() for Up→Front and Back→Front**:
  - Full LTR coordinate support - helper handles all translations internally
  - Added `ltr_to_index()` and `index_to_ltr()` translation methods
  - Added `rotate_ltr_point()` for rotating LTR coordinates
  - Added `get_expected_source_ltr()` for computing source positions
  - Implements the block commutator algorithm: [M', F, M', F', M, F, M, F']
  - Handles cage preservation (undo source rotation after commutator)
- **Key insight: Center position is invariant for odd cubes**
  - Position (mid, mid) can't be moved by the commutator
  - Test skips center positions using `_is_center_position()` helper
- **All tests pass**:
  - ✅ `test_create_helper[5,7]` - PASSED
  - ✅ `test_commutator_supported_pairs[5,7]` - PASSED (all positions, all rotations)
  - ✅ `test_commutator_simple_case[5]` - PASSED
- Updated class docstring to document LTR coordinate API

### Session 4 (2025-12-26)
- **Implemented Down→Front support**:
  - Algorithm: Swap M↔M' → [M, F, M, F', M', F, M', F']
  - Coordinate mapping: Identity (same as Up)
  - Refactored `_point_on_source_idx` to accept `source: Face` instead of `is_back: bool`
- **Debugging approach**: Instead of guessing coordinate mappings, traced where attributes actually move
- **All tests pass** for Up→Front, Back→Front, and Down→Front (3 out of 30 pairs implemented)
- **Visual debugging**: Added console display to show markers moving between faces

### Session 5 (2025-12-26)
- **Implemented Left→Front and Right→Front support**:
  - Uses E slice instead of M slice (E moves L→F→R→B)
  - Added `_get_slice_e_alg()` method for E slice algorithms
  - E-based algorithm: [E, F, E, F', E', F, E', F'] for Left→Front
  - Right→Front: Swap E↔E' (analogous to Down vs Up)
  - Row intersection check instead of column intersection (E operates on rows)
  - Coordinate mapping: Identity for both Left and Right
- **Key insight: Pattern between M and E algorithms**:
  - M slice (vertical) uses columns for intersection check
  - E slice (horizontal) uses rows for intersection check
  - Both share same algorithm structure, just different slice type
- **All 5 sources → Front now working!**:
  - ✅ Up→Front (M-based)
  - ✅ Down→Front (M-based, inverted)
  - ✅ Back→Front (M-based, doubled)
  - ✅ Left→Front (E-based)
  - ✅ Right→Front (E-based, inverted)
- **All tests pass** for 5x5 and 7x7 cubes with all positions and rotations

## Known Bugs

### BUG: `cube.reset()` invalidates helper face references
After calling `cube.reset()`, the helper's `is_supported()` check fails because face object references change.

**Workaround**: Create a fresh cube/helper instead of using `cube.reset()`. Or re-fetch faces from cube after reset.

**To clear attributes without reset**, iterate all pieces:
```python
for face in cube.faces:
    for y in range(n_slices):
        for x in range(n_slices):
            idx = helper.ltr_to_index(face, y, x)
            cs = face.center.get_center_slice(idx)
            cs.edge.c_attributes.clear()
```

---

## Open Questions

### Q1: Why does rotation matter between LTR and Index coordinate systems?

When rotating a point to find the source position, we must go through Index space:
```
LTR(face) → Index(face) → rotate in Index → Index(face) → LTR(face)
```

We cannot rotate directly in LTR space because:
- Each face has a different LTR↔Index mapping
- For Front: LTR (y,x) ≈ Index (y,x)
- For Up: LTR (0,0) → Index (n-1, 0) on NxN cube (Y-axis relationship differs)

The physical rotation happens in Index space (how slices actually move on the cube).
The LTR coordinates are a user-facing abstraction that differs per face.

**TODO**: Investigate if there's a mathematical relationship that allows direct LTR rotation without going through Index space.

### Q2: How to transform algorithms for other face pairs (Down→Front, Left→Right, etc.)?

The commutator algorithm [M', F, M', F', M, F, M, F'] is designed for Up→Front.

Key insights from research:
- Cube rotations: x (around R axis), y (around U axis), z (around F axis)
- Slice relation: M ~ x', E ~ y', S ~ z
- After x2: U↔D swap, F↔B swap

**SOLVED for Down→Front:**
- Algorithm: Swap M↔M' → [M, F, M, F', M', F, M', F']
- Coordinate mapping: Identity (same as Up) → Down(r, c) → Front(r, c)
- All tests pass for 5x5 and 7x7 cubes!

Sources:
- [Ruwix - Advanced Notation](https://ruwix.com/the-rubiks-cube/notation/advanced/)
- [JPerm - Cube Moves](https://jperm.net/3x3/moves)

---

## Support Matrix

> **Instructions:** Update this table after testing new cube sizes or face pairs.

### By Cube Size (Target = Front)

| Cube | Type | U→F | D→F | B→F | L→F | R→F | Notes |
|------|------|-----|-----|-----|-----|-----|-------|
| 5x5 | Odd | ✅ | ✅ | ✅ | ✅ | ✅ | All positions work |
| 6x6 | Even | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Inner 2x2 fails (see below) |
| 7x7 | Odd | ✅ | ✅ | ✅ | ✅ | ✅ | All positions work |

### 6x6 Even Cube Limitation

On 6x6 cubes (4x4 center grid), the **inner 2x2 positions** fail:
- Failing positions: (1,1), (1,2), (2,1), (2,2)
- Symptom: Attribute moves to target, but cube state NOT preserved (edges disturbed)
- Outer positions work correctly: corners (0,0), (0,3), (3,0), (3,3) and edges

| Source→Front | Total Tests | Failed | Fail Positions |
|--------------|-------------|--------|----------------|
| U→F | 64 | 7 | (1,1), (1,2), (2,1), (2,2) |
| D→F | 64 | 7 | (1,1), (1,2), (2,1), (2,2) |
| B→F | 64 | 7 | (1,1), (1,2), (2,1), (2,2) |
| L→F | 64 | 7 | (1,1), (1,2), (2,1), (2,2) |
| R→F | 64 | 7 | (1,1), (1,2), (2,1), (2,2) |

**Root Cause**: The commutator algorithm [M', F, M', F', M, F, M, F'] is not edge-preserving for certain inner positions on even cubes. The M slices used pass through the cube center in a way that affects edge pieces.

**TODO**: Investigate if there's a different algorithm variant for even cube inner positions.

---

## Next Steps

1. ✅ All 5 sources → Front complete for odd cubes!
2. ⚠️ Fix even cube inner 2x2 position issue
3. Consider adding other target faces (currently only Front is supported)
4. Integration: ensure existing tests still pass
5. Optional: Refactor NxNCenters to use CommutatorHelper

---

## Files

| File | Purpose |
|------|---------|
| `docs/commutator-helper.md` | This tracking document |
| `src/cube/domain/solver/common/big_cube/CommutatorHelper.py` | The helper class |
| `tests/solvers/test_commutator_helper.py` | Test file |

---

## References

- `NxNCenters.py:890-1041` - `_block_commutator()` - the old algorithm
- `NxNCenters.py:1282-1308` - `_point_on_source/_point_on_target`
- `Cube.py:570-571` - `inv()` function definition
- `Face.py` - Face class definition
