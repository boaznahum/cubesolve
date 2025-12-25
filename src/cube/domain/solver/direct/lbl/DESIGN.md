# Layer-by-Layer NxN Solver Design

> **Issue:** [#48](https://github.com/boaznahum/cubesolve/issues/48)
> **Branch:** `issue-48-big-cube-layer-by-layer`
> **Status:** Design Phase
> **Created:** 2025-12-24

---

## Overview

This document describes a **direct layer-by-layer solver** for NxN cubes that solves each horizontal layer sequentially from bottom to top (or top to bottom), rather than using the traditional reduction method (centers → edges → 3x3).

**Inspiration:** [PuzzleMax13 YouTube](https://www.youtube.com/watch?v=lv9y8_4UZrk)

---

## Method Concept

### Traditional Reduction Method
```
Phase 1: Solve ALL centers (all 6 faces)
Phase 2: Pair ALL edges (all 12 edges)
Phase 3: Solve as 3x3
```

### Layer-by-Layer Method (This Design)
```
Layer 1 (D face):     Centers + Corners + Edges
Layer 2 (d slice):    Side centers + Edge wings
Layer 3 (3d slice):   Side centers + Edge wings
...
Layer n-1 (u slice):  Side centers + Edge wings
Layer n (U face):     Centers + Corners + Edges
```

**Key difference:** Each layer is fully solved before moving to the next. Once a layer is solved, moves affecting that layer are prohibited.

---

## Layer Structure

### For an NxN cube (example: 10x10 where n=10):

#### Layer 1 (D face - bottom)
| Piece Type | Count | Description |
|------------|-------|-------------|
| Centers | (n-2)² = 64 | D-face center pieces |
| Corners | 4 | DFL, DFR, DBL, DBR |
| Edge Wings | 4×(n-2) = 32 | Wings on DF, DR, DB, DL edges |
| **Total** | **100** | = n² |

#### Layers 2 through n-1 (middle slices)
| Piece Type | Count | Description |
|------------|-------|-------------|
| Centers | 4×(n-2) = 32 | Ring on F, R, B, L faces |
| Edge Wings | 4 | One wing from FL, FR, BL, BR |
| **Total** | **36** | Per layer |

#### Layer n (U face - top)
| Piece Type | Count | Description |
|------------|-------|-------------|
| Centers | (n-2)² = 64 | U-face center pieces |
| Corners | 4 | UFL, UFR, UBL, UBR |
| Edge Wings | 4×(n-2) = 32 | Wings on UF, UR, UB, UL edges |
| **Total** | **100** | = n² |

---

## Solving Constraints

### Move Restrictions by Layer

As layers are solved, available moves become restricted:

| After Solving | Forbidden Moves | Available Moves |
|---------------|-----------------|-----------------|
| Layer 1 | D | U, u, F, R, B, L, inner slices |
| Layer 2 | D, d | U, u, F, R, B, L, deeper slices |
| Layer k | D, d, 3d, ..., kd | U, u, ..., outer + deeper slices |
| Layer n-1 | All except U, u | U, u only |

### Implication
The last layer (layer n) must be solved using only U-layer moves and possibly the u-slice, similar to how 3x3 last-layer methods work.

---

## Proposed Solver Architecture

### Class Hierarchy

```
LayerByLayerNxNSolver (extends BaseSolver)
├── Implements: Solver protocol
├── Components:
│   ├── LayerSolverFactory → creates layer-specific solvers
│   ├── FirstLayerSolver (Layer 1)
│   │   ├── CentersSolver (for D-face centers)
│   │   ├── CornersSolver (for D-layer corners)
│   │   └── EdgesSolver (for D-face edges)
│   ├── MiddleLayerSolver (Layers 2 to n-1)
│   │   ├── RingCentersSolver (for side-face centers in this slice)
│   │   └── EdgeWingSolver (for 4 edge wings in this slice)
│   └── LastLayerSolver (Layer n)
│       ├── CentersSolver (for U-face centers)
│       ├── EdgesSolver (for U-face edges)
│       └── CornersSolver (for U-layer corners)
```

### Layer Abstraction

```python
class Layer:
    """Represents a horizontal layer of the cube."""

    def __init__(self, cube: Cube, layer_index: int):
        self.cube = cube
        self.index = layer_index  # 1 to n
        self.n = cube.size

    @property
    def is_first_layer(self) -> bool:
        return self.index == 1

    @property
    def is_last_layer(self) -> bool:
        return self.index == self.n

    @property
    def is_middle_layer(self) -> bool:
        return not self.is_first_layer and not self.is_last_layer

    def get_centers(self) -> list[CenterSlice]:
        """Get all center pieces in this layer."""
        ...

    def get_corners(self) -> list[CornerSlice] | None:
        """Get corners (only for first/last layers)."""
        ...

    def get_edge_wings(self) -> list[EdgeWing]:
        """Get edge wings in this layer."""
        ...

    def is_solved(self) -> bool:
        """Check if all pieces in this layer are in position."""
        ...
```

---

## Solving Steps (Detailed)

### Layer 1 (D face)

**Step 1.1: D-face Centers**
- Goal: Place all (n-2)² center pieces on D face
- Method: Build centers using R/L/F/B face turns and slice moves
- Similar to: Current NxNCenters but limited to one face

**Step 1.2: D-layer Corners**
- Goal: Position and orient 4 D-layer corners (DFL, DFR, DBL, DBR)
- Method: Use beginner method corner insertion or advanced techniques
- Key: Must not disturb D-face centers

**Step 1.3: D-face Edges**
- Goal: Pair and place all wings on DF, DR, DB, DL edges
- Method: Pair wings using slice moves, insert into position
- Similar to: Current NxNEdges but only for D-face edges

---

### Layer k (Middle layer, 2 ≤ k ≤ n-1)

**Step k.1: Ring Centers**
- Goal: Place 4×(n-2) center pieces on F/R/B/L faces at depth k
- Method: Use available slice moves and face turns
- Constraint: Cannot use moves that affect layers 1 to k-1

**Step k.2: Edge Wings**
- Goal: Place 4 edge wings (one from each of FL, FR, BL, BR edges)
- Method: Insert wings using commutators or specific algorithms
- These wings are at depth k from the D face

---

### Layer n (U face)

**Step n.1: U-face Centers**
- Goal: Place all (n-2)² center pieces on U face
- Method: Only U and possibly u moves available
- This is essentially an OLL-like step for centers

**Step n.2: U-face Edges**
- Goal: Pair and orient all wings on UF, UR, UB, UL edges
- Method: Edge orientation + permutation with restricted moves
- May need special algorithms for edge parity

**Step n.3: U-layer Corners**
- Goal: Position and orient 4 U-layer corners
- Method: Standard last-layer corner algorithms (OLL/PLL style)
- May need corner parity fix for even cubes

---

## Algorithm Requirements

### For First Layer
- Cross algorithms (D-face cross)
- Corner insertion algorithms
- Edge wing pairing (using inner slices)

### For Middle Layers
- Center commutators (3-cycle centers without disturbing lower layers)
- Edge wing commutators (3-cycle wings)
- May need "safe" slice sequences

### For Last Layer
- OLL-style algorithms for U-face centers
- Edge orientation algorithms
- Corner orientation (similar to 3x3 OLL)
- Permutation algorithms (similar to 3x3 PLL)
- Parity algorithms (if needed for even cubes)

---

## Comparison with Existing Solvers

| Aspect | Reduction Method | Layer-by-Layer |
|--------|-----------------|----------------|
| Move count | Lower | Higher |
| Conceptual simplicity | Medium | High |
| Memory (algorithms) | Medium | Higher |
| Parallelism | Centers/edges separate | Sequential layers |
| Partial progress visible | Less clear | Very clear |
| Suitable for | Speed solving | Learning, demonstration |

---

## Implementation Plan

### Phase 1: Foundation
- [ ] Create `Layer` class to represent horizontal cube layers
- [ ] Add methods to query pieces by layer
- [ ] Create `LayerByLayerNxNSolver` skeleton

### Phase 2: First Layer Solver
- [ ] Implement D-face center solver
- [ ] Implement D-layer corner solver
- [ ] Implement D-face edge solver
- [ ] Test on 4x4, 5x5

### Phase 3: Middle Layer Solver
- [ ] Implement ring center solver with constraints
- [ ] Implement edge wing solver with constraints
- [ ] Test layer-by-layer progression

### Phase 4: Last Layer Solver
- [ ] Implement U-face center solver (constrained)
- [ ] Implement edge solver (orientation + permutation)
- [ ] Implement corner solver (OLL + PLL style)
- [ ] Handle parity cases

### Phase 5: Integration
- [ ] Add to `Solvers` factory
- [ ] Add `SolverName.LAYER_BY_LAYER` enum
- [ ] Create tests for various cube sizes
- [ ] Performance comparison with reduction

---

## Open Questions

1. **Layer direction:** Should we solve D→U or U→D? (D→U seems more natural)

2. **Parity handling:** How to detect and fix parity in this method?
   - Edge parity: May appear in last layer
   - Corner parity: May appear in last layer (even cubes)

3. **Algorithm library:** Need to develop/collect algorithms that work with move restrictions

4. **Odd vs Even cubes:** Different handling needed?

5. **Optimization:** Can we optimize the middle layer solving to reduce moves?

---

## Layer 2 Center Solving - Detailed Design

> **Status:** Planning (2025-12-25)

### Coordinate System Mapping

Understanding how horizontal layers map to center slice coordinates is critical.

#### Center Slice Coordinate System

Each face uses `(row, column)` indexing:
- `row` ranges from 0 to n_slices-1 (top to bottom when looking at face)
- `column` ranges from 0 to n_slices-1 (left to right)
- Origin `(0,0)` is **top-left** of the face

```
Looking at F face (from outside):
    ┌───────────────────┐
    │ (0,0) (0,1) (0,2) │  ← row 0 (TOP)
    │ (1,0) (1,1) (1,2) │  ← row 1 (MIDDLE)
    │ (2,0) (2,1) (2,2) │  ← row 2 (BOTTOM)
    └───────────────────┘
       ↑                ↑
    col 0            col 2
```

#### Horizontal Slice to Center Row Mapping

**Important:** Slice indices are 0-based: `slice_index = 0 to n_slices-1`

For a 5x5 cube (n=5, n_slices=3):

```
Side view (looking at cube from right):

    U face (top)
    ┌─────────────────┐
    │     row 0       │  ← slice_index = 2 (closest to U)
    │     row 1       │  ← slice_index = 1 (middle)
    │     row 2       │  ← slice_index = 0 (closest to D)
    └─────────────────┘
    D face (bottom, Layer 1 - already solved)

Mapping formula (for side faces F, R, B, L):
    slice_index = 0 to n_slices-1
    row_index = n_slices - 1 - slice_index
             = (n - 2) - 1 - slice_index
             = n - 3 - slice_index

Example for 5x5 (n=5, n_slices=3):
    slice 0 → row = 3 - 1 - 0 = 2 (bottom row, closest to D)
    slice 1 → row = 3 - 1 - 1 = 1 (middle row)
    slice 2 → row = 3 - 1 - 2 = 0 (top row, closest to U)
```

**Key insight:** We solve slices bottom-up (0 → n_slices-1), which means:
- First solve row 2 (bottom) on all side faces
- Then solve row 1 (middle)
- Finally solve row 0 (top)

#### Ring Centers Definition

For slice s (0 to n_slices-1), "ring centers" means:
- The row of centers at `row = n_slices - 1 - s` on faces F, R, B, L
- Total pieces: `4 × n_slices` per slice (one row on each of 4 faces)

```
Ring for slice 0 on 5x5 (row 2 of each side face):

         ┌───────────┐
         │  U face   │
    ┌────┴───────────┴────┐
    │ L  │    F      │  R │
    │    │ [2,0][2,1][2,2] │ ← slice 0 ring (bottom row)
    └────┬───────────┬────┘
         │  D face   │  (Layer 1 - already solved)
         └───────────┘

Ring for slice 1 on 5x5 (row 1 of each side face):

         ┌───────────┐
         │  U face   │
    ┌────┴───────────┴────┐
    │ L  │    F      │  R │
    │    │ [1,0][1,1][1,2] │ ← slice 1 ring (middle row)
    └────┬───────────┬────┘
         │  D face   │
         └───────────┘
```

---

### Layer 2 Center Solving Challenges

#### Challenge 1: Partial Face Solving

**Problem:** `NxNCenters.solve_single_face()` solves the **entire** face center. For Layer 2, we only need to solve **one row** on each of 4 faces.

**Impact:** Cannot directly reuse `solve_single_face()` for middle layers.

**Approach:** Create a new method `solve_ring_centers(layer_index)` that:
- Iterates only over centers in the target row
- Uses commutators to bring pieces from source positions

#### Challenge 2: Move Restrictions

**Problem:** After Layer 1 is solved, D face cannot be rotated. Some commutators in `NxNCenters` use D face rotations.

**Current NxNCenters behavior:**
- Brings faces to front position
- Rotates cube to access all source faces
- Uses `B[1:n]` rotations which DON'T disturb D corners/edges

**Good news:** The `_block_communicator()` and `_swap_slice()` methods use inner slices and F rotations, which preserve D face.

**Approach:** Use `preserve_cage=True` mode which already exists in NxNCenters for cage solver.

#### Challenge 3: Source Center Location

**Problem:** Where are the source centers for Layer 2?

**Analysis for Layer 2:**
```
Needed: Centers with correct colors for F/R/B/L row 2

Possible sources:
1. U face centers (any position)
2. Other rows on F/R/B/L (rows 0, 1)
3. D face centers (BUT D is already solved - these are correct!)
```

**Key insight:** D face centers are already solved, so:
- D face has the correct white (Layer 1 color) centers
- Source centers for Layer 2 must come from U face or other rows on side faces

#### Challenge 4: Face Orientation During Solving

**Problem:** NxNCenters works by:
1. Bringing target face to front
2. Bringing source faces to up/back
3. Using commutators

For ring solving:
- We're solving 4 faces at once (the ring)
- Each face's row 2 needs correct colors

**Approach options:**
1. **Rotate cube:** Bring each face to front, solve that row, rotate to next
2. **Work in place:** Use slice moves without rotating cube
3. **Hybrid:** Minimal cube rotation with adapted algorithms

#### Challenge 5: Even Cube Face Tracking

**Problem:** On even cubes (4x4, 6x6), there's no fixed center piece. The FaceTracker uses majority voting to determine which color belongs to which face.

For Layer 2:
- Layer 1 centers are solved (face color is now fixed for D)
- But other faces still have scrambled centers
- How do we know what color goes on F row 2?

**Solution:** Use existing FaceTracker system - it tracks face colors even on scrambled cubes.

---

### Proposed Approach for Slice Centers

#### High-Level Strategy

```python
def _solve_slice_centers(self, slice_index: int, th: FacesTrackerHolder) -> None:
    """Solve the ring of centers for a middle slice.

    Args:
        slice_index: 0 to n_slices-1 (0 = closest to D, n_slices-1 = closest to U)
        th: FacesTrackerHolder for face color tracking
    """
    # Calculate which row on side faces corresponds to this slice
    n_slices = self.cube.n_slices
    row_index = n_slices - 1 - slice_index  # slice 0 → bottom row

    # For each side face (F, R, B, L)
    for face_tracker in self._get_side_face_trackers(th):
        target_face = face_tracker.face
        target_color = face_tracker.color

        # Check which centers in this row need fixing
        for col in range(n_slices):
            center = target_face.center.get_center_slice((row_index, col))
            if center.color != target_color:
                # Find and move correct piece using commutator
                self._fix_ring_center(target_face, row_index, col, target_color, th)

def _solve_all_middle_slices(self, th: FacesTrackerHolder) -> None:
    """Solve all middle slice centers, bottom to top."""
    for slice_index in range(self.cube.n_slices):
        self._solve_slice_centers(slice_index, th)
```

#### Key Components Needed

1. **Slice-to-row conversion:**
   ```python
   def slice_to_row(self, slice_index: int) -> int:
       """Convert slice index (0=bottom) to row index on side faces."""
       return self.cube.n_slices - 1 - slice_index
   ```

2. **Row-based center query:**
   ```python
   def get_row_centers(face: Face, row: int) -> list[CenterSlice]:
       return [face.center.get_center_slice((row, c))
               for c in range(face.center.n_slices)]
   ```

3. **Source center finder:**
   ```python
   def find_source_center(color: Color, exclude_rows: set[int], th: FacesTrackerHolder) -> tuple[Face, int, int]:
       # Search U face first (best source - no restrictions)
       # Then search rows ABOVE current slice on side faces
       # Never use D face (Layer 1 is solved)
       # Never use already-solved rows (below current slice)
       ...
   ```

4. **Ring-preserving commutator:**
   - Adapt `_block_communicator()` to work with row constraints
   - Ensure moves don't disturb completed slices (rows below current)

#### Implementation Order

1. **Add `slice_to_row()` helper**
2. **Create `_solve_slice_centers(slice_index)` method**
3. **Create `_is_slice_centers_solved(slice_index)` check**
4. **Add `SolveStep.LBL_SLICE_CTR` enum value**
5. **Write tests for various cube sizes**
6. **Generalize to solve all slices in order**

---

### E-Slice Relationship

The E slice (horizontal middle) directly relates to ring centers:

```python
# E slice index → center row index
# For Slice.E with slice_index=i:
#   - Affects row i on some faces (depends on face orientation)

# Example: E[0] slice on 5x5
# - When rotated, centers in certain rows move between F/R/B/L
```

**Key insight:** E slice moves preserve Layer 1 (D face) completely. We can use E slices freely for Layer 2+ solving.

---

## References

- [PuzzleMax13 YouTube Channel](https://www.youtube.com/@puzzlemax13)
- [SpeedSolving: Layer-by-Layer Discussion](https://www.speedsolving.com/threads/solving-the-4x4x4-cube-layer-by-layer.18490/)
- [Ruwix: Big Cube Solutions](https://ruwix.com/twisty-puzzles/big-cubes-nxnxn-solution/)
- [Kenneth's Big Cube Method](https://www.speedsolving.com/threads/kenneths-big-cube-method-explained.4073/)
