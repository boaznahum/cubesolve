
# Algorithm Transformation by Whole-Cube Rotations — Theory & Implementation

## Table of Contents

1. [Definition](#1-definition)
2. [Motivation — Why This Works](#2-motivation--why-this-works)
3. [Formal Definitions](#3-formal-definitions)
4. [The Three Identities](#4-the-three-identities-theorem)
5. [The Transformation Principle](#5-the-transformation-principle)
6. [Lemmas — How Each Move Type Transforms](#6-lemmas--how-each-move-type-transforms)
7. [Implementation Reference](#7-implementation-reference)
8. [Examples](#8-examples)

---

## 1. Definition

Given a whole-cube rotation W and an algorithm A, find T(W, A) such that:

```
W  T(W, A)  W'  =  A
```

- **W** — a whole-cube rotation (X, Y, Z, or any sequence of them)
- **A** — any algorithm, acting on some positions POS1
- **T(W, A)** — the transformed algorithm we want to find

In words: find an algorithm that, applied between W and W', reproduces A.

---

## 2. Motivation — Why This Works

A acts on positions POS1. We need the same effect at positions POS2.

W is a whole-cube rotation that moves POS1 to POS2.

Read **W T(W,A) W'** left to right:

1. **W** — rotate the cube. Pieces at POS1 move to POS2.
2. **T(W,A)** — does work at POS2.
3. **W'** — rotate back. Pieces return from POS2 to POS1.

The net effect is A (which acts on POS1). So T(W,A) must be doing
A's work, but at POS2.

**Key insight**: if we apply T(W,A) alone — without the W/W' wrapper —
it performs A's effect at POS2. That's exactly what we wanted.

### Example: Edge Swap

Algorithm A swaps edges at {LU, FU} (U face, top-down view):

```
      B
   +--+--+--+
   |  |  |  |
L  +--+--+--+  R
   |* |  |  |
   +--+--+--+
   |  |* |  |
   +--+--+--+
      F

   * = LU and FU (the edges A swaps)
```

We want to swap {FU, RU} instead. Pick **W = Y'**, which maps
L->F and F->R, so Y'({LU, FU}) = {FU, RU}.

T(Y', A) acts on {FU, RU}:

```
      B
   +--+--+--+
   |  |  |  |
L  +--+--+--+  R
   |  |  |* |
   +--+--+--+
   |  |* |  |
   +--+--+--+
      F

   * = FU and RU (the edges T(Y',A) swaps)
```

One base algorithm + whole-cube rotations = all positional variants.

---

## 3. Formal Definitions

### 3.1 Whole-Cube Rotation (W)

A whole-cube rotation is one of X, Y, Z (or their primes/doubles). It
rotates the entire cube without changing any piece's relative position —
only the naming of faces changes.

```
X (like R):  F→U→B→D→F    R,L fixed
Y (like U):  F→L→B→R→F    U,D fixed
Z (like F):  U→R→D→L→U    F,B fixed
```

A **sequence** W = w₁ w₂ … wₙ of whole-cube rotations composes their
effects. The combined permutation is P_W = P_wₙ ∘ … ∘ P_w₁ (applied
left-to-right on faces).

**Code**: `FacePermutation.from_axis()` builds the permutation for a single
rotation. `compute_permutation(w)` composes the full sequence.
→ `face_permutation.py:FacePermutation.from_axis()`
→ `alg_transform.py:compute_permutation()`

### 3.2 Face Permutation (P_W)

Each whole-cube rotation W induces a permutation P_W on the six face names
{U, D, F, B, L, R}. This is a bijection — every face maps to exactly one
other face.

For example, P_{Y'} maps:

```
F → R,  R → B,  B → L,  L → F,  U → U,  D → D
```

**Code**: `FacePermutation` class.
→ `face_permutation.py:FacePermutation`

### 3.3 Algorithm Transformation T(W, A)

Given whole-cube rotation W and algorithm A, define:

```
T(W, A) = the algorithm obtained by remapping every atomic
           move in A through the face permutation P_W
```

We write **WA** as shorthand for T(W, A).

**Code**: `a.transform(w)` is the public API (method on `Alg`). Internally,
each `Alg` subclass implements `transform_by(p, n_slices)` — the class itself
decides how to remap its face/slice/axis.
→ `Alg.py:transform()` (public method)
→ `Alg.py:transform_by()` (abstract, implemented by every subclass)

### 3.4 Piece-Position Set (S)

A set of piece-positions on the cube. For example:

- S = {LU, FU} — the edge at the Left-Up position and the edge at
  the Front-Up position
- S = {UFR, UBR, UFL} — three corners on the U face

An algorithm A **acts on S** if it only modifies pieces within S,
leaving all other pieces unchanged.

### 3.5 Equivalence (≡)

Two algorithms are **equivalent** (A₁ ≡ A₂) if they produce identical
cube states from any starting position.

**Code**: `assert_algs_equivalent(a1, a2, cube_size)` verifies this
by applying both algorithms to a solved cube and comparing all faces.
→ `tests/utils/_alg_utils.py:assert_algs_equivalent()`

---

## 4. The Three Identities (Theorem)

**Theorem**. Let W be a whole-cube rotation sequence and A any algorithm.
Then:

```
(1)  Conjugation:     W' A W   ≡  T(W, A)
(2)  Push-through:    A W      ≡  W T(W, A)
(3)  Composition:     T(W₁W₂, A)  ≡  T(W₂, T(W₁, A))
```

### Proof of (1) — Conjugation

This is the defining property of T. Each atomic move m in A, when
conjugated by W, becomes W' m W. But W' m W is exactly the move on
the face that W maps m's face to. That is, W' m W = T(W, m). By
induction over the sequence (Lemma 6), the identity extends to any A.

### Proof of (2) — Push-through

From (1): W' A W = T(W, A). Multiply both sides on the left by W:

```
A W = W T(W, A)     ∎
```

This is the practical form: a whole-cube rotation W at the end of A
can be moved to the front if every move in A is transformed.

### Proof of (3) — Composition

From (1) applied twice:

```
T(W₁W₂, A) = (W₁W₂)' A (W₁W₂)
            = W₂' W₁' A W₁ W₂
            = W₂' T(W₁, A) W₂       [by (1) on inner]
            = T(W₂, T(W₁, A))       [by (1) on outer]   ∎
```

**Code**: All three identities are verified by randomized tests.
→ `test_alg_transform.py:TestTheoremConjugationRandomized`
→ `test_alg_transform.py:TestTheoremPushThroughRandomized`
→ `test_alg_transform.py:TestTheoremCompositionRandomized`

---

## 5. The Transformation Principle

This is the **practical theorem** that motivates the entire module.

### Statement

> Let A be an algorithm that acts on piece-set S₁.
> Let W be a whole-cube rotation such that W(S₁) = S₂.
> Then **T(W, A) acts on S₂**, and its effect on S₂ mirrors A's effect on S₁.

### Proof (by unwrapping the conjugation)

We know from identity (1) that:

```
W' A W  =  T(W, A)
```

Rearranging (multiply left by W, right by W'):

```
A  =  W · T(W, A) · W'
```

Now, A acts on S₁ (given). So **W · T(W, A) · W'** acts on S₁.

Read this right-to-left as three steps:

```
Step 1:  W'          — rotate the whole cube
Step 2:  T(W, A)     — do the work
Step 3:  W           — rotate back
```

Diagram — what happens to the pieces at S₁:

```
          W'                T(W,A)              W
S₁ ──────────────▶ S₂ ──────────────▶ S₂ ──────────────▶ S₁
  (pieces move       (pieces at S₂     (pieces move
   from S₁ to S₂     are modified)      back to S₁)
   by rotation)                         by rotation)
```

- **Step 1 (W')**: The whole cube rotates. Pieces that were at S₁ are
  now sitting at S₂ = W(S₁). No pieces are actually changed — they
  just moved to different positions.

- **Step 2 (T(W, A))**: This is where the actual work happens. The
  pieces are at S₂, and T(W, A) modifies them — swapping, cycling,
  flipping — whatever A would have done, but at position S₂.

- **Step 3 (W)**: The whole cube rotates back. The modified pieces
  return from S₂ to S₁. The net effect is: pieces at S₁ are modified
  exactly as A modifies them.

The key insight: **T(W, A) does its work in Step 2, when the pieces
are at S₂**. Therefore, if we apply T(W, A) alone (without the W'/W
wrapper), it acts on S₂.

Formally: since W · T(W, A) · W' fixes everything outside S₁, and W'
maps S₁ → S₂, T(W, A) must fix everything outside S₂.   ∎

### Concrete Example: L3 Edge Swap

**Base algorithm** A: swaps edges LU ↔ FU

```
S₁ = { LU, FU }
```

```
        B
     ┌──┬──┬──┐
     │  │  │  │
  L  ├──┼──┼──┤  R    A swaps the edges
     │* │  │  │        marked * (LU and FU)
     ├──┼──┼──┤
     │  │* │  │
     └──┴──┴──┘
        F
```

**Goal**: swap FU ↔ RU instead.

```
S₂ = { FU, RU }
```

**Example 1 — W = Y' (swap FU ↔ RU)**:

We need W such that W({LU, FU}) = {FU, RU}.
Y' maps L→F and F→R, so **W = Y'**.

Compute T(Y', A): every move in A has its face remapped by P_{Y'}:

```
P_{Y'}:  F→R, R→B, B→L, L→F, U→U, D→D
```

The result is a new algorithm T(Y', A) that swaps FU ↔ RU:

```
        B
     ┌──┬──┬──┐
     │  │  │  │
  L  ├──┼──┼──┤  R    T(Y', A) swaps the edges
     │  │  │* │        marked * (FU and RU)
     ├──┼──┼──┤
     │  │* │  │
     └──┴──┴──┘
        F
```

Verification: Y · A · Y' ≡ T(Y', A).

**Example 2 — W = Y (swap BU ↔ LU)**:

We need W such that W({LU, FU}) = {BU, LU}.
Y maps L→B and F→L, so **W = Y**.

Compute T(Y, A): every move in A has its face remapped by P_Y:

```
P_Y:  F→L, L→B, B→R, R→F, U→U, D→D
```

The result is a new algorithm T(Y, A) that swaps BU ↔ LU:

```
        B
     ┌──┬──┬──┐
     │  │* │  │
  L  ├──┼──┼──┤  R    T(Y, A) swaps the edges
     │* │  │  │        marked * (BU and LU)
     ├──┼──┼──┤
     │  │  │  │
     └──┴──┴──┘
        F
```

Verification: Y' · A · Y ≡ T(Y, A).

**Both directions work.** The Transformation Principle is not tied to a
specific rotation direction — any W that maps S₁ → S₂ gives a valid
transform. The choice of Y vs Y' simply determines *which* target set S₂
you reach.

### Generating All Variants

From one base algorithm A acting on S₁, we derive a family:

| W   | S₂ = W(S₁)  | T(W, A) swaps |
|-----|-------------|---------------|
| —   | {LU, FU}    | LU ↔ FU (original) |
| Y'  | {FU, RU}    | FU ↔ RU |
| Y2  | {RU, BU}    | RU ↔ BU |
| Y   | {BU, LU}    | BU ↔ LU |

Four algorithms from one. The same principle applies to corner cycles,
edge flips, OLL, PLL — any algorithm that acts on a localizable set.

**Code**: `TestTransformationPrinciple` demonstrates this.
→ `test_alg_transform.py:TestTransformationPrinciple`

---

## 6. Lemmas — How Each Move Type Transforms

These lemmas establish *how* T(W, A) is computed for each atomic move type.
Combined with Lemma 6 (sequence homomorphism), they prove the conjugation
identity for arbitrary algorithms.

### Lemma 1 — Face Permutation

Each whole-cube rotation w ∈ {X, Y, Z, X', Y', Z', X2, Y2, Z2} induces
a permutation P_w on the 6 face names. The tables are:

```
X (like R): F→U→B→D→F,  R,L fixed
Y (like U): F→L→B→R→F,  U,D fixed
Z (like F): U→R→D→L→U,  F,B fixed
```

Primes reverse the cycle. Doubles compose twice.

**Code**: `face_permutation.py:_X_PERM`, `_Y_PERM`, `_Z_PERM`

### Lemma 2 — Permutation Composition

For W = w₁ w₂ … wₙ, the induced permutation is:

```
P_W = P_wₙ ∘ P_wₙ₋₁ ∘ … ∘ P_w₁
```

Applied left-to-right: P_W(f) = P_wₙ(…P_w₂(P_w₁(f))…)

**Code**: `face_permutation.py:FacePermutation.then()`

### Lemma 3 — Face Move Transform

For a face move on face f with rotation count n:

```
T(W, face_move(f, n))  =  face_move(P_W(f), n)
```

The rotation count n is preserved because the whole-cube rotation
preserves the "clockwise from outside" orientation.

**Code**: `FaceAlg.transform_by()`, `SlicedFaceAlg.transform_by()`

### Lemma 4 — Slice Move Transform

A slice S has a rotation face r_S (from `geometry_fundamentals.py`):

```
M → L,   E → D,   S → F
```

Map r_S through P_W:
- If P_W(r_S) is itself a slice rotation face → same slice, same n
- If P_W(r_S) is the **opposite** of a slice rotation face → that slice, **negated n**

The direction negation occurs because opposite faces have opposite
"looking from outside" orientations.

**When direction is negated for sliced slices** (e.g., M[2:3]):
slice indices must be **mirrored** (i → n_slices + 1 - i) because the
"near side" of the axis swaps. This requires knowing cube_size.

Example on 5×5 (n_slices = 3):

```
M[3:3] (nearest R)  →  S'[1:1] (nearest F)
M[1:1] (nearest L)  →  S'[3:3] (nearest B)
```

**Code**: `SliceAlg.transform_by()`, `MiddleSliceAlg.transform_by()`,
`SlicedSliceAlg.transform_by()`,
`face_permutation.py:transform_slice()`, `mirror_slice_indices()`

### Lemma 5 — Whole-Cube Rotation Transform

Same rule as Lemma 4, using axis faces instead of slice rotation faces:

```
X → R,   Y → U,   Z → F
```

**Code**: `WholeCubeAlg.transform_by()`,
`face_permutation.py:transform_axis()`

### Lemma 6 — Sequence Homomorphism

```
T(W, A₁ A₂ … Aₖ)  =  T(W, A₁)  T(W, A₂)  …  T(W, Aₖ)
```

The transform distributes over sequences because conjugation distributes:

```
W' (A₁ A₂) W  =  (W' A₁ W)(W' A₂ W)
```

This is the lemma that extends the per-move rules (Lemmas 3-5) to
arbitrary algorithms.

**Code**: `SeqAlg.transform_by()`, `_Inv.transform_by()`, `_Mul.transform_by()`

---

## 7. Implementation Reference

### File Structure

```
src/cube/domain/algs/
├── face_permutation.py      ← FacePermutation class + helper functions
├── alg_transform.py         ← compute_permutation() helper
├── Alg.py                   ← Base class: abstract transform_by()
├── FaceAlg.py               ← transform_by(): remap face
├── SlicedFaceAlg.py          ← transform_by(): remap face, keep slices
├── WideLayerAlg.py           ← transform_by(): remap face, keep layers
├── SliceAlg.py               ← transform_by(): remap slice via rotation face
├── MiddleSliceAlg.py          ← transform_by(): remap slice via rotation face
├── SlicedSliceAlg.py          ← transform_by(): remap slice, mirror if negated
├── WholeCubeAlg.py            ← transform_by(): remap axis via axis face
├── Inv.py                     ← transform_by(): delegate, wrap with inv
├── Mul.py                     ← transform_by(): delegate, keep multiplier
├── SeqAlg.py                  ← transform_by(): delegate to each child
└── AnnotationAlg.py           ← transform_by(): return self (no-op)

tests/algs/
└── test_alg_transform.py    ← 329 tests (unit + randomized + exhaustive)
```

### Public API

```python
from cube.domain.algs.Algs import Algs

# Transform algorithm A by whole-cube rotation W
result = Algs.F.transform(Algs.Y.prime)                # → R
result = sexy_move.transform(Algs.Y.prime, cube_size=3) # → B U B' U'

# Precompute permutation for reuse
from cube.domain.algs.alg_transform import compute_permutation
p = compute_permutation(Algs.Y.prime + Algs.X)
r1 = alg1.transform_by(p, n_slices=None)
r2 = alg2.transform_by(p, n_slices=None)
```

### Design: Polymorphic Dispatch

Each `Alg` subclass implements `transform_by(p, n_slices)`:

```python
class Alg(ABC):
    @abstractmethod
    def transform_by(self, p: FacePermutation, n_slices: int | None) -> Alg: ...
```

This ensures:
- **No isinstance chain**: each class owns its logic
- **Future-proof**: new Alg subtypes must implement transform_by (abstract)
- **No external access to protected members**: each class uses its own fields

### Facts Used

The transformation relies on these facts from `geometry_fundamentals.py`:

| Fact | Source | Used For |
|------|--------|----------|
| `SLICE_ROTATION_FACE` | axiom | M→L, E→D, S→F |
| `AXIS_FACE` | axiom | X→R, Y→U, Z→F |
| `FACE_TO_SLICE` | derived (reverse of above) | face → slice lookup |
| `FACE_TO_AXIS` | derived (reverse of above) | face → axis lookup |
| `SchematicCube.opposite()` | `schematic_cube.py` | direction negation |

The face permutation tables (X/Y/Z content movement) are defined in
`face_permutation.py` and match `Cube.x_rotate / y_rotate / z_rotate`.

---

## 8. Examples

### 8.1 Simple Face Move

```
W = Y'      A = F       T(Y', F) = R

P_{Y'}: F→R, R→B, B→L, L→F, U→U, D→D
F maps to R. Rotation count preserved.
```

### 8.2 Slice Move with Direction Negation

```
W = Y'      A = S       T(Y', S) = M'

S rotates like F.  P_{Y'}(F) = R.
R is the OPPOSITE of L (M's rotation face).
So S → M with negated direction → M'
```

### 8.3 Sequence (Sexy Move)

```
W = Y'      A = R U R' U'

T(Y', R) = B       (R→B)
T(Y', U) = U       (U fixed)
T(Y', R') = B'
T(Y', U') = U'

T(Y', A) = B U B' U'
```

### 8.4 The Transformation Principle in Action

```
A swaps edges at {LU, FU}.

To swap {FU, RU}: use T(Y', A)     — since Y'({LU,FU}) = {FU,RU}
To swap {RU, BU}: use T(Y2, A)     — since Y2({LU,FU}) = {RU,BU}
To swap {BU, LU}: use T(Y, A)      — since Y({LU,FU})  = {BU,LU}

One algorithm → four variants via Y rotations.
```
