# Algorithm Notation Guide

This document describes the algorithm notation used in this Rubik's cube solver.

---

## Quick Reference Card

```
FACES:  R L U D F B    (clockwise when looking at face)
PRIME:  R' L' U' ...   (counter-clockwise)
DOUBLE: R2 L2 U2 ...   (180° turn)
SLICE:  M E S          (middle layers)
WIDE:   Rw Lw Uw ...   (2 layers)
CUBE:   X Y Z          (rotate whole cube)
```

---

## Cube Orientation

```
                    ┌─────────────┐
                    │             │
                    │      U      │   U = Up (White)
                    │    (top)    │
                    │             │
        ┌───────────┼─────────────┼───────────┬─────────────┐
        │           │             │           │             │
        │     L     │      F      │     R     │      B      │
        │  (left)   │  (front)    │  (right)  │   (back)    │
        │           │             │           │             │
        └───────────┼─────────────┼───────────┴─────────────┘
                    │             │
                    │      D      │   D = Down (Yellow)
                    │  (bottom)   │
                    │             │
                    └─────────────┘

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

         ↻  ← You see this when looking at R face
        ┌───┐
        │ R │  Arrows show movement direction
        └───┘

    From the normal front view, R moves:
        Front-right edge → Top-right edge
        Top-right edge → Back-right edge
        Back-right edge → Bottom-right edge
        Bottom-right edge → Front-right edge
```

### All Six Face Moves

```
┌─────────┬─────────────────────────────────────────────────────┐
│  Move   │  How to Remember                                    │
├─────────┼─────────────────────────────────────────────────────┤
│   R     │  Right hand turns right layer AWAY from you (↻)     │
│   L     │  Left hand turns left layer TOWARD you (↻)          │
│   U     │  Top layer turns LEFT when viewed from above (↻)    │
│   D     │  Bottom layer turns RIGHT when viewed from below    │
│   F     │  Front layer turns clockwise like a clock (↻)       │
│   B     │  Back layer turns clockwise (opposite of F view)    │
└─────────┴─────────────────────────────────────────────────────┘
```

### Prime (Inverse) Moves

Add `'` to reverse the direction:

```
    R' = R counter-clockwise

         ↺  ← Counter-clockwise when looking at R face
        ┌───┐
        │ R │
        └───┘

    R + R' = cube unchanged (they cancel out)
```

### Double Moves

`R2` = Do R twice (180° turn). Same as R + R. Direction doesn't matter for 180°.

---

## Slice Moves (Middle Layers)

Slice moves rotate the MIDDLE layer(s) between two opposite faces.
The outer faces DON'T move - only the inner slices rotate.

### The Three Slice Moves

```
┌──────────────────────────────────────────────────────────────────┐
│                        M SLICE (Middle)                          │
│                                                                  │
│  The slice BETWEEN L and R faces. Rotates like L does.          │
│                                                                  │
│       ┌───┬───┬───┐                                              │
│       │   │ ↑ │   │     Front view of 3x3:                       │
│       ├───┼───┼───┤     - Left column = L face                   │
│       │   │ M │   │     - Middle column = M slice                │
│       ├───┼───┼───┤     - Right column = R face                  │
│       │   │ ↓ │   │                                              │
│       └───┴───┴───┘     M moves the middle column UP             │
│        L   M   R                                                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                        E SLICE (Equator)                         │
│                                                                  │
│  The slice BETWEEN U and D faces. Rotates like D does.          │
│                                                                  │
│       ┌───┬───┬───┐                                              │
│       │   │   │   │  ← U (top row)                               │
│       ├───┼───┼───┤                                              │
│       │ ← │ E │ → │  ← E slice (middle row)                      │
│       ├───┼───┼───┤     E moves the middle row to the RIGHT      │
│       │   │   │   │  ← D (bottom row)                            │
│       └───┴───┴───┘                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                        S SLICE (Standing)                        │
│                                                                  │
│  The slice BETWEEN F and B faces. Rotates like F does.          │
│                                                                  │
│  Top view (looking down):                                        │
│       ┌───┬───┬───┐                                              │
│       │   │   │   │  ← B (back)                                  │
│       ├───┼───┼───┤                                              │
│       │   │ S │   │  ← S slice (middle depth)                    │
│       ├───┼───┼───┤     S rotates clockwise (like F)             │
│       │   │   │   │  ← F (front)                                 │
│       └───┴───┴───┘                                              │
└──────────────────────────────────────────────────────────────────┘
```

### Slice Direction Reference

**Remember:** Each slice rotates in the SAME direction as its reference face.

```
┌─────────┬────────────────┬─────────────────────────────────────┐
│ Slice   │ Reference Face │ Movement Description                │
├─────────┼────────────────┼─────────────────────────────────────┤
│   M     │      L         │ Front→Up→Back→Down (like L)         │
│   E     │      D         │ Front→Left→Back→Right (like D)      │
│   S     │      F         │ Up→Right→Down→Left (like F)         │
└─────────┴────────────────┴─────────────────────────────────────┘
```

---

## Slice Indexing (NxN Cubes)

On bigger cubes (4x4 and up), there are MULTIPLE middle slices.
You can control which slices move using index notation.

### CRITICAL: Indexing is 1-Based (NOT 0!)

```
┌────────────────────────────────────────────────────────────────┐
│  ⚠️  WARNING: Indices start at 1, NOT 0!                        │
│                                                                │
│     M[0]  ← INVALID! This will cause an error!                 │
│     M[1]  ← VALID. First inner slice.                          │
└────────────────────────────────────────────────────────────────┘
```

### How Many Slices?

```
Formula: n_slices = Cube Size - 2

┌─────────────┬────────────┬─────────────────────────────────────┐
│ Cube Size   │ n_slices   │ Valid Indices                       │
├─────────────┼────────────┼─────────────────────────────────────┤
│    3x3      │     1      │ [1] only                            │
│    4x4      │     2      │ [1], [2]                            │
│    5x5      │     3      │ [1], [2], [3]                       │
│    6x6      │     4      │ [1], [2], [3], [4]                  │
│    7x7      │     5      │ [1], [2], [3], [4], [5]             │
└─────────────┴────────────┴─────────────────────────────────────┘
```

### Where Does Slice[1] Start?

**Slice[1] is ALWAYS closest to the reference face!**

```
┌─────────┬────────────────┬─────────────────────────────────────┐
│ Slice   │ Reference Face │ Slice[1] is closest to...           │
├─────────┼────────────────┼─────────────────────────────────────┤
│   M     │      L         │ L face (left side)                  │
│   E     │      D         │ D face (bottom)                     │
│   S     │      F         │ F face (front)                      │
└─────────┴────────────────┴─────────────────────────────────────┘
```

### Visual Example: 5x5 Cube M Slices (Side View)

```
    Looking at the cube from ABOVE (bird's eye view):

    ┌─────┬─────┬─────┬─────┬─────┐
    │     │     │     │     │     │
    │  L  │M[1] │M[2] │M[3] │  R  │   ← Row of the cube
    │face │     │     │     │face │
    └─────┴─────┴─────┴─────┴─────┘
      ↑                       ↑
    Left                   Right
    face                   face
    (doesn't               (doesn't
     move)                  move)

    M[1] = slice closest to L (reference face for M)
    M[2] = middle slice (true center)
    M[3] = slice closest to R
```

### Visual Example: 6x6 Cube E Slices (Front View)

```
    ┌─────────────────────────────────────┐
    │                                     │
    │              U face                 │  ← Top (doesn't move)
    │                                     │
    ├─────────────────────────────────────┤
    │                                     │ ← E[4] (closest to U)
    ├─────────────────────────────────────┤
    │                                     │ ← E[3]
    ├─────────────────────────────────────┤
    │                                     │ ← E[2]
    ├─────────────────────────────────────┤
    │                                     │ ← E[1] (closest to D)
    ├─────────────────────────────────────┤
    │                                     │
    │              D face                 │  ← Bottom (doesn't move)
    │                                     │
    └─────────────────────────────────────┘

    E[1] = closest to D (reference face for E)
    E[4] = closest to U
```

### Visual Example: 7x7 Cube S Slices (Side View)

```
    Looking at cube from the RIGHT side:

    ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
    │     │     │     │     │     │     │     │
    │  F  │S[1] │S[2] │S[3] │S[4] │S[5] │  B  │
    │face │     │     │     │     │     │face │
    └─────┴─────┴─────┴─────┴─────┴─────┴─────┘
      ↑                                   ↑
    Front                               Back
    face                                face
    (doesn't                           (doesn't
     move)                              move)

    S[1] = closest to F (reference face for S)
    S[3] = true center slice
    S[5] = closest to B
```

### Slice Range Notation

Move multiple slices at once using various notations:

#### Output Formats (as generated by algorithms)

| Format | Meaning | Example |
|--------|---------|---------|
| `[start:stop]CODE` | Slices from `start` to `stop` inclusive | `[1:2]M` |
| `[start:]CODE` | Slices from `start` to max | `[1:]M` |
| `[1:stop]CODE` | Slices from 1 to `stop` (default start) | `[1:3]M` |
| `[i1,i2,...]CODE` | Specific slice indices | `[1,3]M` |

#### Parser Input Formats (can be parsed)

```
M[1:2]  - Move slices 1 and 2 together
M[1:3]  - Move slices 1, 2, and 3 together
E[2:4]  - Move slices 2, 3, and 4 together
M[1:]   - Move slices 1 through max
M[1,3]  - Move specific slices 1 and 3
```

**Note:** The output format places brackets BEFORE the algorithm (`[1:2]M`), but this is parsed correctly.

### Examples by Cube Size

**4x4 Cube (2 inner slices):**
```
M[1]    - Inner slice near L
M[2]    - Inner slice near R
M[1:2]  - Both inner slices (equivalent to M on 3x3)
```

**5x5 Cube (3 inner slices):**
```
M[1]    - First inner slice (near L)
M[2]    - Middle slice (true center)
M[3]    - Third inner slice (near R)
M[1:2]  - First two slices
M       - All slices together
```

**7x7 Cube (5 inner slices):**
```
E[1]    - First inner slice (near D)
E[2]    - Second slice
E[3]    - Middle slice (true center)
E[4]    - Fourth slice
E[5]    - Fifth slice (near U)
E[1:3]  - Bottom three inner slices
E[3:5]  - Top three inner slices
```

---

## Whole Cube Rotations

Rotate the entire cube (no pieces move relative to each other, but orientation changes).

| Move | Like Face | Implementation |
|------|-----------|----------------|
| `X` | R | Rotate cube as if doing R (but entire cube) |
| `Y` | U | Rotate cube as if doing U (but entire cube) |
| `Z` | F | Rotate cube as if doing F (but entire cube) |

**Agreement with standard:** Full agreement

---

## Wide Moves

### Double-Layer Moves (Nw notation)

| Move | Meaning |
|------|---------|
| `Rw` | R + adjacent M' (two layers) |
| `Uw` | U + adjacent E' (two layers) |
| `Fw` | F + adjacent S (two layers) |

**Agreement with standard:** Full agreement

### Adaptive Wide Moves (lowercase)

These moves are specific to this solver and adapt to cube size:

| Move | On 3x3 | On NxN |
|------|--------|--------|
| `r` | Same as R | R + all inner layers (L stays fixed) |
| `l` | Same as L | L + all inner layers (R stays fixed) |
| `u` | Same as U | U + all inner layers (D stays fixed) |
| `d` | Same as D | D + all inner layers (U stays fixed) |
| `f` | Same as F | F + all inner layers (B stays fixed) |
| `b` | Same as B | B + all inner layers (F stays fixed) |

**Difference from standard:** In standard notation, lowercase `r` often means `Rw` (2 layers). Our lowercase moves adapt to cube size, moving N-1 layers.

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

**Agreement with standard:** Mostly agrees. Some notations use `(...)2` others use `(...)×2`.

---

## Parser Limitations

The current parser (`_parser.py`) has these limitations:

1. **No exponent N support**: `R3` is not supported (use `R' ` instead)
2. **Basic tokenization**: Complex nested structures may not parse correctly
3. **Case sensitivity**: `r` vs `R` have different meanings (see Adaptive Wide Moves)

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

## Examples

### Input → Parsed → Output

| Input | Parsed OK | Output |
|-------|-----------|--------|
| `R` | Yes | `R` |
| `R'` | Yes | `R'` |
| `R2` | Yes | `R2` |
| `R U R' U'` | Yes | `[R U R' U']` |
| `(R U)2` | Yes | `[R U]2` |
| `M` | Yes | `M` |
| `M[1]` | No (not supported) | - |
| `Rw` | Yes | `Rw` |
| `r` | Yes | `r` (adaptive wide) |

---

## Code Reference

| File | Purpose |
|------|---------|
| `src/cube/domain/algs/_parser.py` | `parse_alg(s)` - String to Alg |
| `src/cube/domain/algs/Alg.py` | Base class, `__str__()` |
| `src/cube/domain/algs/Algs.py` | `Algs.parse(s)`, move constants |
| `src/cube/domain/algs/SimpleAlg.py` | `atomic_str()` implementation |
