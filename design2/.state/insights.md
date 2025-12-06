# Insights - What I've Learned

This file captures key understandings gained during the documentation project.

---

## Project Architecture (from README)

**Source:** README.md (2025-12-06)

Architecture layers:
- **Entry Points** - main_pyglet.py, main_headless.py, main_any_backend.py
- **GUI Layer** - Window, Viewer, Animation Manager
- **Application Core** - App, Cube, Operator, Solver, ViewState
- **Backend Abstraction** - Renderer, EventLoop protocols

**Model package location:** `src/cube/domain/model/`

**Solvers (order matters - reflects two-phase solving):**
1. `nxn_centers.py` - Big cube centers (Phase 1)
2. `nxn_edges.py` - Big cube edges (Phase 1)
3. `l1_cross.py`, `l1_corners.py` - Layer 1 (Phase 2)
4. `l2.py` - Layer 2
5. `l3_cross.py`, `l3_corners.py` - Layer 3

**Algs:** in algs.py - can be combined, inverted, sliced, multiplied

**Diagrams available:** readme_files/ folder contains architecture diagrams

---

## Model Deep Dive (from code reading)

**Source:** Direct code reading of model/ package (2025-12-06)

### Core Design Philosophy

**CRITICAL INSIGHT: Fixed Parts, Rotating Colors**
- Unlike physical cubes where pieces move in 3D space
- This model keeps all parts at FIXED POSITIONS
- Only their COLORS rotate/change during operations
- Benefits: Simpler state management, faster queries, easier validation

### Object Hierarchy

```
Cube
 |-- 6 Faces (F, B, L, R, U, D)
 |   |-- 4 Edges (shared with adjacent faces)
 |   |-- 4 Corners (shared with 2 adjacent faces)
 |   +-- 1 Center (NxN grid for big cubes)
 |
 |-- 12 Edges (shared between pairs of faces)
 |   +-- EdgeWing slices (N-2 slices per edge)
 |
 |-- 8 Corners (shared between triples of faces)
 |   +-- CornerSlice (always 1 per corner)
 |
 +-- 3 Slices (M, E, S - middle layers)
```

### Class Hierarchy

```
Part (abstract base)
 |-- Edge      -> contains N-2 EdgeWing slices
 |-- Corner    -> contains 1 CornerSlice
 +-- Center    -> contains (N-2)x(N-2) CenterSlice grid

PartSlice (abstract base)
 |-- EdgeWing    -> 2 PartEdges (belongs to 2 faces)
 |-- CornerSlice -> 3 PartEdges (belongs to 3 faces)
 +-- CenterSlice -> 1 PartEdge (belongs to 1 face)

PartEdge -> the smallest unit, a "sticker" on a face
```

### Part Sharing (Critical Concept!)

**Edges are shared between 2 faces:**
```python
front.edge_top is up.edge_bottom  # True! Same object
```

**Corners are shared between 3 faces:**
```python
front.corner_top_right is right.corner_top_left is up.corner_bottom_right  # True!
```

When you rotate a face, the colors change on shared parts, automatically updating all adjacent faces.

---

## The ID System (CRITICAL!)

**Source:** Part.py, _part_slice.py (2025-12-06)

### Three Types of IDs

1. **`fixed_id`** (PartFixedID)
   - Based on face NAMES (FaceName enum values)
   - NEVER changes - identifies the physical position in the cube
   - Same across all cube instances
   - Formula: `frozenset(tuple([index]) + tuple(face.name for each edge))`

2. **`position_id`** (PartColorsID)
   - Colors of the FACES the part is currently ON
   - Based on face center colors (not part colors!)
   - Changes ONLY during slice/whole-cube rotations (M, E, S, x, y, z)
   - Does NOT change during face rotations (F, R, U, etc.)
   - Formula: `frozenset(edge.face.color for each edge)`

3. **`colors_id`** (PartColorsID)
   - The ACTUAL colors currently showing on the part
   - Changes during ANY rotation
   - Formula: `frozenset(edge.color for each edge)`

### Key Relationships

- `in_position`: True when `position_id == colors_id` (part is in correct slot)
- `match_faces`: True when ALL colors match their respective faces (correctly oriented)

---

## Two-Phase Architecture - Deep Understanding

**Source:** Human developer + code analysis (2025-12-06)

### Connection to the ID System

**Phase 1 (Big Cube - before reduction):**
- Working with part SLICES (EdgeWing, CenterSlice)
- `colors_id` is NOT meaningful at Part level
- Why? Different slices of same edge may have different colors!
- `is3x3` property returns False

**Phase 2 (After reduction - 3x3 mode):**
- All slices of an edge have SAME colors (aligned)
- `colors_id` NOW meaningful
- `is3x3` property returns True
- Part methods like `colors_id`, `in_position`, `match_faces` are valid

### The `is3x3` Property Chain

```python
Edge.is3x3:   All slices have same colors (slices aligned)
Center.is3x3: All center slices have same color (center solved)
Face.is3x3:   All parts on face are 3x3
Cube.is3x3:   All faces are 3x3 AND cube is in BOY orientation
```

### Which Methods are Phase-Dependent?

**Always valid (both phases):**
- `fixed_id` - based on structure, not colors
- Individual slice operations
- `position_id` - based on face centers

**Only valid in Phase 2 (after reduction):**
- `colors_id` at Part level (not PartSlice)
- `in_position` at Part level
- `match_faces` at Part level
- `color` property on Center, Edge (uses middle slice)

---

## Questions Still to Investigate

1. How does rotation actually work mechanically? (traced through Face.rotate())
2. How does the Slice class (M, E, S) work?
3. What is `right_top_left_same_direction` in Edge?
4. How does the solver know when reduction is complete?

---

*(More insights will be added as research progresses)*
