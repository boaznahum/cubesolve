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

## References

- [PuzzleMax13 YouTube Channel](https://www.youtube.com/@puzzlemax13)
- [SpeedSolving: Layer-by-Layer Discussion](https://www.speedsolving.com/threads/solving-the-4x4x4-cube-layer-by-layer.18490/)
- [Ruwix: Big Cube Solutions](https://ruwix.com/twisty-puzzles/big-cubes-nxnxn-solution/)
- [Kenneth's Big Cube Method](https://www.speedsolving.com/threads/kenneths-big-cube-method-explained.4073/)
