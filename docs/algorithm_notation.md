# Algorithm Notation Guide

This document describes the algorithm notation used in this Rubik's cube solver.

---

## Quick Reference Card

```
FACES:    R L U D F B          (clockwise when looking at face)
PRIME:    R' L' U' ...         (counter-clockwise)
DOUBLE:   R2 L2 U2 ...         (180 turn)
INNER:    2F 2R 3R ...         (inner slice, SiGN standard)
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

## Inner Slice Moves (SiGN Notation)

On big cubes (4x4+), `nF` means "turn only the nth inner slice from that face".
This is **SiGN standard notation**, used by Twizzle, speedsolving.com, and alg.cubing.net.

```
+---------+--------------------------------------------------------+
| Notation| Meaning                                                |
+---------+--------------------------------------------------------+
|   2F    | Turn only the 2nd layer from Front (inner slice)       |
|   2R    | Turn only the 2nd layer from Right (inner slice)       |
|   3R    | Turn only the 3rd layer from Right (5x5+)              |
|   2F'   | 2nd inner slice from Front, counter-clockwise          |
|   2F2   | 2nd inner slice from Front, 180° turn                  |
+---------+--------------------------------------------------------+
```

**Key distinction:** The number goes BEFORE the face letter, NOT after.

- `2F` = inner slice (2nd layer from F) — number before
- `F2` = F face 180° turn — number after

**Equivalence with bracket notation:**

| SiGN | Bracket | Meaning |
|------|---------|---------|
| `2F` | `[2:2]F` | 2nd inner slice from F |
| `3R` | `[3:3]R` | 3rd inner slice from R |

On a 3x3, `2L` = `M`, `2D` = `E`, `2F` = `S` (there's only one inner slice).

```
5x5 Cube - 2R (2nd inner slice from R):

    +-----+-----+-----+-----+-----+
    |     |     |     |#####|     |
    |  L  | M3  | M2  |#2R #|  R  |  <- Only this slice turns
    |     |     |     |#####|     |
    +-----+-----+-----+-----+-----+
                        ^^^^^
                    Only this layer
```

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

> Using R as the example face — same pattern applies to L, U, D, F, B.<br>
> Using M as the example slice — same for E (like D) and S (like F).<br>
> Modifiers `'` (CCW) and `2` (180°) apply to all move types.<br>
> **Span:** When a slice index reaches the opposite face (e.g., `4R` on a 4×4 = `L'`), the move "spans" across the cube. Range moves like `3-4R` can also span.

<table>
<tr>
  <th rowspan="2">#</th>
  <th rowspan="2">Description / Effect</th>
  <th colspan="3">Standard Sources</th>
  <th colspan="4">Ours</th>
</tr>
<tr>
  <th><a href="https://alpha.twizzle.net/edit/">Twizzle</a></th>
  <th><a href="https://mzrg.com/rubik/nota.shtml">MZRG</a></th>
  <th><a href="https://www.speedsolving.com/wiki/index.php?title=NxNxN_Notation">SS Wiki</a></th>
  <th>Code</th>
  <th>str()</th>
  <th>parse("str") ≡</th>
  <th>parse("str", 3×3) ≡</th>
</tr>
<!-- ═══════════════════ 1. Face Moves ═══════════════════ -->
<tr style="border-top:2px solid #888;"><td></td><td style="font-weight:bold;">Face Moves</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr>
  <td>1</td>
  <td>Turn outermost R layer CW</td>
  <td><code>R</code></td>
  <td><code>R</code></td>
  <td><code>R</code></td>
  <td><code>Algs.R</code></td>
  <td><code>R</code></td>
  <td>✅ <code>"R"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>2</td>
  <td>Turn outermost R layer CCW</td>
  <td><code>R'</code></td>
  <td><code>R'</code></td>
  <td><code>R'</code></td>
  <td><code>Algs.R.prime</code></td>
  <td><code>R'</code></td>
  <td><code>"R'"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>3</td>
  <td>Turn outermost R layer 180°</td>
  <td><code>R2</code></td>
  <td><code>R2</code></td>
  <td><code>R2</code></td>
  <td><code>Algs.R * 2</code></td>
  <td><code>R2</code></td>
  <td><code>"R2"</code></td>
  <td>same</td>
</tr>
<!-- ═══════════════════ 2. Inner Slices ═══════════════════ -->
<tr style="border-top:2px solid #888;"><td></td><td style="font-weight:bold;">Inner Slices</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr>
  <td>4</td>
  <td>Turn only the nth inner slice from R<br>(can span)</td>
  <td><code>2R</code>, <code>3R</code></td>
  <td><code>2R</code>, <code>3R</code></td>
  <td>—</td>
  <td><code>2 * Algs.R</code>, <code>3 * Algs.R</code><br><code>Algs.R[2]</code>, <code>Algs.R[3]</code><br><code>Algs.R[2:2]</code>, <code>Algs.R[3:3]</code></td>
  <td><code>2R</code>, <code>3R</code></td>
  <td>✅ <code>"2R"</code>, <code>"3R"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>5</td>
  <td>Turn inner slices n–m from R<br>(can span)</td>
  <td>✅ <code>3-4R</code><br>✅ <code>3-4Rw</code><br>✅ <code>3-4r</code></td>
  <td><code>3-4R</code> / <code>3-4r</code></td>
  <td>—</td>
  <td>✅ <code>Algs.R[3:4]</code><br>✅ <code>Algs.Rw[3:4]</code><br>✅ <code>Algs.r[3:4]</code></td>
  <td><code>[3:4]R</code><br><code>[3:4]Rw</code><br><code>[3:4]r</code></td>
  <td>✅ <code>"3-4R"</code><br>✅ <code>"3-4Rw"</code><br>✅ <code>"3-4r"</code><br>✅ <code>"[3:4]R"</code><br>✅ <code>"[3:4]Rw"</code><br>✅ <code>"[3:4]r"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>8</td>
  <td>Turn all slices from nth to last</td>
  <td>?</td>
  <td>?</td>
  <td>—</td>
  <td><code>Algs.R[3:]</code><br><code>Algs.r[3:]</code></td>
  <td><code>[3:]R</code><br><code>[3:]r</code></td>
  <td>✅ <code>"[3:]R"</code><br>✅ <code>"[3:]r"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>9</td>
  <td>Turn ALL R layers (≡ X, whole cube like R)</td>
  <td><code>x</code></td>
  <td><code>x</code></td>
  <td><code>x</code></td>
  <td>✅ <code>Algs.X</code><br>
      ✅ <code>Algs.R[:]</code><br>
      ✅ <code>Algs.Rw[:]</code><br>
      ✅ <code>Algs.r[:]</code><br>
      ✅ <code>Algs.R[1:]</code></td>
  <td>✅ <code>X</code><br>
      ✅ <code>[:]R</code><br>
      ✅ <code>[:]Rw</code><br>
      ✅ <code>[:]r</code><br>
      ✅ <code>[1:]R</code></td>
  <td>✅ <code>"X"</code><br>
      ✅ <code>"[:]R"</code><br>
      ✅ <code>"[:]Rw"</code><br>
      ✅ <code>"[:]r"</code><br>
      ✅ <code>"[1:]R"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>10</td>
  <td>Turn layers 1–3 from R (≡ [1:3]R)<br>
      <em>5×5: ≡ R + 2R + 3R</em></td>
  <td>?</td>
  <td>?</td>
  <td>—</td>
  <td><code>Algs.R[:3]</code><br><code>Algs.r[:3]</code></td>
  <td><code>[1:3]R</code><br><code>[1:3]r</code></td>
  <td>✅ <code>"[:3]R"</code><br>✅ <code>"[:3]r"</code><br>✅ <code>"1-3R"</code></td>
  <td>same</td>
</tr>
<!-- ═══════════════════ 3. Wide Moves ═══════════════════ -->
<tr style="border-top:2px solid #888;"><td></td><td style="font-weight:bold;">Wide Moves<sup>③④</sup></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr>
  <td>11</td>
  <td>Turn 2 outermost R-side layers</td>
  <td>✅ <code>Rw</code> ✅ <code>r</code></td>
  <td><code>r</code> only<sup>③</sup></td>
  <td><code>Rw</code> or <code>r</code></td>
  <td><code>Algs.Rw</code> / <code>Algs.r</code></td>
  <td><code>Rw</code> / <code>r</code></td>
  <td>✅ <code>"Rw"</code> / <code>"r"</code></td>
  <td>⚠ ≡ <code>Algs.RRw</code><sup>④</sup></td>
</tr>
<tr>
  <td>12</td>
  <td>Turn 3 outermost R-side layers</td>
  <td>✅ <code>3Rw</code> ✅ <code>3r</code><br>❌ no span</td>
  <td><code>3r</code> only<sup>③</sup></td>
  <td><code>3Rw</code> or <code>3r</code></td>
  <td><code>3 * Algs.Rw</code><br><code>3 * Algs.r</code></td>
  <td><code>3Rw</code><br><code>3r</code></td>
  <td>✅ <code>"3Rw"</code><br>✅ <code>"3r"</code></td>
  <td>⚠ ≡ <code>Algs.RRw</code><sup>④</sup></td>
</tr>
<tr>
  <td>13</td>
  <td>Turn all layers except opposite face (adaptive)<br>
      <em>3×3: 2 · 4×4: 3 · 5×5: 4 · NxN: N−1</em></td>
  <td>—</td>
  <td>—</td>
  <td>—</td>
  <td><code>Algs.RRw</code> / <code>Algs.rr</code></td>
  <td><code>[:-1]Rw</code> / <code>[:-1]r</code></td>
  <td><code>"[:-1]Rw"</code> / <code>"[:-1]r"</code></td>
  <td>same</td>
</tr>
<!-- ═══════════════════ 4. Slice Moves ═══════════════════ -->
<tr style="border-top:2px solid #888;"><td></td><td style="font-weight:bold;">Slice Moves — sources disagree on big cubes<sup>①②</sup></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr>
  <td>14</td>
  <td>Turn single center slice between L&amp;R, like L<br>
      <em>3×3: 1 slice · 4×4: N/A · 5×5: 1 slice</em></td>
  <td><code>M</code></td>
  <td>—<sup>①</sup></td>
  <td><code>M</code></td>
  <td><code>Algs.M</code></td>
  <td><code>M</code></td>
  <td><code>"M"</code></td>
  <td>⚠ ≡ <code>Algs.MM</code><sup>②</sup></td>
</tr>
<tr>
  <td>15</td>
  <td>Turn ALL inner slices between L&amp;R, like L<br>
      <em>3×3: 1 · 4×4: 2 · 5×5: 3 slices</em></td>
  <td><code>m</code> (lowercase)</td>
  <td><code>M</code><sup>①</sup></td>
  <td>—</td>
  <td><code>Algs.MM</code></td>
  <td><code>[:]M</code></td>
  <td><code>"[:]M"</code></td>
  <td>same</td>
</tr>
<!-- ═══════════════════ 5. Slice Range & Indexing ═══════════════════ -->
<tr style="border-top:2px solid #888;"><td></td><td style="font-weight:bold;">Slice Range &amp; Indexing (ours only)</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr>
  <td>16</td>
  <td>Turn R face + 1st inner slice (= Rw)</td>
  <td>—</td>
  <td>—</td>
  <td>—</td>
  <td><code>Algs.R[1:2]</code></td>
  <td><code>[1:2]R</code></td>
  <td><code>"[1:2]R"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>17</td>
  <td>Turn R layers 2–3 (no outer face)<br>
      <em>5×5+: 2 inner slices</em></td>
  <td>—</td>
  <td>—</td>
  <td>—</td>
  <td><code>Algs.R[2:3]</code></td>
  <td><code>[2:3]R</code></td>
  <td><code>"[2:3]R"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>18</td>
  <td>Turn 1st M slice only (closest to L)</td>
  <td>—</td>
  <td>—</td>
  <td>—</td>
  <td><code>Algs.MM[1]</code></td>
  <td><code>[1:1]M</code></td>
  <td><code>"[1]M"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>19</td>
  <td>Turn M slices 1–2<br>
      <em>4×4+: 2 slices</em></td>
  <td>—</td>
  <td>—</td>
  <td>—</td>
  <td><code>Algs.MM[1:2]</code></td>
  <td><code>[1:2]M</code></td>
  <td><code>"[1:2]M"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>20</td>
  <td>Turn all M slices from 1st to last<br>
      <em>= [:]M, all inner slices</em></td>
  <td>—</td>
  <td>—</td>
  <td>—</td>
  <td><code>Algs.MM[1:]</code></td>
  <td><code>[1:]M</code></td>
  <td><code>"[1:]M"</code></td>
  <td>same</td>
</tr>
<!-- ═══════════════════ 6. Whole Cube Rotations ═══════════════════ -->
<tr style="border-top:2px solid #888;"><td></td><td style="font-weight:bold;">Whole Cube Rotations<sup>⑤</sup></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr>
  <td>21</td>
  <td>Rotate whole cube like R</td>
  <td><code>x</code></td>
  <td><code>x</code></td>
  <td><code>x</code></td>
  <td><code>Algs.X</code></td>
  <td><code>X</code></td>
  <td><code>"X"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>22</td>
  <td>Rotate whole cube like U</td>
  <td><code>y</code></td>
  <td><code>y</code></td>
  <td><code>y</code></td>
  <td><code>Algs.Y</code></td>
  <td><code>Y</code></td>
  <td><code>"Y"</code></td>
  <td>same</td>
</tr>
<tr>
  <td>23</td>
  <td>Rotate whole cube like F</td>
  <td><code>z</code></td>
  <td><code>z</code></td>
  <td><code>z</code></td>
  <td><code>Algs.Z</code></td>
  <td><code>Z</code></td>
  <td><code>"Z"</code></td>
  <td>same</td>
</tr>
</table>

**Notes:**

<sup>①</sup> MZRG defines `M` as ALL inner slices (portable across sizes), not single center.<br>
<sup>②</sup> In `compat_3x3` mode, `parse("M")` → all-slices (`[:]M`), so 3×3 algs work on bigger cubes.<br>
<sup>③</sup> MZRG (SiGN) uses only lowercase for wide moves — no `Rw` form.<br>
<sup>④</sup> In `compat_3x3` mode, `parse("Rw")`/`parse("r")`/`parse("3Rw")` → adaptive (`[:-1]Rw`/`[:-1]r`).<br>
<sup>⑤</sup> Standards use lowercase `x`/`y`/`z`. Our parser accepts uppercase `X`/`Y`/`Z`.<br>
❌<sup>⑥</sup> In standard notation, `3Rw` on a 3×3 is an error (only 2 non-opposite layers exist). Our implementation clamps to `min(3, size-1)` = 2 layers, equivalent to `Rw`.<br>
✅<sup>⑦</sup> Parser now supports SiGN range syntax (`3-4R`, `3-4Rw`, `3-4r`) — equivalent to bracket `[3:4]R`.<br>
✅<sup>⑧</sup> Bracket slicing on wide moves (`[3:4]Rw`, `[3:4]r`) now works — produces same result as `[3:4]R` (wide distinction irrelevant with explicit layers).<br>
✅<sup>⑨</sup> `[3:4]R` on 4×4 now works — spans to opposite face (layer 4 = L face rotated in R direction = L').<br>
✅<sup>⑩</sup> `nR` where n = cube size now rotates the opposite face (e.g. `4R` on 4×4 ≡ `L'`). Tested for all 6 faces on 3×3, 4×4, 5×5.

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
- [MZRG - SiGN Notation](https://mzrg.com/rubik/nota.shtml)
- [Twizzle Explorer](https://alpha.twizzle.net/edit/)
