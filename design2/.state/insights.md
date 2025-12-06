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

## Verified: ID Usage in Solvers

**Source:** Solver code analysis (2025-12-06)

### Phase 1 Solver (NxNEdges.py)
```python
# Works at SLICE level - not Part level!
a_slice = edge.get_slice(i)
a_slice_id = a_slice.colors_id  # ← Slice colors_id, NOT edge.colors_id!

# Checks reduction status
if edge.is3x3:
    # Edge is solved (all slices aligned)
```

### Phase 2 Solver (L1Cross.py)
```python
# Works at PART level - assumes is3x3 = True
color_codes = Part.parts_id_by_pos(wf.edges)  # ← position_id usage
source_edge = cube.find_edge_by_color(color_id)  # ← colors_id usage
if source_edge.match_faces:  # ← Only valid when is3x3!
    continue
```

### Tracker.py (Part Tracking)
```python
# Tracks by colors_id, finds by position_id
EdgeTracker.of_position(edge)  # Creates tracker from edge.position_id
tracker.actual  # Finds part by colors_id
tracker.position  # Finds slot by position_id
```

**Conclusion:** My understanding of the ID system is VERIFIED by solver usage patterns.

---

## Edge Coordinate System: right_top_left_same_direction

**Source:** Human diagram (coor-system-doc/right-top-left-coordinates.jpg) + code analysis (2025-12-06)

### The Problem

When rotating a face, colors move between edges. But in NxN cubes, edges have multiple slices.
Which slice index on the source edge maps to which slice index on the target edge?

### The Solution

Each face has a "left-to-right" (R) and "bottom-to-top" (T) direction.
When two faces share an edge, these directions may:
- **Agree** (`right_top_left_same_direction = True`): slice i → slice i
- **Disagree** (`right_top_left_same_direction = False`): slice i → slice (n-1-i)

### Edge Direction Mapping

```
SAME DIRECTION (8 edges):     OPPOSITE DIRECTION (4 edges):
  F-U, F-L, F-R, F-D            L-U
  L-D, L-B                      U-B
  R-B, U-R                      D-R, D-B
```

**Pattern:** All Front edges are SAME. Back edges meeting U or D are OPPOSITE.

### Code Usage

```python
# Edge.py - automatic index conversion
def get_ltr_index_from_slice_index(self, face, i):
    if self.right_top_left_same_direction:
        return i  # Direct mapping
    else:
        if face is self._f1:
            return i  # f1 is reference
        else:
            return self.inv_index(i)  # f2: INVERT!
```

### Why It Matters

Without this flag, Face.rotate() would copy slices to wrong positions, corrupting the cube.
With this flag, rotation works correctly for ANY NxN cube.

**Developer note:** "This is the most complicated thing to understand - without it I couldn't visualize
and correctly rotate slices."

---

## PartEdge Attribute System (CRITICAL for Animation!)

**Source:** PartEdge.py, Face.py, OpAnnotation.py, FaceTracker.py (2025-12-06)

### Three Attribute Types

PartEdge has three distinct dictionary attributes for different purposes:

| Attribute | Moves with Color? | Purpose |
|-----------|-------------------|---------|
| `attributes` | No (structural) | Physical slot properties |
| `c_attributes` | **YES** | Track pieces as they move |
| `f_attributes` | **NO** | Mark destination slots |

### 1. `attributes` - Structural/Positional

Set ONCE during `Face.finish_init()`:
- `"origin"` (bool) - Marks slice 0 on each edge
- `"on_x"` (bool) - X direction marker
- `"on_y"` (bool) - Y direction marker
- `"cw"` (int) - Clockwise rotation index

**Never moves** - describes the physical slot position.

### 2. `c_attributes` - Color-Associated (KEY INSIGHT!)

**COPIED during `PartEdge.copy_color()`** - this is the magic!

```python
def copy_color(self, source):
    self._color = source._color
    self.c_attributes.clear()
    self.c_attributes.update(source.c_attributes)  # <-- COPIED!
```

**Use case:** Track a specific sticker as it moves around:
```python
# Put a marker
edge.c_attributes["track_key"] = True
# After rotation, find where it went
def pred(s): return "track_key" in s.edge.c_attributes
```

Used by: FaceTracker.by_center_piece(), VMarker.C1

### 3. `f_attributes` - Fixed to Slot

**NOT copied during rotation** - stays at the physical position!

**Use case:** Mark a destination (where piece should go):
```python
# Mark destination slot
target.f_attributes["dest"] = True
# After rotation, marker is still there
```

Uses `defaultdict(bool)` so missing keys return False.

Used by: OpAnnotation for VMarker.C2

### Animation System Integration

The annotation system uses both attribute types together:

| AnnWhat Value | Attribute | Marker | Visual Effect |
|---------------|-----------|--------|---------------|
| `AnnWhat.Moved` | c_attributes | C1 | Marker follows sticker |
| `AnnWhat.FixedPosition` | f_attributes | C2 | Marker stays at destination |
| `AnnWhat.Both` | Both | Both | Shows source AND target |

**Example animation flow:**
1. Mark source piece with c_attributes marker (follows it)
2. Mark destination with f_attributes marker (stays put)
3. Execute rotation
4. Both markers now at same position = piece arrived!

### Why Three Types?

This is a brilliant design for puzzle visualization:
- **"Track this piece"** = put marker in c_attributes (moves with piece)
- **"Mark destination"** = put marker in f_attributes (stays at slot)
- **"Know slot position"** = read attributes (coordinate system)

---

## Questions Still to Investigate

See `.state/task-queue.md` for full list.

High priority:
1. Face.rotate() mechanics (partially understood via right_top_left analysis)
2. Slice class (M, E, S) rotation

---

## Documentation Created

- `design2/model-id-system.md` - Visual diagrams of ID system
- `design2/edge-coordinate-system.md` - right_top_left_same_direction explained
- `design2/partedge-attribute-system.md` - Three attribute types for animation

---

*(More insights will be added as research progresses)*
