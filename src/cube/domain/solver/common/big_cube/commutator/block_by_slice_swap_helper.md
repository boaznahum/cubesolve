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

## The Six Blocks and SwapBlockTriple

When a slice swap happens, there are **6 blocks** that get swapped (3 pairs).
Each group of 3 is represented by a `SwapBlockTriple(prefix, main, suffix)`.

Only `prefix` and `suffix` can be `None` (when the main block starts/ends at the edge).
`main` is never `None`.

### Vertical Slice — Block in the Middle

The slice covers a full vertical strip. The target block sits in the middle:

```
Target face (n=6)                Source face (natural)
cols c1..c2                      (translated coordinates)
┌──────────────────┐             ┌──────────────────┐
│                  │             │                  │
│   ┌──┐           │             │   ┌──┐           │
│   │P │ ← prefix  │             │   │P'│ ← source  │
│   │  │  (0,c1)   │             │   │  │   prefix  │
│   │  │  to       │             │   │  │           │
│   │  │  (r1-1,c2)│             │   └──┘           │
│   ├──┤           │   SWAP      │   ├──┤           │
│   │M │ ← main    │  ←────→    │   │M'│ ← source  │
│   │  │  (r1,c1)  │             │   │  │   main    │
│   │  │  to       │             │   │  │           │
│   │  │  (r2,c2)  │             │   └──┘           │
│   ├──┤           │             │   ├──┤           │
│   │S │ ← suffix  │             │   │S'│ ← source  │
│   │  │  (r2+1,c1)│             │   │  │   suffix  │
│   │  │  to       │             │   │  │           │
│   │  │  (n-1,c2) │             │   └──┘           │
│   └──┘           │             │                  │
└──────────────────┘             └──────────────────┘

After swap:  P↔P'  M↔M'  S↔S'
```

### Vertical Slice — Block at the Top (No Prefix)

```
Target face                      Source face
cols c1..c2
┌──────────────────┐             ┌──────────────────┐
│   ┌──┐           │             │   ┌──┐           │
│   │M │ ← main    │   SWAP     │   │M'│           │
│   │  │  (0,c1)   │  ←────→    │   │  │           │
│   │  │  to       │             │   └──┘           │
│   │  │  (r2,c2)  │             │   ├──┤           │
│   ├──┤           │             │   │S'│           │
│   │S │ ← suffix  │             │   │  │           │
│   │  │           │             │   └──┘           │
│   └──┘           │             │                  │
└──────────────────┘             └──────────────────┘

prefix = None (main starts at row 0)
```

### Vertical Slice — Full Column (No Prefix, No Suffix)

```
Target face                      Source face
cols c1..c2
┌──────────────────┐             ┌──────────────────┐
│   ┌──┐           │             │   ┌──┐           │
│   │M │ ← main    │   SWAP     │   │M'│           │
│   │  │  (0,c1)   │  ←────→    │   │  │           │
│   │  │  to       │             │   │  │           │
│   │  │  (n-1,c2) │             │   │  │           │
│   └──┘           │             │   └──┘           │
└──────────────────┘             └──────────────────┘

prefix = None, suffix = None (main spans full column)
```

### Horizontal Slice — Block in the Middle

```
Target face (n=6)
rows r1..r2
┌───────────────────────────────────────┐
│                                       │
│  ┌────────┬────────────┬─────────┐    │
│  │ prefix │   main     │ suffix  │    │
│  │(r1,0)  │ (r1,c1)   │(r1,c2+1)│    │
│  │  to    │  to        │  to     │    │
│  │(r2,    │ (r2,c2)    │(r2,n-1) │    │
│  │ c1-1)  │            │         │    │
│  └────────┴────────────┴─────────┘    │
│                                       │
└───────────────────────────────────────┘
```

### With Target Setup Rotation (setup_rotation=1)

When a 90° CW setup rotation is used, the blocks exist in two coordinate systems:

```
BEFORE setup (original coords)     AFTER setup (effective coords)
target_before_setup triple          target_after_setup triple

┌──────────────────┐                ┌──────────────────┐
│                  │    90° CW      │       ┌──┐       │
│ ┌──────────────┐ │   ────────→    │       │P'│       │
│ │ P  M   S     │ │                │       ├──┤       │
│ │ (horizontal) │ │                │       │M'│       │
│ └──────────────┘ │                │       │  │       │
│                  │                │       ├──┤       │
│                  │                │       │S'│       │
│                  │                │       └──┘       │
└──────────────────┘                └──────────────────┘

The algorithm operates on target_after_setup coordinates internally.
If undo_target_setup=True, setup' is appended and the face returns
to its original orientation → blocks end up at target_before_setup.
If undo_target_setup=False, the face stays rotated → blocks end up
at target_after_setup.
```

### With Source Setup Rotation (source_block parameter)

When the content you want is NOT at the natural source position, pass `source_block`
to tell the helper where it actually is. The helper computes the rotation needed:

```
Source face

BEFORE source_setup                  AFTER source_setup
(content at source_block)            (content aligned to natural_source)

┌──────────────────┐                 ┌──────────────────┐
│                  │   source_setup  │                  │
│   ┌──┐           │   (CW × N)     │        ┌──┐      │
│   │XX│ ← content │  ────────────→  │        │XX│ ← now│
│   │XX│   is here │                 │        │XX│   at  │
│   └──┘           │                 │        └──┘  nat. │
│  source_block    │                 │  natural_source   │
└──────────────────┘                 └──────────────────┘

source_before_setup.main == source_block
source_after_setup.main  == natural_source.main
natural_source.main      == geometric position from face-to-face translation

After the swap + source_setup' (undo):
- Source content (was at source_block) → arrives at target
- Target content → lands at source_block position (because source_setup' undoes)
```

## The 5 Block Triples

Each `SwapBlockTriple` has `.prefix`, `.main`, `.suffix`.

| # | Triple                | Face   | Description                                           |
|---|----------------------|--------|-------------------------------------------------------|
| 1 | `natural_source`      | source | Geometric natural position via face-to-face translation |
| 2 | `source_before_setup` | source | Where content actually is before source_setup rotation |
| 3 | `source_after_setup`  | source | After source_setup aligns content = natural_source     |
| 4 | `target_before_setup` | target | Target blocks in original face coordinates             |
| 5 | `target_after_setup`  | target | Target blocks in setup-rotated (effective) coordinates |

**Relationship between source triples:**
- `source_after_setup` always equals `natural_source` (setup aligns content to natural)
- `source_before_setup` differs from `natural_source` when `source_block` is provided
- When `source_block=None`: all 3 source triples are identical

**When `undo_target_setup=True`** (default): the algorithm includes `target_setup'`,
so after execution the target face is back in original orientation.
The caller should use `target_before_setup` for the final block positions.

**When `undo_target_setup=False`**: the algorithm omits `target_setup'`,
so the target face stays in setup-rotated orientation.
The caller should use `target_after_setup` for the final block positions.

**When `undo_source_setup=True`** (default): the algorithm includes `source_setup'`,
so the source face is back in its original orientation. Target content that went to
source ends up at `source_before_setup` positions (= `source_block` position).

**When `undo_source_setup=False`**: the algorithm omits `source_setup'`,
so the source face stays rotated. Target content ends up at `natural_source` positions.

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
1. **Vertical slice + 180° rotation** (no setup)
2. **Horizontal slice + 180° rotation** (no setup)
3. **Vertical slice + 180° rotation** (with 90° CW setup)
4. **Horizontal slice + 180° rotation** (with 90° CW setup)

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

With target setup + undo:
```
target_setup → slice_alg → target_rotation → slice_alg' → target_setup'
```

With target setup, no undo (`undo_target_setup=False`):
```
target_setup → slice_alg → target_rotation → slice_alg'
```

Full form (with source and target setup):
```
[source_setup] → [target_setup] → slice_alg → target_rotation → slice_alg' → [target_setup'] → [source_setup']
```

`source_setup` = rotate source face CW by `source_setup_rotation` steps.
`source_setup'` = undo (only if `undo_source_setup=True`).

## API

### SwapBlockTriple

```python
@dataclass(frozen=True)
class SwapBlockTriple:
    prefix: Block | None    # None if main starts at edge
    main: Block             # Never None
    suffix: Block | None    # None if main ends at edge
```

### SliceSwapResult

```python
@dataclass(frozen=True)
class SliceSwapResult:
    slice_name: SliceName
    algorithm: Alg
    rotation_type: int              # 1 (90° CW), -1 (90° CCW), or 2 (180°)
    setup_rotation: int             # 0 (none) or 1 (90° CW target setup)
    source_setup_rotation: int      # 0-3: CW rotations to align source_block to natural

    # The 5 block triples
    natural_source: SwapBlockTriple
    source_before_setup: SwapBlockTriple
    source_after_setup: SwapBlockTriple
    target_before_setup: SwapBlockTriple
    target_after_setup: SwapBlockTriple
```

Backward-compatible properties are available:
`target_block`, `target_prefix_block`, `target_suffix_block` → from `target_before_setup`
`source_block`, `source_prefix_block`, `source_suffix_block` → from `natural_source`

### Key Methods

1. **`is_valid_for_swap(target_block) -> bool`**
   - Check if target block can be swapped (no self-intersection for at least one
     rotation type)

2. **`execute_swap(source_face, target_face, target_block, source_block=None,
   dry_run=False, undo_target_setup=True, undo_source_setup=True) -> SliceSwapResult`**
   - Main API: execute or dry-run the slice swap
   - `source_block`: where content actually is on source face. If None, assumes
     content is at natural source position. If provided, computes the rotation
     needed to align it with natural_source and wraps the algorithm with
     source_setup / source_setup'.
   - Rotation type is auto-selected internally (first valid combination).
     The caller does not choose it — it's a geometric detail.
   - Returns all 5 block triples and the algorithm
   - `undo_target_setup`: include `target_setup'` in algorithm (default True)
   - `undo_source_setup`: include `source_setup'` in algorithm (default True)
   - In dry_run mode: computes geometry but doesn't execute

3. **`get_all_combinations(source_face, target_face, target_block) -> list[SliceSwapResult]`**
   - Returns all valid combinations (up to 4) with their 5 triples

## Finding Swappable Blocks

### `get_largest_blocks_from_point(n, point) -> list[Block]`

Returns up to 2 largest valid blocks with `point` as bottom-left corner,
extending upward (larger rows) and rightward (larger cols).

Two candidates from each point:
1. **Row-safe**: rows stay within the half containing `r`, cols extend to `n-1`
2. **Col-safe**: cols stay within the half containing `c`, rows extend to `n-1`

On odd `n`, the middle row/col produces no block in that dimension.
The center point `(mid, mid)` returns empty.

### `iter_sub_blocks(block) -> Iterator[Block]`

Yields all sub-blocks anchored at `block.start`, from biggest to smallest.
Shrinks the larger dimension first (outer loop).

```python
# For Block((r1,c1), (r2,c2)), yields:
# Block((r1,c1), (r,c))  for r2 >= r >= r1, c2 >= c >= c1
```

### `get_largest_blocks_containing_point(n, point) -> list[Block]`

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
            result = helper.execute_swap(source, target, sub)
            # Access triples:
            result.natural_source.main      # source main block
            result.target_before_setup.prefix  # target prefix in original coords
```

## Tests

**File**: `tests/geometry/test_block_slice_swap.py`

- 6-block marker verification across all 30 face pair combinations
- Full-slice blocks: 576 individual test cases
- Center cell invariant on odd cubes
- Dry run mode verification
- Nuclear swap tests for cube sizes 4-7 (1241 tests total)
