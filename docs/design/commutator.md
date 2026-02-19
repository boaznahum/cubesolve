# Block Commutator for NxN Cubes

**Module:** `src/cube/domain/solver/common/big_cube/commutator/CommutatorHelper.py`

---

## What is CommutatorHelper?

**CommutatorHelper** is a tool that moves center pieces from one face to another on big cubes (4x4, 5x5, etc.).

```
Example: Move center piece from UP to FRONT

    UP face              FRONT face
    ┌───┬───┬───┐        ┌───┬───┬───┐
    │   │   │   │        │   │   │   │
    ├───┼───┼───┤        ├───┼───┼───┤
    │   │ A │   │  ───►  │   │ A │   │   Piece A transfers
    ├───┼───┼───┤        ├───┼───┼───┤   from UP to FRONT
    │   │   │   │        │   │   │   │
    └───┴───┴───┘        └───┴───┴───┘
```

**The algorithm used:**
```
[m, F, m2, F', m', F, m2', F']

Where:
  m  = slice move (M, E, or S) that brings piece from source to target
  F  = target face rotation
  m2 = slice for the rotated position
```

**Key features:**
- Moves center pieces without disturbing edges or corners
- Supports all 30 face pair combinations (any source → any adjacent target)
- Can move single pieces or rectangular blocks

---

## Theory Background

> **Source Credits:** This documentation is based on content from:
> - [Speedsolving Wiki: Commutators](https://www.speedsolving.com/wiki/index.php/Commutator)
> - [Ruwix: Commutators and Conjugates](https://ruwix.com/the-rubiks-cube/commutators-conjugates/)
> - [MIT: Mathematics of the Rubik's Cube](https://web.mit.edu/sp.268/www/rubik.pdf)
> - [UC Berkeley: Mathematical Theory](https://math.berkeley.edu/~hutching/rubik.pdf)
> - [Ryan Heise: Commutator Tutorials](https://www.ryanheise.com/cube/commutators.html)

### What is a Commutator?

A **commutator** is a sequence of moves in the form `[A, B] = A B A' B'` that affects only a small number of pieces while leaving most of the cube untouched.

In group theory notation:
- `A` and `B` are arbitrary move sequences
- `A'` is the inverse of `A`
- `[A, B]` denotes the commutator

### Why Commutators Work

The key insight is that when A and B overlap partially:

```
Step 1: A affects some pieces (set SA)
Step 2: B affects some pieces (set SB), including some from SA
Step 3: A' undoes A, BUT the overlapping pieces (SA ∩ SB) have moved
Step 4: B' undoes B, BUT the overlapping pieces have moved again

Result: Only pieces in the overlap region (SA ∩ SB) are affected!
```

If `A` and `B` are **completely disjoint** (affect different parts of the cube), then `A B A' B'` does exactly nothing - everything cancels out.

### The 3-Cycle Theorem

> **Theorem:** If supp(A) ∩ supp(B) consists of exactly one cubie, then [A, B] is a 3-cycle.

Where `supp(X)` (support of X) means the set of pieces affected by algorithm X.

**Example:** Let A = R' D' R and B = U
```
[A, B] = (R' D' R) U (R' D R) U'
```
This affects exactly 3 corners in a cycle, leaving everything else untouched.

This theorem is the foundation of center solving on big cubes: we use M-slice moves and face rotations that overlap in exactly one center piece position.

### Conjugates vs Commutators

| Pattern | Notation | Purpose |
|---------|----------|---------|
| **Conjugate** | A B A' | Setup → Action → Undo setup |
| **Commutator** | A B A' B' | Two partial operations that almost cancel |

**Conjugates** are used to "move a problem to a better position, solve it, then restore."
**Commutators** exploit the overlap between two operations to create minimal changes.

---

## The Block Commutator Pattern

For NxN cubes, the CommutatorHelper uses this pattern:

```
[m, F, m2, F', m', F, m2', F']
```

Where:
- `m` = Inner M-slice (or E/S slice depending on face pair)
- `F` = Target face rotation (clockwise or counter-clockwise)
- `m2` = M-slice for the rotated position (after F)

### Visual Example (5x5, Up→Front)

```
BEFORE COMMUTATOR:
==================

    UP face (source)           FRONT face (target)
    ┌───┬───┬───┬───┬───┐      ┌───┬───┬───┬───┬───┐
    │   │   │   │   │   │      │   │   │   │   │   │
    ├───┼───┼───┼───┼───┤      ├───┼───┼───┼───┼───┤
    │   │   │ A │   │   │      │   │   │ C │   │   │  ← target position
    ├───┼───┼───┼───┼───┤      ├───┼───┼───┼───┼───┤
    │   │   │   │   │   │      │   │   │   │   │   │
    ├───┼───┼───┼───┼───┤      ├───┼───┼───┼───┼───┤
    │   │   │   │   │   │      │   │   │ B │   │   │  ← intermediate
    ├───┼───┼───┼───┼───┤      ├───┼───┼───┼───┼───┤
    │   │   │   │   │   │      │   │   │   │   │   │
    └───┴───┴───┴───┴───┘      └───┴───┴───┴───┴───┘

    Piece A needs to move to position C on FRONT face

AFTER [M', F, M2', F', M, F, M2, F']:
=====================================

    3-CYCLE RESULT:
    A (from UP)    → C position (on FRONT)  ✓ Goal achieved!
    C (from FRONT) → B position (on FRONT)
    B (from FRONT) → A position (on UP)
```

### The Commutator Moves Visualized

```
Step 1: M' (inner slice)
┌─────────────┐
│ Brings A    │──→ A moves from UP to FRONT (to C position)
│ down to     │    along the M slice
│ Front       │
└─────────────┘

Step 2: F (rotate front face)
┌─────────────┐
│ C position  │──→ C moves to B position (rotated)
│ rotates to  │    A is now at C position
│ B position  │
└─────────────┘

Step 3: M2' (inner slice for rotated position)
┌─────────────┐
│ Brings the  │──→ Moves piece from B position
│ piece at B  │    (original C) back toward UP
│ up          │
└─────────────┘

Step 4: F' (undo front rotation partially)
... and so on, completing the 3-cycle
```

### Why It's Balanced (Preserves Corners)

The face rotations come in pairs:
```
F, F', F, F' = F + F' + F + F' = 0 net rotation
```

So corners return to their original positions after the commutator.

**However:** The source face rotation (setup move) is NOT balanced. When `preserve_state=True`, we undo this rotation after the commutator to preserve edge pairing.

---

## Coordinate System

The CommutatorHelper uses **LTR (Left-to-Right)** coordinates:

```
Looking at any face:

        Column →
        0   1   2
      ┌───┬───┬───┐
Row 2 │   │   │   │  ↑
      ├───┼───┼───┤  │
Row 1 │   │ X │   │  │  ← X is at (1, 1) in LTR
      ├───┼───┼───┤  │
Row 0 │ O │   │   │  Row
      └───┴───┴───┘

      O is at (0, 0) = bottom-left
```

**Key Points:**
- `(0, 0)` = bottom-left corner
- Y (row/first value) increases upward
- X (column/second value) increases rightward
- This matches mathematical convention (Cartesian coordinates)

---

## Slice Selection by Face Pair

Different source/target face pairs use different slices:

### Front as Target
| Source | Slice | Direction | Diagram |
|--------|-------|-----------|---------|
| Up | M | M' brings U→F | ↓ (down) |
| Down | M | M brings D→F | ↑ (up) |
| Back | M | M'2 brings B→F | ↓↓ (180°) |
| Left | E | E brings L→F | → (right) |
| Right | E | E' brings R→F | ← (left) |

### Right as Target
| Source | Slice | Direction | Diagram |
|--------|-------|-----------|---------|
| Up | S | S brings U→R | → (right looking at Front) |
| Down | S | S' brings D→R | ← (left looking at Front) |
| Front | E | E' brings F→R | ← |
| Back | E | E brings B→R | → |

```
SLICE ORIENTATION DIAGRAM:

      U
      ↑
  L ← F → R
      ↓
      D

M slice: Vertical, cuts between L and R
         M' moves U→F, M moves D→F

E slice: Horizontal, cuts between U and D
         E moves L→F, E' moves R→F

S slice: Parallel to F, cuts between F and B
         S moves U→R, S' moves D→R
```

---

## The Algorithm in Detail

### Step 1: Find Source Position (Face2FaceTranslator)

Given target position `(r, c)`, the `Face2FaceTranslator` computes where on the source face the piece must be for a single slice move to bring it to target.

```python
translation_result = Face2FaceTranslator.translate(
    target_face, source_face, target_point
)
expected_source = translation_result.source_coord
```

### Step 2: Setup Rotation (Align Source)

If the actual source piece is not at the expected position, rotate the source face to align it:

```python
n_rotate = find_rotation_idx(actual_source, expected_source)
# n_rotate ∈ {0, 1, 2, 3} clockwise rotations
source_face * n_rotate
```

```
EXAMPLE: Expected source is at (1,2), actual is at (2,1)
         Need 1 clockwise rotation to align

         Before:          After 1 CW:
         ┌───┬───┬───┐    ┌───┬───┬───┐
         │   │   │   │    │   │   │   │
         ├───┼───┼───┤    ├───┼───┼───┤
         │   │   │ E │    │ P │   │ E │  ← P moved to expected
         ├───┼───┼───┤    ├───┼───┼───┤
         │ P │   │   │    │   │   │   │
         └───┴───┴───┘    └───┴───┴───┘
         P = piece, E = expected position
```

### Step 3: Avoid Slice Intersection

The target face rotation (F) must not cause the target block to intersect with its rotated position on the slice axis:

```python
if cw_intersect:
    use F'  # counter-clockwise
else:
    use F   # clockwise
```

```
INTERSECTION PROBLEM:

If target is at column 1, and after F rotation it moves to column 1:
┌───┬───┬───┐     ┌───┬───┬───┐
│   │ T │   │  F  │   │ T │   │  ← Same column!
├───┼───┼───┤ ──→ ├───┼───┼───┤     The two M slices
│   │   │   │     │   │   │   │     would affect each other
└───┴───┴───┘     └───┴───┴───┘

SOLUTION: Use F' instead to move T to a different column
```

### Step 4: Execute Commutator

```python
commutator = [
    inner_slice,           # m
    on_front_rotate,       # F
    second_slice,          # m2
    on_front_rotate.prime, # F'
    inner_slice.prime,     # m'
    on_front_rotate,       # F
    second_slice.prime,    # m2'
    on_front_rotate.prime  # F'
]
```

### Step 5: Preserve State (Cage Method)

Undo the source setup rotation to preserve edge pairing:

```python
if preserve_state and n_rotate:
    source_face.prime * n_rotate  # Undo the setup
```

This is called the **Cage Method** - we "cage" the edges by undoing any face rotations that would break their pairing.

---

## Supported Face Pairs

The helper supports **30 face pair combinations** (all except same-face and opposite-face pairs).

```
NOT SUPPORTED (same face): U→U, D→D, F→F, B→B, L→L, R→R (6 pairs)
NOT SUPPORTED (opposite):  U↔D, F↔B, L↔R (6 pairs, 3 bidirectional)

SUPPORTED: All 30 remaining pairs
```

See `_supported_faces.py` for the complete translation table.

---

## Even Cube Considerations

On even cubes (4x4, 6x6), the inner 2x2 center positions require special handling because adjacent M slices share edge wings.

```
4x4 CENTER (2x2):
┌───┬───┐
│ I │ I │   I = Inner position (ALL positions on 4x4 are inner)
├───┼───┤
│ I │ I │
└───┴───┘

6x6 CENTER (4x4):
┌───┬───┬───┬───┐
│ O │ O │ O │ O │   O = Outer position
├───┼───┼───┼───┤   I = Inner position
│ O │ I │ I │ O │
├───┼───┼───┼───┤   Inner 2x2 needs special M slice ordering
│ O │ I │ I │ O │
├───┼───┼───┼───┤
│ O │ O │ O │ O │
└───┴───┴───┴───┘
```

The `_is_inner_position()` method detects these cases.

---

## CommutatorHelper Method Reference

### Public API

| Method | Purpose |
|--------|---------|
| `do_commutator()` | Execute commutator to move piece from source to target |
| `get_natural_source_ltr()` | Get expected source position for a target (debug) |
| `ltr_to_index()` | Convert LTR coordinates to center index |
| `index_to_ltr()` | Convert center index to LTR coordinates |
| `is_supported()` | Check if face pair is supported |

### Internal Methods

| Method | Purpose |
|--------|---------|
| `_do_commutator()` | Internal: compute translation data |
| `_find_rotation_idx()` | Find rotation to align actual→expected |
| `_compute_rotate_on_target()` | Determine F or F' based on intersection |
| `_get_slice_alg()` | Get slice algorithm for block position |
| `_normalize_block()` | Ensure block coordinates are ordered |
| `_1d_intersect()` | Check if two 1D ranges intersect |
| `_is_inner_position()` | Detect inner 2x2 on even cubes |

---

## Usage Example

```python
from cube.domain.solver.common.big_cube.commutator.CommutatorHelper import CommutatorHelper

helper = CommutatorHelper(solver)

# Move piece from Up(1,1) to Front(1,1)
target_block = ((1, 1), (1, 1))  # LTR coordinates (single point)
helper.do_commutator(
    source_face=cube.up,
    target_face=cube.front,
    target_block=target_block,
    preserve_state=True  # Undo setup rotation (Cage Method)
)
```

---

## Animation Reference

The commutator can be visualized as a "sliding" operation:

```
Frame 1: M' slice down
    ┌───┐         ┌───┐
    │ A │    →    │   │
    └───┘         └───┘
      ↓
    ┌───┐         ┌───┐
    │   │    →    │ A │
    └───┘         └───┘

Frame 2: F rotation
    ┌───┬───┐     ┌───┬───┐
    │ A │ C │  →  │   │ A │
    └───┴───┘     └───┴───┘
                  │ C │   │
                  └───┴───┘

... (continue for full commutator)
```

---

## Block Search Integration in LBL Solver

**Module:** `src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py`

### Overview

The LBL solver can optionally search for rectangular blocks of same-color pieces and solve them with a single commutator operation instead of piece-by-piece iteration. This feature is **currently disabled** pending investigation of edge cases.

### The Challenge: Block Rotation Changes Shape

**Critical Insight:** When searching for source blocks, we cannot rotate block COORDINATES like we do with single points. Rotating a block's coordinates changes its SHAPE:

```
Original 1x3 horizontal block at positions:
  (1,0), (1,1), (1,2)    ← Row 1, columns 0-2

After 90° clockwise coordinate rotation:
  (0,1), (1,1), (2,1)    ← Column 1, rows 0-2

This is now a 3x1 VERTICAL block!
```

The commutator's slice algorithm depends on the target block's shape to determine which slice to use. A 1x3 horizontal block uses different slices than a 3x1 vertical block. Therefore, **source blocks cannot be rotated** - we must find them at their natural position.

### Algorithm: Target-First Block Search

1. **Find target blocks** from tracked unsolved positions on target face
2. **Dry run commutator** to compute the "natural source block" position
3. **Check source face** at natural position (NO rotation search)
4. **Verify** second_block won't destroy solved pieces
5. **Execute** if valid

```python
def _try_blocks_from_target(
    self,
    required_color: Color,
    target_face_tracker: FaceTracker,
    source_face: Face
) -> bool:
    """
    Block-based solving: find target blocks first, check natural source.

    Unlike single-piece solving which can search 4 rotations,
    multi-cell blocks CANNOT be rotated because that changes shape.
    """
    target_blocks = self._find_target_blocks(required_color, target_face_tracker)

    for target_block in target_blocks:
        # Dry run to get natural source position
        dry_result = self._comm_helper.execute_commutator(
            source_face=source_face,
            target_face=target_face_tracker.face,
            target_block=target_block,
            dry_run=True
        )

        natural_source = dry_result.source_block
        second_block = dry_result.second_block

        # Check WITHOUT rotation (critical for multi-cell blocks)
        if self._source_block_has_color_no_rotation(
            required_color, source_face, natural_source, second_block
        ):
            self._comm_helper.execute_commutator(
                dry_run=False,
                _cached_secret=dry_result
            )
            return True

    return False
```

### Key Methods Added

| Method | Purpose |
|--------|---------|
| `_block_iter(block)` | Iterate over all cells in a rectangular block |
| `_rotate_block_clockwise(block, n)` | Rotate block coordinates (for future use) |
| `_source_block_has_color_no_rotation()` | Check source block WITHOUT rotation search |
| `_find_target_blocks()` | Find potential target blocks from tracked positions |
| `_try_blocks_from_target()` | Main entry point for block-based solving |

### Why No Rotation Search for Blocks

Single piece solving in `_source_point_has_color()`:
```python
# Single point: can search 4 rotations
for n in range(4):
    rotated_point = rotate_point_clockwise(source_point, n)
    if source_face.get(rotated_point).color == required_color:
        return n  # Found at rotation n
```

Multi-cell block solving in `_source_block_has_color_no_rotation()`:
```python
# Block: NO rotation search - shape would change
all_match = all(
    source_face.center.get_center_slice(pt).color == required_color
    for pt in self._block_iter(source_block)
)
if not all_match:
    return False  # Block not found at natural position
```

### Current Status

**Status:** Infrastructure implemented but disabled

The block search is disabled in `_solve_single_center_piece_from_source_face_impl()`:

```python
# Block-based solving infrastructure is implemented but temporarily disabled.
# To enable, uncomment:
# work_done = self._try_blocks_from_target(
#     color, target_face, source_face.face
# )
```

**Known Issues:** ~3% of test cases (9 out of ~300) fail when enabled. Investigation needed for edge cases where the commutator executes but pieces don't end up with correct colors.

### The 3-Cycle for Blocks

Block commutators work the same as single-piece commutators:

```
3-CYCLE: source1 → target → source2 → source1

For a 1x3 block:
┌───┬───┬───┐    ┌───┬───┬───┐
│ A │ A │ A │ →  │ T │ T │ T │   (source1 → target)
└───┴───┴───┘    └───┴───┴───┘

The entire block moves as a unit, preserving relative positions.
```

---

## Further Reading

- [MIT: Mathematics of the Rubik's Cube (PDF)](https://web.mit.edu/sp.268/www/rubik.pdf)
- [UC Berkeley: Mathematical Theory (PDF)](https://math.berkeley.edu/~hutching/rubik.pdf)
- [Ryan Heise: Corner 3-cycles](https://www.ryanheise.com/cube/corner_3_cycles.html)
- [Academic Paper: Commutators in the Rubik's Cube Group](https://www.tandfonline.com/doi/full/10.1080/00029890.2023.2263158)
