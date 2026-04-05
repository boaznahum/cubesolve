# Session: Algorithm Transformation by Whole-Cube Rotations

Branch: `claude/cube-algorithm-transform-BYqjB`

## Concept

**T(W, A) = WA** — Transform algorithm A by whole-cube rotation W.

- **W** = sequence of whole-cube rotations: X, Y, Z (and primes/multiples)
- **A** = any cube algorithm (face moves, slices, wide moves, sequences)
- **WA** = A with every move remapped by the face permutation W induces

### Mathematical Identities

The correct identity (verified by tests):

```
W' A W = WA          (conjugation form)
A W = W WA           (push-through form — rotations commute past moves)
```

The push-through form is the practical one: you can "slide" a whole-cube
rotation W past any algorithm A by replacing each move with its transform.

### Example

```
W = Y'    A = F    WA = R
```

Y' sends the F face to the R position, so the F move becomes R.

Verification: `Y F Y' = R` (on-cube conjugation matches the transform).

---

## Key Insight: Everything Reduces to a Face Permutation

Each whole-cube rotation (X, Y, Z) is just a **permutation of 6 face names**.
Transforming ANY algorithm is nothing more than remapping face names through
that permutation.

### The Three Permutation Tables

```
X (like R): F→U  U→B  B→D  D→F    R,L fixed
Y (like U): F→L  L→B  B→R  R→F    U,D fixed
Z (like F): U→R  R→D  D→L  L→U    F,B fixed
```

These are **content movement** directions (matching Cube.x/y/z_rotate).

For primes (n=-1): apply the table 3 times (since n%4=3).
For doubles (n=2): apply 2 times.
For sequences (W = w1 w2 ... wn): compose permutations left-to-right.

### How Each Move Type Transforms

| Move Type | Transform Rule |
|-----------|---------------|
| **Face** (R,L,U,D,F,B) | Replace face name with P(face). Keep n. |
| **Sliced Face** (R[1:2]) | Replace face name. Keep slices and n. |
| **Wide** (Rw, 3r) | Replace face name. Keep layers and n. |
| **Slice** (M,E,S) | Map rotation face (M→L, E→D, S→F) through P. If result is a rotation face → same n. If result is OPPOSITE of a rotation face → negate n. |
| **Middle Slice** | Same as Slice. |
| **Whole-Cube** (X,Y,Z in A) | Map axis face (X→R, Y→U, Z→F) through P. Same direction/opposite logic as slices. |
| **Inverse** (_Inv) | Transform inner, then wrap with inv. |
| **Multiply** (_Mul) | Transform inner, keep multiplier. |
| **Sequence** (SeqAlg) | Transform each element. |

### Slice Direction Logic

Slice M rotates like face L. Under permutation P:
- If P(L) = D → M becomes E (same direction, since E rotates like D)
- If P(L) = U → M becomes E' (negated, since U is opposite of D)
- If P(L) = F → M becomes S
- If P(L) = B → M becomes S'
- If P(L) = L → M stays M
- If P(L) = R → M becomes M'

---

## Implementation

### Files Created

1. **`src/cube/domain/algs/alg_transform.py`** — Core transformation module
   - `FacePermutation` — Immutable permutation of 6 face names, with composition
   - `compute_permutation(w)` — Extract face permutation from a WholeCubeAlg sequence
   - `transform(w, a)` — Main API: T(W, A) = WA
   - `transform_by_permutation(p, a)` — Transform with precomputed permutation

2. **`tests/algs/test_alg_transform.py`** — 65 tests covering:
   - FacePermutation unit tests (identity, composition, all axes)
   - Face move transforms (all 6 faces under Y', X, Z)
   - Slice move transforms (M, E, S direction and negation)
   - Wide move transforms
   - Whole-cube rotation transforms within A
   - Sequence transforms
   - **Conjugation identity**: W' A W = WA (verified on 3x3 and 5x5)
   - **Push-through identity**: A W = W WA
   - Composed rotations (Y' X Z)

### Usage

```python
from cube.domain.algs.Algs import Algs
from cube.domain.algs.alg_transform import transform, compute_permutation, transform_by_permutation

# Basic transform
result = transform(Algs.Y.prime, Algs.F)  # → R

# Transform a sequence
sexy = Algs.R + Algs.U + Algs.R.prime + Algs.U.prime
result = transform(Algs.Y.prime, sexy)  # → B U B' U'

# Precompute permutation for reuse
p = compute_permutation(Algs.Y.prime + Algs.X)
r1 = transform_by_permutation(p, Algs.F)
r2 = transform_by_permutation(p, Algs.R)
```

---

## Design Decisions

1. **Permutation-based, not conjugation-based**: Instead of actually playing
   W A W' on a cube (O(n) cube operations), we compute a 6-element permutation
   once and remap each move in O(1). This is both faster and more elegant.

2. **Content movement convention**: The permutation tables follow the code's
   existing convention (Cube.y_rotate content direction), ensuring consistency.

3. **Immutable output**: Transformed algorithms are new Alg instances (consistent
   with the codebase's frozen-alg pattern).

4. **Separation of permutation and transformation**: `compute_permutation` and
   `transform_by_permutation` are separate, allowing the same rotation to be
   applied to many algorithms efficiently.
