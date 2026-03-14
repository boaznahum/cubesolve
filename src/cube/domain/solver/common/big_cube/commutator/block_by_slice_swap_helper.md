# Block-by-Slice Swap Algorithm

## Overview

We have a **target block** on a target face with coordinates (r1,c1,r2,c2). Our task is
to swap it with a **source block** from a source face.

**How the swap works:**
1. Bring slices from source face to target face using slice operation (E, M, or S)
2. Rotate the target face (90° or 180°) — this puts the target block onto the visiting
   source slices and moves source content onto the target face
3. Apply the inverse slice operation — the slices return to source, carrying the
   original target block content with them

This is much simpler than the commutator, but the key difference is: **it swaps ALL
content on the affected slices, not just the target block**.

## The Six Blocks

When a slice swap happens, there are **6 blocks** that get swapped (3 pairs):

On the **target face** (in terms of the slice direction), the slice covers a full
strip. If the slice is vertical on the target face and the target block spans rows
r1..r2, columns c1..c2, then the full strip 0..nn-1 on columns c1..c2 splits into:

1. **Prefix block (before)**: rows 0..r1-1, cols c1..c2 (can be empty if r1=0)
2. **Target block (main)**: rows r1..r2, cols c1..c2
3. **Suffix block (after)**: rows r2+1..nn-1, cols c1..c2 (can be empty if r2=nn-1)

Each of these 3 blocks on the target face has a corresponding block on the source face
(determined by the face-to-face coordinate translation), giving us **6 blocks total**
(3 target blocks + 3 source blocks).

After the swap, each target block's content moves to its corresponding source block
position, and vice versa.

## Self-Intersection Constraint

For the swap to work, the target block must NOT overlap with itself after rotation:

- **180° rotation**: block (r1,c1,r2,c2) maps to (inv(r1),inv(c1),inv(r2),inv(c2))
  where inv(x) = nn-1-x
  - For vertical slices: rows r1..r2 must not overlap with inv(r2)..inv(r1)
  - For horizontal slices: cols c1..c2 must not overlap with inv(c2)..inv(c1)

- **90° rotation**: similar rules using rotation formulas
  (r,c) → (nn-1-c, r) for CW

### "Doesn't Cross the Middle" Rule

A block is valid if it **doesn't cross the middle in at least one direction**.

- Block entirely in one half (row or col) → 180° rotation sends it to the other half → no overlap → valid
- Block crosses the middle in BOTH directions → every rotation overlaps → invalid

**Half boundaries (precise math):**
For 180° rotation, range `[a, b]` must not overlap `[n-1-b, n-1-a]`:
- `lower_max = (n-2) // 2` — last row/col of lower half
- `upper_min = (n+1) // 2` — first row/col of upper half
- Even n: halves touch (`lower_max + 1 == upper_min`)
- Odd n: middle row/col excluded from both halves (gap at `n//2`)

### Center Cell Invariant

On odd cubes, `(n//2, n//2)` maps to itself under all rotations — always invalid.

## Four Combinations

There are 4 combinations to consider:
1. **Vertical slice + 90° rotation**
2. **Vertical slice + 180° rotation**
3. **Horizontal slice + 90° rotation**
4. **Horizontal slice + 180° rotation**

For a given source/target face pair, the Face2FaceTranslator determines which slice(s)
connect them. For **opposite faces**, there may be two different slice options. For
**adjacent faces**, there is one.

If the initial slice type doesn't match what we need, we can pre-rotate the target face
by 90° to convert between horizontal and vertical slice operations.

Note: 90° CCW is redundant for self-intersection — if CW overlaps on both axes,
CCW must also overlap on both axes. Only need to check CW and 180°.

## Natural Source

Like in the commutator, we have the concept of **natural source** — the position on the
source face that geometrically corresponds to the target position via face-to-face
translation. The caller may need to rotate the source face to align actual content with
the natural source position.

## Algorithm Sequence

For a basic swap (no setup rotations):
```
slice_alg → target_face_rotation → slice_alg' (inverse)
```

With source/target setup:
```
[source_setup] → [target_setup] → slice_alg → target_rotation → slice_alg' → [target_setup'] → [source_setup']
```

## API

### Class: BlockBySliceSwapHelper(SolverHelper)

### Result Dataclass: SliceSwapResult

```python
@dataclass(frozen=True)
class SliceSwapResult:
    slice_name: SliceName
    algorithm: Alg
    rotation_type: int               # 1 (90° CW), -1 (90° CCW), or 2 (180°)

    # The 3 target blocks (on target face)
    target_prefix_block: Block | None   # None if empty
    target_block: Block                 # The main target block
    target_suffix_block: Block | None   # None if empty

    # The 3 corresponding source blocks (on source face)
    source_prefix_block: Block | None   # None if empty
    source_block: Block                 # Natural source block
    source_suffix_block: Block | None   # None if empty
```

### Key Methods

1. **`is_valid_for_swap(target_block) -> bool`**
   - Check if target block can be swapped (no self-intersection for at least one
     rotation type)

2. **`execute_swap(source_face, target_face, target_block, rotation_type=None,
   dry_run=False, preserve_state=True) -> SliceSwapResult`**
   - Main API: execute or dry-run the slice swap
   - Auto-selects rotation_type if not specified
   - Returns all 6 blocks and the algorithm
   - In dry_run mode: computes geometry but doesn't execute

3. **`get_all_combinations(source_face, target_face, target_block) -> list[SliceSwapResult]`**
   - Returns all valid combinations (up to 4) with their 6 blocks

## Finding Swappable Blocks

### `get_largest_blocks_from_point(n, point) → list[Block]`

Returns up to 2 largest valid blocks with `point` as bottom-left corner,
extending upward (larger rows) and rightward (larger cols).

Two candidates from each point:
1. **Row-safe**: rows stay within the half containing `r`, cols extend to `n-1`
2. **Col-safe**: cols stay within the half containing `c`, rows extend to `n-1`

On odd `n`, the middle row/col produces no block in that dimension.
The center point `(mid, mid)` returns empty.

### `iter_sub_blocks(block) → Iterator[Block]`

Yields all sub-blocks anchored at `block.start`, from biggest to smallest.
Shrinks the larger dimension first (outer loop).

```python
# For Block((r1,c1), (r2,c2)), yields:
# Block((r1,c1), (r,c))  for r2 >= r >= r1, c2 >= c >= c1
```

### `get_largest_blocks_containing_point(n, point) → list[Block]`

Returns up to 4 half-plane blocks that contain `point`:
- Bottom half full-width, Top half full-width
- Left half full-height, Right half full-height

### Discovery Chain

```
get_largest_blocks_from_point(n, point)  →  up to 2 largest valid blocks
    ↓
iter_sub_blocks(block)  →  all sub-blocks anchored at start, biggest first
    ↓
is_valid_for_swap(block)  →  check no self-intersection under rotation
```

### Usage Pattern

```python
# Discover blocks for a point
for block in get_largest_blocks_from_point(n, point):
    for sub in iter_sub_blocks(block):
        if helper.is_valid_for_swap(sub):
            result = helper.do_swap(source, target, sub)
```

## Tests

**File**: `tests/geometry/test_block_slice_swap.py`

- 6-block marker verification across all 30 face pair combinations
- Full-slice blocks: 576 individual test cases
- Center cell invariant on odd cubes
- Dry run mode verification
- Nuclear swap tests for cube sizes 4–7 (1241 tests total)
