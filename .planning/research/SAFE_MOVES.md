# Safe Moves Analysis: L1 + Middle Layer Edges Solved

**Context:** Layer-by-Layer (LBL) solve on NxN cube. L1 (bottom/D face) is fully solved
(centers + edges + corners). All middle-layer edge wings are also solved. Only L3
(top/U face) edge wings remain unsolved.

**Goal:** Determine which moves preserve all solved L1 and middle-layer edges.

---

## Cube Model Reference (from codebase)

### Layer Convention
```
Layer 1 (L1) = D face = bottom. Contains:
  - D-face centers
  - 4 D-layer corners (DFL, DFR, DBL, DBR)
  - Edge wings on DF, DR, DB, DL edges

Middle Layers = inner slices between D and U. Contain:
  - Side-face center rings (F, R, B, L at various rows)
  - Edge wings on FL, FR, BL, BR edges (one per slice level)

Layer 3 (L3) = U face = top. Contains:
  - U-face centers
  - 4 U-layer corners
  - Edge wings on UF, UR, UB, UL edges  <-- THESE are unsolved
```

### Physical Layer Structure (NxN cube, size N, n_slices = N-2)

```
Looking at cube from front:

    U face (L3 - top)
    ┌─────────────────────────┐
    │ UF edge wings (unsolved)│
    ├─────────────────────────┤  ← E[n_slices] (closest to U)
    │  Middle layer n_slices  │
    ├─────────────────────────┤  ← E[n_slices-1]
    │  Middle layer ...       │
    ├─────────────────────────┤  ← E[2]
    │  Middle layer 1         │
    ├─────────────────────────┤  ← E[1] (closest to D)
    │ DF edge wings (solved)  │
    └─────────────────────────┘
    D face (L1 - bottom, fully solved)
```

### Move → Physical Layer Mapping

Every move in this codebase maps to a face rotation and/or slice rotation.
The key is: **which physical layers does a move touch?**

**Face Moves (uppercase):**
- `R` → rotates R face only (slice index [0] from R side). Touches 0 inner layers.
- `L` → rotates L face only. Touches 0 inner layers.
- `U` → rotates U face only. Touches 0 inner layers.
- `D` → rotates D face only. Touches 0 inner layers.
- `F` → rotates F face only. Touches 0 inner layers.
- `B` → rotates B face only. Touches 0 inner layers.

**Face Moves with Slice Notation:**
- `R[1]` = `R` (default, face only)
- `R[1:2]` = face + first inner slice from R side = Rw equivalent on 3x3
- `R[1:k]` = face + first k-1 inner slices from R side

**Slice Moves:**
- `M[i]` → single inner slice on L↔R axis. Index 1 = closest to L.
- `E[i]` → single inner slice on U↔D axis. Index 1 = closest to D.
- `S[i]` → single inner slice on F↔B axis. Index 1 = closest to F.
- Bare `M`, `E`, `S` (no index) → ALL inner slices.

**Wide Moves (lowercase, adaptive):**
- `r` → R face + ALL inner layers (L face stays fixed). Moves N-1 layers total.
- `l` → L face + ALL inner layers (R face stays fixed).
- `u` → U face + ALL inner layers (D face stays fixed).
- `d` → D face + ALL inner layers (U face stays fixed).
- `f` → F face + ALL inner layers (B face stays fixed).
- `b` → B face + ALL inner layers (F face stays fixed).

**Double-Layer Moves (Rw etc.):**
- `Rw` = `R[1:size-1]` = R face + first (size-2) inner slices from R side.
  On 3x3: face + 1 slice. On 5x5: face + 3 slices.

**Whole-Cube Rotations:**
- `X` = rotate entire cube like R (R + all M' + L')
- `Y` = rotate entire cube like U (U + all E' + D')
- `Z` = rotate entire cube like F (F + all S + B')

---

## What "Solved Middle-Layer Edges" Means Physically

The middle-layer edge wings live on edges FL, FR, BL, BR. Specifically:
- FL edge has n_slices wings, one at each slice level
- FR edge has n_slices wings, one at each slice level
- BL edge has n_slices wings, one at each slice level
- BR edge has n_slices wings, one at each slice level

Each wing sits at a particular row/depth between L1 and L3.

A move is "safe for middle edges" if it does NOT move any of these wing positions, OR
if any wing it moves is restored to its original position by the end of the algorithm.

---

## ALWAYS-SAFE MOVES

### U and U' and U2

**Always safe. No exceptions.**

Rationale: U face rotation only touches the U face itself (slice index [0] from U side).
The U face edges are UF, UR, UB, UL -- all on L3, all unsolved. The E slice is NOT
touched. No middle-layer edge wings are on the U face edges.

```
Code path: Algs.U.play() → normalize_slice_index returns [0]
           → cube.rotate_face_and_slice(n, FaceName.U, [0])
           → only rotates U face (i==0 branch)
           → does NOT call rotate_slice()
```

### E[i] for any single inner slice index i

**Always safe.** E slice moves rotate the horizontal ring (F, R, B, L faces).
They move center slices and edge wings on FL, FR, BL, BR edges -- but ONLY at the
specific slice index i. If that specific slice level's edges are already solved, then
E[i] disrupts them. HOWEVER: E[i] cycles the wings in a ring:

```
E rotation cycle: FL[i] → BL[i] → BR[i] → FR[i] → FL[i]
```

This is a pure permutation of 4 wings at the same depth. If all 4 are solved (correct
colors in position), an E rotation scrambles them -- so E[i] is NOT always safe for
already-solved middle edges at depth i.

**CORRECTION:** E[i] moves solved middle-layer edges. E[i] is NOT unconditionally safe.
See "Conditional Moves" below.

### Whole-Cube Rotations (X, Y, Z)

**Always safe for piece relationships.** They rotate the entire cube, so relative
positions of all pieces are preserved. Solved pieces remain solved. However, they
change which physical face is "up" vs "down", which matters for algorithms that
assume a specific orientation.

Used freely by `bring_face_front_preserve_down` (Y rotations).

---

## NEVER-SAFE MOVES (for middle-layer edges specifically)

### D, D', D2

**Never safe.** D face rotation touches DF, DR, DB, DL edge wings at slice level
closest to D. These are L1 edges (solved). D rotation scrambles them.

### d (wide D, adaptive)

**Never safe.** `d` = D face + ALL inner layers. Moves everything except U face.
Destroys all middle-layer edges AND L1 edges.

### E (bare, no index) = all inner slices simultaneously

**Never safe.** Rotates ALL inner slice levels at once. This is equivalent to `Y'`
without the U and D face rotations. Destroys all middle-layer edges.

### M (bare, no index) = all inner slices simultaneously

**Never safe** for middle-layer edges. `M` rotates ALL M-slice layers. This moves
edge wings on the FL and FR edges (from L side perspective, the M slices contain
edge wing positions on edges perpendicular to L-R axis). Specifically:

M slice affects edges: F-U (FU edge wings at each depth), F-D (FD), B-U (BU), B-D (BD).

Wait -- let me be precise. The M slice (L-R axis) contains edge wings from:
- The FU edge (wing at each M-slice depth)
- The FD edge (wing at each M-slice depth)
- The BU edge
- The BD edge

These are VERTICAL edges (running top-to-bottom on front/back faces).

M does NOT directly touch the FL, FR, BL, BR edges (which run LEFT-RIGHT on side faces).
Those edges are on the S-slice axis (F-B) and... actually no.

**Let me re-derive from the Slice.py documentation:**

```
M Slice (axis L-R):
  Traversal: F → U → B → D → F
  Affects: content on F, U, B, D faces (the 4 faces perpendicular to L-R axis)

E Slice (axis U-D):
  Traversal: R → B → L → F → R
  Affects: content on R, B, L, F faces (the 4 faces perpendicular to U-D axis)

S Slice (axis F-B):
  Traversal: U → R → D → L → U
  Affects: content on U, R, D, L faces (the 4 faces perpendicular to F-B axis)
```

**Edge wing locations by slice type:**

M[i] moves edge wings that sit at depth i along the L-R axis. These wings are on:
- UF edge (the wing at column i from left) -- this is an L3 edge wing
- DF edge (the wing at column i from left) -- this is an L1 edge wing
- UB edge (the wing at corresponding position) -- L3 edge wing
- DB edge -- L1 edge wing

So M[i] touches L1 edge wings (on DF, DB) and L3 edge wings (on UF, UB).
**M[i] does NOT touch middle-layer edge wings** (those are on FL, FR, BL, BR).

Hmm, wait. Let me reconsider what "middle-layer edges" means in the LBL context.

### Clarification: Which Edges Are "Middle Layer Edges"?

In the LBL design document (DESIGN.md), middle layers are horizontal slices.
The middle-layer edge wings are:

```
Per middle layer (slice level k, k = 1 to n_slices):
  - FL edge, wing at index k  (on the Front-Left vertical edge)
  - FR edge, wing at index k  (on the Front-Right vertical edge)
  - BL edge, wing at index k  (on the Back-Left vertical edge)
  - BR edge, wing at index k  (on the Back-Right vertical edge)
```

These are the 4 VERTICAL edges of the cube. Each has n_slices wings.

**Which slice type moves these?**

FL edge: shared by F face and L face.
- F face rotation moves FL edge wings (all of them on the F face side)
- L face rotation moves FL edge wings (all of them on the L face side)
- The slice that contains FL edge wings between F and L... that's the S slice? No.
  S slice is F-B axis. M slice is L-R axis.

Actually: FL edge wings at depth k from D sit at E[k] slice level.
When E[k] rotates, the 4 wings at that depth cycle: FL[k] → BL[k] → BR[k] → FR[k].

**Therefore: E[k] is the slice move that moves middle-layer edge wings at depth k.**

And:
- **F face rotation** moves ALL FL edge wings (entire FL edge) and ALL FR edge wings.
- **R face rotation** moves ALL FR edge wings and ALL BR edge wings.
- **L face rotation** moves ALL FL edge wings and ALL BL edge wings.
- **B face rotation** moves ALL BL edge wings and ALL BR edge wings.

---

## REVISED CLASSIFICATION

### ALWAYS SAFE

| Move | Why Safe |
|------|----------|
| `U`, `U'`, `U2` | Only touches U face. U face edges (UF, UR, UB, UL) are L3 edges, not middle-layer edges. |
| `X`, `Y`, `Z` (whole-cube rotations) | Rotate entire cube. All relative positions preserved. |
| `M[i]` (single M-slice) | Moves wings on UF/DF/UB/DB edges (vertical front/back edges). These are L1 or L3 edges, NOT middle-layer edges (FL/FR/BL/BR). |
| `S[i]` (single S-slice) | Moves wings on UL/UR/DL/DR edges. These are L1 or L3 edges, NOT middle-layer edges. |

### NEVER SAFE (destroy solved pieces unconditionally)

| Move | Why Unsafe | What It Destroys |
|------|------------|-----------------|
| `D`, `D'`, `D2` | Rotates D face. Moves DF, DR, DB, DL edge wings. | L1 edges |
| `d` (wide D) | D + all inner layers. Moves everything except U. | L1 edges + all middle edges |
| `E` (bare, all slices) | All E-slice layers rotate. | All middle-layer edges |

### CONDITIONAL MOVES (safe WITH restoration)

| Move | What It Touches | Safe If... |
|------|-----------------|------------|
| `R`, `R'`, `R2` | FR and BR edge wings (ALL wings on these edges) | Followed by inverse to restore. Use as part of commutator: R ... R'. |
| `L`, `L'`, `L2` | FL and BL edge wings (ALL wings on these edges) | Followed by inverse to restore. |
| `F`, `F'`, `F2` | FL and FR edge wings (ALL wings on these edges) | Followed by inverse to restore. |
| `B`, `B'`, `B2` | BL and BR edge wings (ALL wings on these edges) | Followed by inverse to restore. |
| `E[i]` (single slice) | 4 edge wings at depth i: FL[i], FR[i], BL[i], BR[i] | Followed by inverse E[i]' to restore. |
| `M[i]` | UF/DF/UB/DB wings at depth i | Safe for middle edges (see Always Safe). But moves L1 edges (DF[i], DB[i]). Safe for L1 if restored. |
| `S[i]` | UL/UR/DL/DR wings at depth i | Safe for middle edges. But moves L1 edges (DL[i], DR[i]). Safe for L1 if restored. |

### NEVER SAFE for EITHER L1 or Middle Edges (without restoration)

| Move | L1 Impact | Middle Edge Impact |
|------|-----------|-------------------|
| `R` | None (R face has no L1 edges) | Destroys FR[all], BR[all] |
| `L` | None | Destroys FL[all], BL[all] |
| `F` | Destroys DF edge wings | Destroys FL[all], FR[all] |
| `B` | Destroys DB edge wings | Destroys BL[all], BR[all] |
| `M[i]` | Destroys DF[i], DB[i] | Does NOT touch middle edges |
| `S[i]` | Destroys DL[i], DR[i] | Does NOT touch middle edges |
| `E[i]` | None (E slice doesn't touch D face) | Destroys FL[i], FR[i], BL[i], BR[i] |

### WIDE MOVES (lowercase)

| Move | Layers Moved | L1 Safe? | Middle Edges Safe? |
|------|--------------|----------|-------------------|
| `r` | R + all inner (L fixed) | Yes (no L1 edges on R side) | No -- moves FR and BR wings |
| `l` | L + all inner (R fixed) | Yes | No -- moves FL and BL wings |
| `f` | F + all inner (B fixed) | No -- includes DF edge | No |
| `b` | B + all inner (F fixed) | No -- includes DB edge | No |
| `u` | U + all inner (D fixed) | Yes | No -- moves all middle edges |
| `d` | D + all inner (U fixed) | No | No |

---

## COMMUTATOR PATTERNS ALREADY USED IN CODEBASE

The LBL edge solver (`_LBLNxNEdges.py`) already implements safe-with-restoration
patterns. The key algorithm for inserting an edge wing from UF into FL or FR:

### Right-side insertion (target on FR edge):
```
U  R  U' M[k]' U  R' U' M[k]
```

Analysis of each move's safety:
- `U`      -- always safe (L3 only)
- `R`      -- moves FR[all] and BR[all] middle edges (conditional)
- `U'`     -- always safe
- `M[k]'`  -- moves UF[k] and UB[k] (L3 edges) + DF[k] and DB[k] (L1 edges) (conditional)
- `U`      -- always safe
- `R'`     -- RESTORES FR[all] and BR[all] (undoes the R)
- `U'`     -- always safe
- `M[k]`   -- RESTORES DF[k] and DB[k] (undoes the M[k]')

**Net effect on solved edges:** NONE. R and M[k] are both restored by their inverses.
This is a commutator pattern [U R U' M[k]', U R' U' M[k]] = identity on solved pieces.

### Left-side insertion (target on FL edge):
```
U' L' U  M[k]' U' L  U  M[k]
```

Same principle: L and M[k] are both restored.

---

## 5x5 CUBE EXAMPLES

### Setup: 5x5 with L1 solved + all middle edges solved

```
n_slices = 3 (indices 1, 2, 3 in public API; 0, 1, 2 internally)

Physical layout (front view):

    U face
    ┌──────────────────────┐
    │  UF edge: 3 wings    │  ← L3 (unsolved)
    ├──────────────────────┤
    │  Middle slice 3      │  FL[2], FR[2], BL[2], BR[2] solved
    ├──────────────────────┤
    │  Middle slice 2      │  FL[1], FR[1], BL[1], BR[1] solved
    ├──────────────────────┤
    │  Middle slice 1      │  FL[0], FR[0], BL[0], BR[0] solved
    ├──────────────────────┤
    │  DF edge: 3 wings    │  ← L1 (solved)
    └──────────────────────┘
    D face
```

### Example 1: Safe move sequence for L3 edge work

```python
# Goal: Bring a wing from UF to FR[1] (middle-edge position, but on L3 edge actually)
# Wait -- if middle edges are solved, we're only working on L3 (UF, UR, UB, UL) edges.
# So target is UF/UR/UB/UL wing positions.

# Safe sequence to cycle UF wings:
Algs.U          # Pure U rotation -- safe
Algs.U * 2      # U2 -- safe
Algs.U.prime    # U' -- safe
```

### Example 2: Using R in a commutator (conditional)

```python
# This sequence moves a wing but restores all middle edges:
alg = Algs.seq(
    Algs.U,                    # safe
    Algs.R,                    # CONDITIONAL: moves FR[0,1,2] and BR[0,1,2]
    Algs.U.prime,              # safe
    Algs.M[2].prime,           # CONDITIONAL: moves UF[1], UB[1], DF[1], DB[1]
    Algs.U,                    # safe
    Algs.R.prime,              # RESTORES FR and BR middle edges
    Algs.U.prime,              # safe
    Algs.M[2]                  # RESTORES DF[1] and DB[1] L1 edges
)
# Net effect on middle edges: ZERO (R restored by R', M[2] restored by M[2])
# Net effect on L1 edges: ZERO (M[2] restored)
# Useful effect: cycles a specific UF wing into position
```

### Example 3: What NOT to do

```python
# BAD: bare R without restoration
Algs.R          # Destroys FR[0], FR[1], FR[2] middle edge wings

# BAD: bare F
Algs.F          # Destroys FL[0,1,2], FR[0,1,2] middle edges AND DF L1 edge wings

# BAD: E[2] without restoration
Algs.E[2]      # Destroys FL[1], FR[1], BL[1], BR[1] (the 4 middle edges at depth 2)
               # Note: E public index 2 = internal index 1 = second slice from D

# BAD: bare D
Algs.D          # Destroys all DF, DR, DB, DL L1 edge wings
```

### Example 4: M[i] is safe for middle edges but conditional for L1

```python
# M[1] on 5x5:
# - Moves UF[0], UB[0] (L3 edges -- fine, those are unsolved)
# - Moves DF[0], DB[0] (L1 edges -- these ARE solved, must restore!)
# - Does NOT move FL, FR, BL, BR edges (middle edges safe!)

# So M[i] alone is:
#   - Safe for middle edges: YES (always)
#   - Safe for L1 edges: NO (must restore DF[i], DB[i])
#   - Safe for L3: irrelevant (unsolved anyway)

# S[i] is analogous but on the other axis:
# - Moves UL[i], UR[i] (L3)
# - Moves DL[i], DR[i] (L1 -- must restore!)
# - Does NOT move FL, FR, BL, BR (middle edges safe!)
```

---

## SUMMARY TABLE

```
┌─────────────────┬──────────────┬──────────────────┬──────────────┐
│ Move            │ L1 edges     │ Middle edges     │ L3 edges     │
├─────────────────┼──────────────┼──────────────────┼──────────────┤
│ U, U', U2       │ SAFE         │ SAFE             │ MOVED        │
│ X, Y, Z         │ SAFE*        │ SAFE*            │ SAFE*        │
│ R, R', R2       │ SAFE         │ DESTROYS FR,BR   │ SAFE         │
│ L, L', L2       │ SAFE         │ DESTROYS FL,BL   │ SAFE         │
│ F, F', F2       │ DESTROYS DF  │ DESTROYS FL,FR   │ SAFE         │
│ B, B', B2       │ DESTROYS DB  │ DESTROYS BL,BR   │ SAFE         │
│ D, D', D2       │ DESTROYS     │ SAFE             │ SAFE         │
│ M[i]            │ DESTROYS     │ SAFE             │ MOVED        │
│ E[i]            │ SAFE         │ DESTROYS (depth i)│ SAFE        │
│ S[i]            │ DESTROYS     │ SAFE             │ MOVED        │
│ M (bare)        │ DESTROYS ALL │ SAFE             │ MOVED ALL    │
│ E (bare)        │ SAFE         │ DESTROYS ALL     │ SAFE         │
│ S (bare)        │ DESTROYS ALL │ SAFE             │ MOVED ALL    │
│ r (wide R)      │ SAFE         │ DESTROYS FR,BR   │ MOVED        │
│ l (wide L)      │ SAFE         │ DESTROYS FL,BL   │ MOVED        │
│ f (wide F)      │ DESTROYS DF  │ DESTROYS FL,FR   │ MOVED        │
│ b (wide B)      │ DESTROYS DB  │ DESTROYS BL,BR   │ MOVED        │
│ u (wide U)      │ SAFE         │ DESTROYS ALL     │ MOVED        │
│ d (wide D)      │ DESTROYS     │ DESTROYS ALL     │ SAFE         │
│ Rw (=R[1:N-1])  │ SAFE         │ DESTROYS FR,BR   │ MOVED        │
│ Lw              │ SAFE         │ DESTROYS FL,BL   │ MOVED        │
│ Fw              │ DESTROYS DF  │ DESTROYS FL,FR   │ MOVED        │
│ Bw              │ DESTROYS DB  │ DESTROYS BL,BR   │ MOVED        │
│ Uw              │ SAFE         │ DESTROYS ALL     │ MOVED        │
│ Dw              │ DESTROYS     │ DESTROYS ALL     │ SAFE         │
└─────────────────┴──────────────┴──────────────────┴──────────────┘

* Whole-cube rotations preserve ALL relative positions.
  "SAFE" means the piece stays solved relative to its neighbors.
  "MOVED" means the piece changes physical position but is still solved
  relative to other moved pieces. The L3 column shows "MOVED" because
  U moves the unsolved L3 pieces -- that's the whole point.
```

## KEY INSIGHT FOR L3 EDGE SOLVING

When only L3 edges remain unsolved, the only truly "free" moves (no restoration
needed) are:

1. **U rotations** -- cycle L3 edges among themselves
2. **R, L in commutators** -- use R...R' or L...L' pairs that restore middle edges
3. **M[i] in commutators** -- use M[i]...M[i]' pairs that restore L1 edges

The existing codebase pattern (from `_LBLNxNEdges.py`) is exactly right:
```
U R U' M[k]' U R' U' M[k]   -- right-side insertion
U' L' U M[k]' U' L U M[k]   -- left-side insertion
```

Both R and M[k] appear exactly once with their inverse, guaranteeing net-zero
effect on all solved edges.

**Moves that should NEVER appear without restoration in L3 edge work:**
- D (destroys L1)
- F, B (destroy middle edges AND L1 edges)
- E[i] (destroys middle edges at depth i)
- Any bare slice move (M, E, S without index) -- too broad

## SOURCES

- `src/cube/domain/model/Slice.py` lines 1-166 (slice traversal and geometry)
- `src/cube/domain/algs/Algs.py` (move notation, slice indexing convention)
- `src/cube/domain/algs/FaceAlgBase.py` lines 151-156 (face play with normalize_slice_index)
- `src/cube/domain/algs/SliceAlgBase.py` lines 142-148 (slice play)
- `src/cube/domain/algs/WideFaceAlg.py` lines 1-74 (wide move semantics)
- `src/cube/domain/algs/DoubleLayerAlg.py` lines 44-53 (Rw = R[1:size-1])
- `src/cube/domain/model/Cube.py` lines 1228-1371 (rotate_face_and_slice, get_face_and_rotation_info)
- `src/cube/domain/solver/direct/lbl/_LBLNxNEdges.py` lines 434-466 (existing commutator patterns)
- `src/cube/domain/solver/direct/lbl/DESIGN.md` lines 44-87 (layer structure, move restrictions)
- Confidence: HIGH -- derived directly from codebase source code, not from external claims.
