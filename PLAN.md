# Block Commutator Implementation Plan

## Overview

Extend the single-cell commutator to support rectangular blocks of center pieces. Instead of moving one piece at a time, move entire blocks (e.g., 2x1, 1x3, 2x2) in a single commutator operation.

## The Block Intersection Problem

### Why Blocks Have Size Limits

The commutator pattern is: `[m, F, m2, F', m', F, m2', F']`

- `m` = slice move affecting columns [c1, c2] (for M-slice)
- `F` = target face rotation
- `m2` = slice move for the ROTATED position

**Key constraint:** The first slice range must NOT intersect with the second slice range.

### Single Cell Example (works)
```
Position (1, 2) on 5x5 (n_slices=3):
- M-slice affects column 2
- After F rotation: (1,2) → (0,1) [90° CW: (r,c) → (n-1-c, r)]
- New position uses column 1
- No intersection: {2} ∩ {1} = ∅ ✓
```

### Block Intersection Diagram
```
For M-slice commutator, F rotation transforms:
    (r, c) → (n-1-c, r)

Original block at columns [c1, c2], rows [r1, r2]:
After F rotation, block moves to columns [r1, r2] (old rows become new columns)

INTERSECTION CHECK:
    [c1, c2] ∩ [r1, r2] must be empty!

Example on 5x5 (n_slices=3, coords 0-2):

    WORKS - Horizontal block at row 0:
    ┌───┬───┬───┐
    │ X │ X │   │  Block: (0,0)-(0,1), cols=[0,1], rows=[0,0]
    ├───┼───┼───┤  After F: cols become [0,0]
    │   │   │   │  Check: [0,1] ∩ [0,0] = {0} ≠ ∅  INTERSECTION!
    ├───┼───┼───┤
    │   │   │   │  Need F' instead: (r,c) → (c, n-1-r) = cols become [2,2]
    └───┴───┴───┘  Check: [0,1] ∩ [2,2] = ∅ ✓

    WORKS - Horizontal block at row 2:
    ┌───┬───┬───┐
    │   │   │   │
    ├───┼───┼───┤
    │   │   │   │
    ├───┼───┼───┤
    │ X │ X │   │  Block: (2,0)-(2,1), cols=[0,1], rows=[2,2]
    └───┴───┴───┘  After F: cols become [2,2]
                   Check: [0,1] ∩ [2,2] = ∅ ✓

    FAILS - Square block on diagonal:
    ┌───┬───┬───┐
    │ X │ X │   │  Block: (0,0)-(1,1), cols=[0,1], rows=[0,1]
    ├───┼───┼───┤  After F: cols become [0,1]
    │ X │ X │   │  Check: [0,1] ∩ [0,1] = [0,1] ≠ ∅  ALWAYS INTERSECTS!
    ├───┼───┼───┤
    │   │   │   │
    └───┴───┴───┘

    WORKS - Vertical block NOT on diagonal:
    ┌───┬───┬───┐
    │   │   │ X │  Block: (0,2)-(1,2), cols=[2,2], rows=[0,1]
    ├───┼───┼───┤  After F: cols become [0,1]
    │   │   │ X │  Check: [2,2] ∩ [0,1] = ∅ ✓
    ├───┼───┼───┤
    │   │   │   │
    └───┴───┴───┘
```

### Maximum Block Algorithm

Given starting position (r, c) and max requested size, find the largest valid block:

```
Algorithm: find_max_block(start_r, start_c, max_size, n_slices)

1. For each candidate block size (width, height) from largest to smallest:
   - Block spans rows [start_r, start_r + height - 1]
   - Block spans cols [start_c, start_c + width - 1]

2. Check bounds:
   - start_r + height - 1 < n_slices
   - start_c + width - 1 < n_slices

3. Check intersection for BOTH F and F' rotations:
   - F (CW):  new_cols = [start_r, start_r + height - 1]
   - F' (CCW): new_cols = [n-1-(start_r+height-1), n-1-start_r]

4. If at least one rotation avoids intersection, block is valid

5. Return largest valid block, or single cell if no larger block works
```

### Orientation Impact

The maximum block size DOES depend on the slice type:

| Slice | Axis | Intersection Check |
|-------|------|-------------------|
| M | columns | cols ∩ (rows after rotation) |
| E | rows | rows ∩ (cols after rotation) |
| S | depends on target | similar logic |

For E-slice (Left→Front, Right→Front):
- E operates on rows
- After F rotation, rows become columns
- Check: original rows ∩ new rows (from old columns)

## API Design

### New Method: `get_max_block_for_target`

```python
def get_max_block_for_target(
    self,
    source_face: Face,
    target_face: Face,
    target_start: Point,          # Starting position (r, c)
    max_block_size: Point | None  # (max_height, max_width) or None for unlimited
) -> Block:
    """
    Find the maximum block that can be moved via commutator.

    Args:
        source_face: Source face for the commutator
        target_face: Target face for the commutator
        target_start: Starting position (top-left of block) in LTR coords
        max_block_size: Maximum requested block size, None = cube size

    Returns:
        Block: ((r1, c1), (r2, c2)) - the maximum valid block
               May be single cell if no larger block possible
    """
```

### Extended `do_communicator` (already supports blocks)

The existing `do_communicator` already accepts blocks, but has assertion:
```python
assert target_block[0] == target_block[1]  # Remove this!
```

### New Method: `get_natural_source_block`

```python
def get_natural_source_block(
    self,
    source_face: Face,
    target_face: Face,
    target_block: Block
) -> Block:
    """
    Get the source block that maps to target block via single slice move.

    For a block, all points transform consistently.
    """
```

## Test Plan

### Test File: `tests/solvers/test_communicator_blocks.py`

```python
@pytest.mark.parametrize("cube_size", [5, 6, 7, 8, 9])
@pytest.mark.parametrize("face_pair", SUPPORTED_PAIRS)
def test_block_commutator(cube_size, face_pair):
    """
    Test block commutator for all positions and block sizes.

    For each starting position:
    1. Call get_max_block_for_target() with max_size=None
    2. Place unique markers on ALL source block pieces
    3. Execute do_communicator() with the block
    4. Verify:
       a. All markers moved to target block positions
       b. No markers remain on source block
       c. No markers appear elsewhere on cube
       d. Cube state preserved (edges/corners consistent)
    """
```

### Marker Verification for Blocks

```python
def verify_block_movement(cube, source_face, target_face, source_block, target_block):
    # 1. Generate unique markers for each cell in block
    markers = {}
    for r in range(source_block[0][0], source_block[1][0] + 1):
        for c in range(source_block[0][1], source_block[1][1] + 1):
            key = f"block_test_{uuid.uuid4().hex[:8]}"
            value = uuid.uuid4().hex
            markers[(r, c)] = (key, value)

            # Place marker
            slice_piece = source_face.center.get_center_slice((r, c)).edge
            slice_piece.c_attributes[key] = value

    # 2. Execute commutator
    helper.do_communicator(source_face, target_face, target_block, source_block)

    # 3. Verify all markers moved to target
    for (sr, sc), (key, value) in markers.items():
        # Calculate corresponding target position
        tr = target_block[0][0] + (sr - source_block[0][0])
        tc = target_block[0][1] + (sc - source_block[0][1])

        target_piece = target_face.center.get_center_slice((tr, tc)).edge
        assert key in target_piece.c_attributes
        assert target_piece.c_attributes[key] == value

        # Verify removed from source
        source_piece = source_face.center.get_center_slice((sr, sc)).edge
        assert key not in source_piece.c_attributes

    # 4. Verify no markers elsewhere (scan all centers on all faces)
    for face in cube.faces:
        for slice in face.center.all_slices:
            for key, _ in markers.values():
                if slice.edge is not target_piece:  # Skip target
                    assert key not in slice.edge.c_attributes
```

## Implementation Steps

### Phase 1: Create Block Test (TDD)
1. Create `tests/solvers/test_communicator_blocks.py`
2. Copy structure from `test_communicator_helper.py`
3. Add block iteration logic
4. Add block marker verification
5. Tests will fail initially (expected)

### Phase 2: Implement `get_max_block_for_target`
1. Add method to `CommunicatorHelper`
2. Implement intersection check for blocks
3. Handle both F and F' rotation directions
4. Consider slice type (M/E/S) impact

### Phase 3: Extend `do_communicator` for Blocks
1. Remove single-cell assertion
2. Update `_get_slice_alg` to handle block ranges
3. Verify `Face2FaceTranslator` works for blocks (or extend it)

### Phase 4: Run Tests and Iterate
1. Run tests, fix failures
2. Document edge cases discovered
3. Add diagrams to `commutator.md`

## Files to Modify

1. **New:** `tests/solvers/test_communicator_blocks.py`
2. **Modify:** `src/cube/domain/solver/common/big_cube/commun/CommunicatorHelper.py`
   - Add `get_max_block_for_target()`
   - Add `get_natural_source_block()`
   - Remove single-cell assertion in `do_communicator()`
   - Update slice algorithms for block ranges
3. **Possibly Modify:** `src/cube/domain/model/Face2FaceTranslator.py`
   - May need block translation support
4. **Update:** `docs/design/commutator.md`
   - Add block algorithm documentation

## Success Criteria

1. All existing single-cell tests still pass
2. New block tests pass for all:
   - Cube sizes: 5, 6, 7, 8, 9
   - All 30 face pairs
   - All valid block sizes at each position
3. Block markers move correctly (verified by test)
4. No markers left behind or appearing elsewhere
5. Cube state preserved after each commutator
