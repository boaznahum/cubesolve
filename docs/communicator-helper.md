# Communicator Helper - Development Tracking

> **INSTRUCTIONS FOR CLAUDE (future sessions):**
> This document tracks the development of a CommunicatorHelper class for big cube solving.
> When continuing work on this feature:
> 1. Read this file first to understand goals and progress
> 2. Update the "Current Status" and "Progress Log" sections after each session
> 3. Mark completed items in the checklist
> 4. Add new insights to the "Key Insights" section
> 5. Update "Next Steps" before ending the session
> 6. **COMMIT AND PUSH FREQUENTLY** after each progress step

---

## Goal

Create a `CommunicatorHelper` class that provides utilities for working with the **block commutator algorithm** used to solve center pieces on big cubes (NxN, where N > 3).

The core commutator is: `[M', F, M', F', M, F, M, F']`

---

## User Instructions (Session 2)

### Key Differences: Old vs New Helper

| Aspect | Old (NxNCenters) | New (CommunicatorHelper) |
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
3. **No face positioning**: The helper does the communicator WITHOUT first rotating to position faces - this is the core challenge
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
                    # Create sy, sx from y, x, rotation

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

**Phase:** Session 2 - Starting new implementation
**Last Updated:** 2025-12-26
**Session:** 2

---

## Checklist

### Phase 1: Foundation (COMPLETE)
- [x] Explore existing test structure and patterns
- [x] Create this tracking document
- [x] Create `CommunicatorHelper` class skeleton
- [x] Create test file `tests/solvers/test_communicator_helper.py`
- [x] Instantiate 7x7 cube in test
- [x] Instantiate helper in test and verify basic functionality

### Phase 2: Understand Coordinate Systems
- [ ] Study bottom-up, left-to-right coordinate system in existing code
- [ ] Understand how to translate BULR to face index
- [ ] Document coordinate transformation formulas

### Phase 3: Core Helper Methods
- [ ] Implement `inv(i)` - index inversion (adapted for BULR)
- [ ] Implement coordinate translation: BULR <-> face index
- [ ] Implement rotation point mapping for any face pair
- [ ] Implement block mapping between arbitrary faces

### Phase 4: Communicator Implementation
- [ ] Implement main communicator method accepting any source/target
- [ ] Handle all face pair combinations
- [ ] Validate block can be mapped with 0-3 rotations (throw exception if not)
- [ ] Implement cage preservation option

### Phase 5: Comprehensive Tests
- [ ] Test iterating all source faces
- [ ] Test iterating all target faces
- [ ] Test all slice positions (y, x in BULR system)
- [ ] Test all 4 rotation positions on source
- [ ] Verify attribute moves from source to target
- [ ] Verify cube state preserved (edges in position)

### Phase 6: Integration
- [ ] Ensure all existing tests still pass
- [ ] Optional: Refactor `NxNCenters.py` to use `CommunicatorHelper`

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

### New Coordinate System (CommunicatorHelper)

**Bottom-Up, Left-to-Right (BULR):**
- `(0,0)` is at **bottom-left**
- Y increases **upward**
- X increases **rightward**

Reference: See `docs/design2/face-slice-rotation.md` for detailed diagrams showing row 0 at bottom.

### Attribute System

To set/get attributes on center pieces that move with the color:
```python
part_edge = face.center.get_center_slice((row, col))
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
├── CommunicatorHelper.py   # NEW - general commutator utilities
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
- Created `CommunicatorHelper` class skeleton
- Created basic test file

### Session 2 (2025-12-26)
- Received detailed user instructions for new helper requirements
- Key insight: New helper supports ANY source/target face pair
- Key insight: Uses Bottom-Up Left-Right coordinate system
- Key insight: NO face positioning - this is the challenge
- Updated this tracking document with new requirements

---

## Next Steps

1. Study the BULR coordinate system in existing code
2. Understand face index translation
3. Start implementing core coordinate methods
4. Build comprehensive test structure

---

## Files

| File | Purpose |
|------|---------|
| `docs/communicator-helper.md` | This tracking document |
| `src/cube/domain/solver/common/big_cube/CommunicatorHelper.py` | The helper class |
| `tests/solvers/test_communicator_helper.py` | Test file |

---

## References

- `NxNCenters.py:890-1041` - `_block_communicator()` - the old algorithm
- `NxNCenters.py:1282-1308` - `_point_on_source/_point_on_target`
- `Cube.py:570-571` - `inv()` function definition
- `Face.py` - Face class definition
