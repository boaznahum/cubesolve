# Algorithm Notation Guide

This document describes the algorithm notation used in this Rubik's cube solver.

---

## Quick Reference Card

```
FACES:    R L U D F B          (clockwise when looking at face)
PRIME:    R' L' U' ...         (counter-clockwise)
DOUBLE:   R2 L2 U2 ...         (180 turn)
SLICE:    M E S                (single middle slice)
ALL:      [:]M [:]E [:]S       (all middle slices)
WIDE:     Rw r (2 layers)      (WCA standard)
N-WIDE:   3Rw 3r (3 layers)    (WCA standard, n layers)
ADAPTIVE: [:-1]Rw [:-1]r       (all-but-last, adapts to cube size)
CUBE:     X Y Z                (rotate whole cube)
```

---

## Cube Orientation

```
                    +-------------+
                    |             |
                    |      U      |   U = Up (White)
                    |    (top)    |
                    |             |
        +-----------+-------------+-----------+-------------+
        |           |             |           |             |
        |     L     |      F      |     R     |      B      |
        |  (left)   |  (front)    |  (right)  |   (back)    |
        |           |             |           |             |
        +-----------+-------------+-----------+-------------+
                    |             |
                    |      D      |   D = Down (Yellow)
                    |  (bottom)   |
                    |             |
                    +-------------+

Default colors:  F=Green  B=Blue  R=Red  L=Orange  U=White  D=Yellow
```

---

## Face Moves

### What is "Clockwise"?

**IMPORTANT:** Clockwise means looking DIRECTLY at that face.

```
    EXAMPLE: R (Right face, clockwise)

    Imagine you are standing to the RIGHT of the cube,
    looking directly at the R face:

         clockwise
        +---+
        | R |  Arrows show movement direction
        +---+

    From the normal front view, R moves:
        Front-right edge -> Top-right edge
        Top-right edge -> Back-right edge
        Back-right edge -> Bottom-right edge
        Bottom-right edge -> Front-right edge
```

### All Six Face Moves

```
+---------+-------------------------------------------------------------+
|  Move   |  How to Remember                                            |
+---------+-------------------------------------------------------------+
|   R     |  Right hand turns right layer AWAY from you                 |
|   L     |  Left hand turns left layer TOWARD you                      |
|   U     |  Top layer turns LEFT when viewed from above                |
|   D     |  Bottom layer turns RIGHT when viewed from below            |
|   F     |  Front layer turns clockwise like a clock                   |
|   B     |  Back layer turns clockwise (opposite of F view)            |
+---------+-------------------------------------------------------------+
```

### Prime (Inverse) Moves

Add `'` to reverse the direction:

```
    R' = R counter-clockwise
    R + R' = cube unchanged (they cancel out)
```

### Double Moves

`R2` = Do R twice (180 turn). Same as R + R. Direction doesn't matter for 180.

---

## Slice Moves (Middle Layers)

Slice moves rotate the MIDDLE layer(s) between two opposite faces.
The outer faces DON'T move - only the inner slices rotate.

### The Three Slice Moves

```
+------------------------------------------------------------------+
|                        M SLICE (Middle)                           |
|                                                                   |
|  The slice BETWEEN L and R faces. Rotates like L does.           |
|                                                                   |
|       +---+---+---+                                               |
|       |   | ^ |   |     Front view of 3x3:                       |
|       +---+---+---+     - Left column = L face                   |
|       |   | M |   |     - Middle column = M slice                |
|       +---+---+---+     - Right column = R face                  |
|       |   | v |   |                                               |
|       +---+---+---+     M moves the middle column UP             |
|        L   M   R                                                  |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|                        E SLICE (Equator)                          |
|                                                                   |
|  The slice BETWEEN U and D faces. Rotates like D does.           |
|                                                                   |
|       +---+---+---+                                               |
|       |   |   |   |  <- U (top row)                              |
|       +---+---+---+                                               |
|       | < | E | > |  <- E slice (middle row)                     |
|       +---+---+---+     E moves the middle row to the RIGHT     |
|       |   |   |   |  <- D (bottom row)                           |
|       +---+---+---+                                               |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|                        S SLICE (Standing)                         |
|                                                                   |
|  The slice BETWEEN F and B faces. Rotates like F does.           |
|                                                                   |
|  Top view (looking down):                                         |
|       +---+---+---+                                               |
|       |   |   |   |  <- B (back)                                 |
|       +---+---+---+                                               |
|       |   | S |   |  <- S slice (middle depth)                   |
|       +---+---+---+     S rotates clockwise (like F)             |
|       |   |   |   |  <- F (front)                                |
|       +---+---+---+                                               |
+------------------------------------------------------------------+
```

### Slice Direction Reference

**Remember:** Each slice rotates in the SAME direction as its reference face.

```
+---------+----------------+-------------------------------------+
| Slice   | Reference Face | Movement Description                |
+---------+----------------+-------------------------------------+
|   M     |      L         | Front->Up->Back->Down (like L)      |
|   E     |      D         | Front->Left->Back->Right (like D)   |
|   S     |      F         | Up->Right->Down->Left (like F)      |
+---------+----------------+-------------------------------------+
```

### Single vs All-Slices

On any cube, `M` means the single center slice. For big cubes with multiple inner slices, use `[:]M` for all of them:

| Notation | Code | Meaning | Sliceable |
|----------|------|---------|-----------|
| `M` | `Algs.M` | Single center slice (MiddleSliceAlg) | No |
| `[:]M` | `Algs.MM` | All inner slices (SliceAlg) | Yes |
| `E` | `Algs.E` | Single center slice | No |
| `[:]E` | `Algs.EE` | All inner slices | Yes |
| `S` | `Algs.S` | Single center slice | No |
| `[:]S` | `Algs.SS` | All inner slices | Yes |

---

## Slice Indexing (NxN Cubes)

On bigger cubes (4x4 and up), there are MULTIPLE middle slices.
You can control which slices move using index notation.

### CRITICAL: Indexing is 1-Based (NOT 0!)

```
+------------------------------------------------------------+
|  WARNING: Indices start at 1, NOT 0!                       |
|                                                             |
|     M[0]  <- INVALID! This will cause an error!            |
|     M[1]  <- VALID. First inner slice.                     |
+------------------------------------------------------------+
```

### How Many Slices?

```
Formula: n_slices = Cube Size - 2

+-------------+------------+-------------------------------------+
| Cube Size   | n_slices   | Valid Indices                       |
+-------------+------------+-------------------------------------+
|    3x3      |     1      | [1] only                            |
|    4x4      |     2      | [1], [2]                            |
|    5x5      |     3      | [1], [2], [3]                       |
|    6x6      |     4      | [1], [2], [3], [4]                  |
|    7x7      |     5      | [1], [2], [3], [4], [5]             |
+-------------+------------+-------------------------------------+
```

### Where Does Slice[1] Start?

**Slice[1] is ALWAYS closest to the reference face!**

```
+---------+----------------+-------------------------------------+
| Slice   | Reference Face | Slice[1] is closest to...           |
+---------+----------------+-------------------------------------+
|   M     |      L         | L face (left side)                  |
|   E     |      D         | D face (bottom)                     |
|   S     |      F         | F face (front)                      |
+---------+----------------+-------------------------------------+
```

### Visual Example: 5x5 Cube M Slices (Top View)

```
    +-----+-----+-----+-----+-----+
    |     |     |     |     |     |
    |  L  |M[1] |M[2] |M[3] |  R  |
    |face |     |     |     |face |
    +-----+-----+-----+-----+-----+
      ^                       ^
    Left                   Right
    face                   face

    M[1] = slice closest to L (reference face for M)
    M[2] = middle slice (true center)
    M[3] = slice closest to R
```

### Slice Range Notation

Move multiple slices at once:

| Format | Meaning | Example |
|--------|---------|---------|
| `[start:stop]CODE` | Slices from `start` to `stop` inclusive | `[1:2]M` |
| `[start:]CODE` | Slices from `start` to max | `[1:]M` |
| `[:]CODE` | All slices | `[:]M` |
| `[i1,i2,...]CODE` | Specific slice indices | `[1,3]M` |

---

## Whole Cube Rotations

Rotate the entire cube (no pieces move relative to each other, but orientation changes).

| Move | Like Face | Implementation |
|------|-----------|----------------|
| `X` | R | Rotate cube as if doing R (but entire cube) |
| `Y` | U | Rotate cube as if doing U (but entire cube) |
| `Z` | F | Rotate cube as if doing F (but entire cube) |

---

## Wide Moves

Wide moves turn multiple outermost layers from one face side.

### WCA Standard Wide Moves (Rw / r)

**WCA standard:** `Rw` = `r` = 2 outermost layers. Both notations are equivalent.
`Rw` is the official WCA form, `r` (lowercase) is the informal equivalent.

| Move | Layers | Meaning |
|------|--------|---------|
| `Rw` or `r` | 2 | R face + 1 inner layer (default, `n=2` omitted) |
| `3Rw` or `3r` | 3 | R face + 2 inner layers |
| `nRw` or `nr` | n | R face + (n-1) inner layers |

Same for all 6 faces: `Lw`/`l`, `Uw`/`u`, `Dw`/`d`, `Fw`/`f`, `Bw`/`b`.

Modifiers work as expected: `Rw'`, `Rw2`, `3Rw'`, `3r2`, etc.

**Default layer count:** `2Rw` and `Rw` are identical (2 is default, omitted in output).

```
5x5 Cube - Rw (2 layers):

    +-----+-----+-----+-----+-----+
    |     |     |     |     |#####|
    |  L  | M3  | M2  | M1  |# R #|  <- Rw turns R + M1 (2 outermost layers)
    |     |     |     |     |#####|
    +-----+-----+-----+-----+-----+
                              ^^^^
                         These 2 layers turn

5x5 Cube - 3Rw (3 layers):

    +-----+-----+-----+-----+-----+
    |     |     |     |#####|#####|
    |  L  | M3  | M2  |# M1#|# R #|  <- 3Rw turns R + M1 + M2 (3 outermost)
    |     |     |     |#####|#####|
    +-----+-----+-----+-----+-----+
                        ^^^^^^^^^^^
                    These 3 layers turn
```

**Code:**

| Notation | Code | Type |
|----------|------|------|
| `Rw` | `Algs.Rw` | `WideLayerAlg(R, layers=2)` |
| `r` | `Algs.r` | `WideLayerAlg(R, layers=2, lowercase=True)` |
| `3Rw` | `Algs.parse("3Rw")` | `WideLayerAlg(R, layers=3)` |

**Layer clamping:** On a 2x2 cube, `Rw` (layers=2) clamps to `min(2, size-1) = 1` layer.

### Adaptive Wide Moves: [:-1]Rw / [:-1]r (All-But-Last)

These special wide moves adapt to cube size at play time, always turning
ALL layers except the opposite face (`cube.size - 1` layers).

| Move | str() | On 3x3 | On 4x4 | On 5x5 | On NxN |
|------|-------|--------|--------|--------|--------|
| `[:-1]Rw` | `[:-1]Rw` | 2 layers | 3 layers | 4 layers | N-1 layers |
| `[:-1]r` | `[:-1]r` | 2 layers | 3 layers | 4 layers | N-1 layers |

**`[:-1]Rw` and `[:-1]r` are functionally identical** - they differ only in display notation.
Both use `WideLayerAlg` with `layers=ALL_BUT_LAST` (-1 sentinel).

```
5x5 Cube - [:-1]Rw (4 layers, all but L):

    +-----+-----+-----+-----+-----+
    |     |#####|#####|#####|#####|
    |  L  |# M3#|# M2#|# M1#|# R #|  <- Turns everything except L face
    |     |#####|#####|#####|#####|
    +-----+-----+-----+-----+-----+
     ^
     Only L stays fixed
```

**Why this exists:** CFOP F2L algorithms use wide moves to manipulate corner-edge
pairs while keeping the cross layer intact. On a 3x3, `Rw` (2 layers) works fine.
On bigger cubes, you need to move ALL inner layers together to preserve edge pairing.
The `[:-1]` notation computes the layer count at play time, so the same algorithm
works on any cube size.

**Code:**

| Notation | Code | Sugar | Notes |
|----------|------|-------|-------|
| `[:-1]Rw` | `Algs.RRw` | uppercase+w form | Used in commands/registry |
| `[:-1]r` | `Algs.rr` | lowercase form | Used in CFOP solver (`Algs.dd`, etc.) |
| `[:-1]Lw` | `Algs.LLw` | | |
| `[:-1]l` | `Algs.ll` | | |
| `[:-1]Uw` | `Algs.UUw` | | |
| `[:-1]u` | `Algs.uu` | | |
| `[:-1]Dw` | `Algs.DDw` | | |
| `[:-1]d` | `Algs.dd` | | |
| `[:-1]Fw` | `Algs.FFw` | | |
| `[:-1]f` | `Algs.ff` | | |
| `[:-1]Bw` | `Algs.BBw` | | |
| `[:-1]b` | `Algs.bb` | | |

### Parser: compat_3x3 Mode

The parser has a `compat_3x3` flag for CFOP solver algorithms that were written
for 3x3 but need to work on bigger cubes:

| Input | `compat_3x3=False` (default) | `compat_3x3=True` |
|-------|------------------------------|-------------------|
| `Rw` | `WideLayerAlg(R, 2)` — standard 2-layer | `WideLayerAlg(R, ALL_BUT_LAST)` — adaptive |
| `r` | `WideLayerAlg(R, 2, lowercase)` | `WideLayerAlg(R, ALL_BUT_LAST, lowercase)` |
| `M` | `MiddleSliceAlg` — single center | `SliceAlg` — all middle slices |
| `[:-1]Rw` | `WideLayerAlg(R, ALL_BUT_LAST)` | same |
| `3Rw` | `WideLayerAlg(R, 3)` | same |

---

## Sequence Notation

### Basic Sequences

```
R U R' U'    # Space-separated moves
```

### Grouped Sequences

```
[R U R' U']     # Bracketed group
(R U R' U')     # Parenthesized group (for repetition)
```

### Repetition

```
(R U R' U')2    # Repeat 2 times
R2             # R twice (special case for single move)
```

---

## String Output Format

When converting an algorithm to string (`str(alg)`):

| Internal State | Output |
|----------------|--------|
| `n = 1` | `R` |
| `n = 2` | `R2` |
| `n = 3` | `R'` |
| `n = 4` (or 0) | `R4` |

Sequences are output as: `[R U R' U']`

Named sequences are output as: `{name}`

---

## Implementation: WideLayerAlg

All wide moves (standard, n-layer, and adaptive) are implemented by a single class:

```python
class WideLayerAlg(AnimationAbleAlg):
    """
    layers=2:  Rw / r          (standard 2-layer, WCA default)
    layers=3:  3Rw / 3r        (3 outermost layers)
    layers=n:  nRw / nr        (n outermost layers)
    layers=-1: [:-1]Rw / [:-1]r (adaptive, all-but-last)
    """
    __slots__ = ("_face", "_layers", "_lowercase")
```

At play time, `_effective_layers(cube)` computes the actual count:
- Fixed layers: `min(self._layers, cube.size - 1)` (clamped)
- `ALL_BUT_LAST` (-1): `cube.size - 1` (adaptive)

---

## Summary Table

| Move | 3x3 | 5x5 | Standard | Sliceable | Code |
|------|-----|-----|----------|-----------|------|
| `R` | 1 layer | 1 layer | 1 layer | Yes | `Algs.R` |
| `Rw` / `r` | 2 layers | 2 layers | 2 layers | No | `Algs.Rw` / `Algs.r` |
| `3Rw` / `3r` | 2 layers* | 3 layers | 3 layers | No | `Algs.parse("3Rw")` |
| `[:-1]Rw` / `[:-1]r` | 2 layers | 4 layers | N/A | No | `Algs.RRw` / `Algs.rr` |
| `M` | 1 slice | 1 slice | 1 slice | No | `Algs.M` |
| `[:]M` | 1 slice | 3 slices | N/A | Yes | `Algs.MM` |
| `R[1:2]` | 2 layers | 2 layers | = Rw | - | `Algs.R[1:2]` |
| `X` | whole cube | whole cube | whole cube | No | `Algs.X` |

*On 3x3, `3Rw` clamps to `min(3, 2)` = 2 layers.

---

## Code Reference

| File | Purpose |
|------|---------|
| `src/cube/domain/algs/WideLayerAlg.py` | Wide moves: Rw, r, nRw, nr, [:-1]Rw, [:-1]r |
| `src/cube/domain/algs/MiddleSliceAlg.py` | Single middle slice (M, E, S) |
| `src/cube/domain/algs/SliceAlg.py` | All middle slices ([:]M, [:]E, [:]S) — sliceable |
| `src/cube/domain/algs/FaceAlg.py` | Face moves (R, L, U, D, F, B) — sliceable |
| `src/cube/domain/algs/_parser.py` | `parse_alg(s, compat_3x3=False)` — string to Alg |
| `src/cube/domain/algs/Algs.py` | `Algs.parse(s)`, move constants, Simple list |
| `src/cube/domain/algs/Alg.py` | Base class, `__str__()` |
| `src/cube/domain/algs/SimpleAlg.py` | `atomic_str()` implementation |

---

## Sources

- [Speedsolving Wiki - NxNxN Notation](https://www.speedsolving.com/wiki/index.php/NxNxN_Notation)
- [Ruwix - Advanced Notation](https://ruwix.com/the-rubiks-cube/notation/advanced/)
- [KewbzUK - 5x5 Notation](https://kewbz.co.uk/blogs/notations-1/5x5-notation)
