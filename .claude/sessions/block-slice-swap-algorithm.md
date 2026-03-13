# Block-by-Slice Swap Algorithm — Session Plan

## Original Notes

In this session we will work on block swap by slice swap.

Most of the theoretical concepts are taken from the existing CommutatorHelper ("ch") and
Face2FaceTranslator. Most new capabilities are needed.

All the new code will be implemented basically in a new class under the geometry package
where ch is, and it will have similar methods. The class will be called
**BlockBySliceSwapHelper**.

## Theory

### The Algorithm

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

### The Six Blocks

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

### Self-Intersection Constraint

For the swap to work, the target block must NOT overlap with itself after rotation:

- **180° rotation**: block (r1,c1,r2,c2) maps to (inv(r1),inv(c1),inv(r2),inv(c2))
  where inv(x) = nn-1-x
  - For vertical slices: rows r1..r2 must not overlap with inv(r2)..inv(r1)
  - For horizontal slices: cols c1..c2 must not overlap with inv(c2)..inv(c1)

- **90° rotation**: similar rules using rotation formulas
  (r,c) → (nn-1-c, r) for CW

### Four Combinations

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

### Natural Source

Like in the commutator, we have the concept of **natural source** — the position on the
source face that geometrically corresponds to the target position via face-to-face
translation. The caller may need to rotate the source face to align actual content with
the natural source position.

### Algorithm Sequence

For a basic swap (no setup rotations):
```
slice_alg → target_face_rotation → slice_alg' (inverse)
```

With source/target setup:
```
[source_setup] → [target_setup] → slice_alg → target_rotation → slice_alg' → [target_setup'] → [source_setup']
```

## API Design (Following CommutatorHelper Patterns)

### Class: BlockBySliceSwapHelper(SolverHelper)

Located at: `src/cube/domain/solver/common/big_cube/commutator/BlockBySliceSwapHelper.py`

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

1. **`is_valid_for_swap(target_block, n_slices) -> bool`**
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

## Test Plan — TESTS FIRST

### File: `tests/geometry/test_block_slice_swap.py`

Following the commutator test pattern with **marker-based 6-block verification**:

1. **For each cube size** (5x5, 6x6, 7x7):
2. **For each face pair** (source, target):
3. **For each valid target block position**:
   - Place unique UUID markers on all 6 blocks (3 on target, 3 on source)
   - Execute the slice swap
   - Verify ALL 6 markers moved to the correct positions:
     - Target prefix block markers → source prefix block position
     - Target main block markers → source main block position
     - Target suffix block markers → source suffix block position
     - Source prefix block markers → target prefix block position
     - Source main block markers → target main block position
     - Source suffix block markers → target suffix block position
   - Verify edges/corners preserved (cube state preservation check)

### Test Structure:
```python
@pytest.mark.parametrize("cube_size", [5, 6, 7])
def test_slice_swap_6_block_markers(cube_size):
    """Verify all 6 blocks swap correctly with markers."""

@pytest.mark.parametrize("cube_size", [5, 6, 7])
def test_slice_swap_preserves_cube_state(cube_size):
    """Verify edges and corners are preserved after swap + undo."""

def test_slice_swap_self_intersection_rejected():
    """Verify blocks that self-intersect are correctly rejected."""
```

## Implementation Order

1. Write the test file with marker-based 6-block verification
2. Implement SliceSwapResult dataclass
3. Implement BlockBySliceSwapHelper class
4. Make tests pass
5. Commit and push
