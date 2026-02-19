# Non-Reduction Methods for Big Cubes - Research Document

## Overview

This document summarizes research on non-reduction solving methods for NxN cubes.
It serves as a reference for implementing direct solvers.

## Key Finding: The "Layer-by-Layer" Misconception

The term "Layer-by-Layer" for big cubes is often misunderstood:
- On 3x3, Layer-by-Layer means: bottom layer → middle layer → top layer
- On big cubes, this doesn't translate directly because:
  - Centers are 2D grids, not single pieces
  - Edges have multiple wings
  - The concept of "layer" becomes ambiguous

**The actual non-reduction methods are:**
1. **Cage Method** - Most documented, solves edges+corners first, centers last
2. **K4 Method** - Hybrid with blockbuilding
3. **Columns Method** - Direct solve with F4L approach

---

## Method 1: Cage Method (Primary Non-Reduction Approach)

### Concept

Solve the **edges and corners first**, creating a "cage" around the centers.
Then solve centers last using commutators.

```
Standard Reduction:           Cage Method:
─────────────────────         ─────────────────────
1. Centers first              1. Edges + Corners first (the "cage")
2. Edges second               2. Centers last (in the cage)
3. 3x3 solve (corners)
```

### Why It's Called "Cage"

After solving edges and corners, the centers appear to be "trapped" inside:

```
After edges+corners solved:

    ┌─────────────────┐
    │  E ─── E ─── E  │     E = solved edge
    │  │     │     │  │
    │  E ─ [???] ─ E  │     ??? = unsolved centers (caged)
    │  │     │     │  │
    │  E ─── E ─── E  │
    └─────────────────┘
```

### Key Advantages

1. **Parity-Free**: Centers can always be solved with commutators regardless of permutation
2. **Simple Algorithms**: Only needs a few commutator patterns
3. **Scales to Any Size**: Works on 4x4 through 111x111
4. **Predictable**: Same approach works consistently

### Detailed Steps

#### Step 1: Solve Edges (Without Caring About Centers)

For each edge position, pair the wings:
- On 5x5: Each edge has 3 pieces (2 wings + 1 midge)
- Use modified 3x3 algorithms that allow slice moves

```
Key insight: You can freely turn inner slices because
centers don't matter yet!

Example for 5x5:
- Use wide moves (Rw, Uw) without worrying about centers
- Pair wings and midges together
- Place edges in correct positions
```

**Algorithms used (modified from 3x3):**
- `U R U' R' U' F' U F` → becomes `u R u' R' u' F' u F` (with slices)
- Same concept, but you can include inner layers

#### Step 2: Solve Corners

Use standard 3x3 corner algorithms:
- Corners are identical to 3x3 corners
- F2L-style insertion
- Or solve corners after all edges

**Note**: Can use any 3x3 method for corners (CFOP, Roux, etc.)

#### Step 3: Solve Centers (Using Commutators)

This is where the magic happens. Centers are solved using pure commutators.

**Why commutators work perfectly here:**
- Edges and corners are already solved
- Commutators cycle 3 centers without affecting edges/corners
- Any center permutation can be solved with 3-cycles

**Basic Center Commutator:**
```
[Rw U Rw', D2]  = Rw U Rw' D2 Rw U' Rw' D2

Effect: 3-cycles centers between U and D faces
```

**General Pattern:**
```
[A, B] = A B A' B'

Where:
  A = slice move (brings centers into position)
  B = outer layer move (rotates them)
```

### Cage Method Pseudo-Code

```
solve_cage_method():
    # Phase 1: Build the cage (edges + corners)
    solve_all_edges()      # Pair wings, ignore centers
    solve_all_corners()    # Standard 3x3 corner methods

    # Phase 2: Fill the cage (centers)
    for each face in [D, U, F, B, L, R]:
        solve_centers_on_face(face)

solve_all_edges():
    # Similar to reduction edge pairing, but more freedom
    # because we don't care about centers

    for each edge_position:
        if not edge_is_complete(edge_position):
            # Find wings that belong to this edge
            wings = find_wings_for_edge(edge_position)

            # Use wide moves freely to pair them
            pair_wings(wings)

            # Place completed edge
            insert_edge(edge_position)

solve_all_corners():
    # Identical to 3x3 solving
    # Can use F2L, CFOP last layer, or any preferred method

    solve_first_layer_corners()
    solve_last_layer_corners()  # OLL + PLL for corners

solve_centers_on_face(target_face):
    target_color = get_center_color(target_face)  # From fixed center on odd cubes

    # Bring target face to front for easier manipulation
    orient_cube(target_face → FRONT)

    for each center_position (r, c) on front:
        if front.center[r,c].color != target_color:
            # Find a center of correct color elsewhere
            source = find_center_of_color(target_color)

            # Use commutator to cycle it into position
            execute_center_commutator(source → target_position)
```

---

## Method 2: K4 Method (Hybrid Approach)

### Concept

Created by Thom Barlow. Combines:
- **Reduction** for centers (partial)
- **Blockbuilding** for structure
- **Direct solving** with commutators for edges

### Steps

1. **Build two opposite center groups** (e.g., U and D centers)
2. **Blockbuild** a 1x(N-1)xN block on one side
3. **Finish remaining centers** without breaking the block
4. **CLL** (Corners of Last Layer) to solve corners
5. **Commutators** to solve all edges

### Why K4 is Different

- More structured than pure Cage
- Uses blockbuilding for efficiency
- Still avoids full reduction parity

---

## Method 3: Columns Method

### Concept

A direct solve method that:
- Solves pieces directly (no reduction/orientation phases)
- Uses very few slice moves
- Finishes with commutators

### Steps

1. **F4L (First 4 Layers)**: Build first layer corners + middle edges
2. **Complete centers** column by column
3. **Finish with commutators** for remaining pieces

---

## Comparison of Methods

| Aspect | Reduction | Cage | K4 | Columns |
|--------|-----------|------|-----|---------|
| Centers solved | First | Last | Partial first | During |
| Parity issues | Yes (4x4, 6x6...) | No | Minimal | No |
| Move count | Low (~200-300) | Medium (~400-600) | Medium | Medium |
| Algorithm count | Many | Few | Medium | Few |
| Conceptual simplicity | Medium | High | Medium | Medium |
| Scales to large N | Yes | Yes | Somewhat | Yes |

---

## Recommendation for Implementation

Based on research, **Cage Method** is the best candidate because:

1. ✅ Clearly defined, well-documented steps
2. ✅ Completely parity-free
3. ✅ Uses commutators (which you wanted to implement)
4. ✅ Scales to any cube size
5. ✅ Reuses existing infrastructure (3x3 corner algorithms, edge pairing concepts)

### Proposed Implementation Structure

```
direct/
├── cage/
│   ├── __init__.py
│   ├── CageNxNSolver.py         # Main solver
│   ├── CageEdges.py             # Edge solving (phase 1a)
│   ├── CageCorners.py           # Corner solving (phase 1b)
│   ├── CageCenters.py           # Center solving with commutators (phase 2)
│   └── DESIGN.md                # Detailed design
```

---

## References

- [Speedsolving Wiki - Big Cube](https://www.speedsolving.com/wiki/index.php/Big_cube)
- [Speedsolving Wiki - Cage Method](https://www.speedsolving.com/wiki/index.php?title=Cage_Method)
- [Speedsolving Wiki - K4](https://www.speedsolving.com/wiki/index.php/K4)
- [MZRG - Columns Method](https://mzrg.com/rubik/methods/columns/)
- [Ruwix - Big NxN Solution](https://ruwix.com/twisty-puzzles/big-cubes-nxnxn-solution/)
- [Ryan Heise - Commutators](https://www.ryanheise.com/cube/commutators.html)
- [Speedsolving Forum - Cage Method for 5x5](https://www.speedsolving.com/threads/cage-method-for-the-5x5x5.51209/)

---

## Next Steps

1. Rename `layer_by_layer` package to `cage` (more accurate)
2. Create detailed pseudo-code for Cage method
3. Implement edge solving phase
4. Implement corner solving phase
5. Implement center solving with commutators
