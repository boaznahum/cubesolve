# BlockBySliceSwapHelper — Block Discovery & Swap

## Overview

Swaps a target block with content from a source face using a single slice
conjugation: `slice → face_rotate → slice'`.

Unlike the commutator (3-cycle), this swaps ALL content on the affected slices,
creating 3 pairs of swapped blocks (prefix, main, suffix) — 6 blocks total.

## Coordinate System

- Row 0, Col 0 = **bottom-left** of a face
- Blocks grow **upward** (larger rows) and **rightward** (larger cols)
- `block.start` = bottom-left corner, `block.end` = top-right corner

## Block Discovery Functions

### `get_largest_blocks_from_point(n, point) → list[Block]`

Returns up to 2 largest valid blocks with `point` as bottom-left corner.

**Valid** = does not cross the middle in at least one dimension after 180° rotation.

```
lower_max = (n-2) // 2    # last index of lower half
upper_min = (n+1) // 2    # first index of upper half
```

Two candidates from each point:
1. **Row-safe**: rows stay within the half containing `r`, cols extend to `n-1`
2. **Col-safe**: cols stay within the half containing `c`, rows extend to `n-1`

On odd `n`, the middle row/col produces no block in that dimension.
The center point `(mid, mid)` returns empty.

### `iter_sub_blocks(block) → Iterator[Block]`

Yields all sub-blocks anchored at `block.start`, from biggest to smallest.

```python
# For Block((r1,c1), (r2,c2)), yields:
# Block((r1,c1), (r,c))  for r2 >= r >= r1, c2 >= c >= c1
```

Shrinks the larger dimension first (outer loop).

### `get_largest_blocks_containing_point(n, point) → list[Block]`

Returns up to 4 half-plane blocks that contain `point`:
- Bottom half full-width, Top half full-width
- Left half full-height, Right half full-height

## Block Validity

### `is_valid_for_swap(block) → bool`

A block is valid if at least one rotation (90° CW or 180°) doesn't cause
self-overlap on the slice-cut axis.

## Slice Swap Execution

### `do_swap(source_face, target_face, target_block, ...) → SliceSwapResult`

1. Translates target block to source face coordinates
2. Computes prefix/suffix strips around the block
3. Executes: `slice_alg → face_rotation → slice_alg'`

### `SliceSwapResult`

Contains all 6 blocks and the algorithm:
- `target_prefix_block`, `target_block`, `target_suffix_block`
- `source_prefix_block`, `source_block`, `source_suffix_block`

## Usage Pattern

```python
# Discover blocks for a point
for block in get_largest_blocks_from_point(n, point):
    for sub in iter_sub_blocks(block):
        if helper.is_valid_for_swap(sub):
            result = helper.do_swap(source, target, sub)
```

## Grid Size Examples

| Grid | Cube | Vertical NxN | Horizontal NxN | Total Unique |
|------|------|-------------|----------------|-------------|
| 4×4  |  6   | 4 (4×1)     | 4 (1×4)        | 56          |
| 6×6  |  8   | 6 (6×1)     | 6 (1×6)        | 360         |
