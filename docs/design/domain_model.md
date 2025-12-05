# Cube Domain Model

> **Purpose:** Document the Rubik's cube domain model structure.
> **Last Updated:** 2025-12-05

---

## Core Philosophy

**Fixed Parts, Rotating Colors:** Unlike physical cubes where pieces move in 3D space, this model keeps all parts at FIXED POSITIONS and rotates only their COLORS. This simplifies state management and enables efficient algorithms.

---

## Object Hierarchy

```
Cube (size=3 for 3x3, size=4 for 4x4, etc.)
 │
 ├── 6 Faces (F, B, L, R, U, D)
 │    └── Face.slices → yields PartSlice objects
 │
 ├── 12 Edges   (Part) ─── shared by 2 faces
 ├── 8 Corners  (Part) ─── shared by 3 faces
 ├── 6 Centers  (Part) ─── owned by 1 face
 │
 └── cube.get_all_parts() → Collection[PartSlice]
```

---

## Class Hierarchy

```
Part (ABC)                    # Abstract base - Edge, Corner, Center
 ├── Edge                     # 2-face piece, contains EdgeWing slices
 ├── Corner                   # 3-face piece, contains 1 CornerSlice
 └── Center                   # 1-face piece, contains NxN CenterSlice grid

PartSlice (ABC)               # Abstract base - the wrapper around PartEdge
 ├── EdgeWing                 # 2 PartEdge objects (one per face)
 ├── CornerSlice              # 3 PartEdge objects (one per face)
 └── CenterSlice              # 1 PartEdge object

PartEdge                      # Smallest unit - single sticker on single face
```

---

## Part Types

### Part (Abstract Base)

The abstract parent of Edge, Corner, and Center. Parts are NEVER repositioned; only their colors change.

**Location:** `src/cube/domain/model/Part.py`

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `_cube` | Cube | Reference to parent cube |
| `_fixed_id` | PartFixedID | Immutable identifier (never changes) |
| `_colors_id_by_colors` | PartColorsID \| None | Cached current colors |
| `_colors_id_by_pos` | PartColorsID \| None | Cached position colors |

**Key Properties:**
| Property | Returns | Description |
|----------|---------|-------------|
| `colors_id` | PartColorsID | Actual colors currently on the part |
| `position_id` | PartColorsID | Colors it SHOULD have based on face positions |
| `in_position` | bool | True if `position_id == colors_id` |
| `match_faces` | bool | True if every PartEdge color matches its face color |
| `all_slices` | Iterator[PartSlice] | All PartSlice objects in this Part |

### Edge

**Purpose:** 2-sticker piece shared between exactly 2 faces.

**Location:** `src/cube/domain/model/Edge.py`

**Structure:**
- For 3x3: 1 EdgeWing slice
- For 4x4: 2 EdgeWing slices (outer, middle)
- For 5x5: 3 EdgeWing slices

**Example:**
```python
cube = Cube(3)
fu_edge = cube.front.edge_top  # Front-Up edge
assert fu_edge is cube.up.edge_bottom  # Same object! (shared)

wing = fu_edge.get_slice(0)  # EdgeWing
wing.e1  # PartEdge on Front face
wing.e2  # PartEdge on Up face
```

### Corner

**Purpose:** 3-sticker piece shared between exactly 3 faces.

**Location:** `src/cube/domain/model/Corner.py`

**Structure:** Always 1 CornerSlice (regardless of cube size).

**Example:**
```python
cube = Cube(3)
fru_corner = cube.fru  # Front-Right-Up corner
# Shared by 3 faces:
assert fru_corner is cube.front.corner_top_right
assert fru_corner is cube.right.corner_top_left
assert fru_corner is cube.up.corner_bottom_right

cs = fru_corner._slice  # CornerSlice with 3 PartEdge objects
```

### Center

**Purpose:** Center pieces on a single face (NxN grid for big cubes).

**Location:** `src/cube/domain/model/Center.py`

**Structure:**
- For 3x3: 1×1 grid (1 CenterSlice)
- For 4x4: 2×2 grid (4 CenterSlices)
- For 5x5: 3×3 grid (9 CenterSlices)

**Example:**
```python
cube = Cube(5)
center = cube.front.center
cs = center.get_slice((1, 1))  # Middle center piece
cs.color  # Color of that center sticker
```

---

## PartSlice Types

PartSlice wraps PartEdge objects. Each PartSlice belongs to one Part.

### PartSlice (Abstract Base)

**Location:** `src/cube/domain/model/_part_slice.py`

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `_cube` | Cube | Reference to cube |
| `_parent` | Part \| None | Parent Part (Edge, Corner, or Center) |
| `_index` | SliceIndex | Index in parent Part |
| `_edges` | Sequence[PartEdge] | 1, 2, or 3 PartEdge objects |
| `_fixed_id` | PartSliceHashID | Immutable identifier |
| `_colors_id_by_colors` | PartColorsID \| None | Cached colors |

**Key Properties:**
| Property | Returns | Description |
|----------|---------|-------------|
| `colors_id` | PartColorsID | Current colors of this slice |
| `colors` | PartSliceColors | Tuple of Color values |
| `match_faces` | bool | All PartEdge colors match their face |
| `fixed_id` | PartSliceHashID | Immutable identifier |

**Note:** PartSlice does NOT have `position_id` - only Part has that.

### EdgeWing

- **PartEdge count:** 2 (`e1`, `e2`)
- **Index type:** `int` (0 to n_slices-1)

### CornerSlice

- **PartEdge count:** 3
- **Index type:** `int` (always 0)

### CenterSlice

- **PartEdge count:** 1 (`edge`)
- **Index type:** `tuple[int, int]` (row, col)

---

## PartEdge

**Purpose:** Smallest cube element - single sticker on single face.

**Location:** `src/cube/domain/model/PartEdge.py`

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `_face` | Face | The face this sticker is on (never changes) |
| `_color` | Color | Current color (changes during rotations) |

---

## Identity System

### Three Types of IDs

| ID | Level | Type | Mutability | Description |
|----|-------|------|------------|-------------|
| `fixed_id` | Part & PartSlice | frozenset | Immutable | Physical location |
| `colors_id` | Part & PartSlice | frozenset[Color] | Changes | Current actual colors |
| `position_id` | Part only | frozenset[Color] | Changes | Colors SHOULD have |

### Example

```python
edge = cube.front.edge_top  # FU edge

# After scramble:
edge.colors_id      # Actual colors (e.g., {RED, YELLOW})
edge.position_id    # Should-be colors (for FU: {BLUE, YELLOW})
edge.in_position    # True if they match
edge.match_faces    # True if orientations also match
```

---

## What Does `cube.get_all_parts()` Return?

**Signature:** `def get_all_parts(self) -> Collection[PartSlice]`

Returns all unique PartSlice objects (deduplicated).

**For 3x3 cube:** 26 PartSlice objects
- 12 EdgeWing (12 edges × 1 slice)
- 8 CornerSlice (8 corners × 1 slice)
- 6 CenterSlice (6 faces × 1 center)

**For 4x4 cube:** 56 PartSlice objects
- 24 EdgeWing (12 edges × 2 slices)
- 8 CornerSlice (8 corners × 1 slice)
- 24 CenterSlice (6 faces × 2×2 grid)

---

## Part Sharing

Critical concept: Parts are shared between faces.

```python
# Edges shared by 2 faces
cube.front.edge_top is cube.up.edge_bottom  # True!

# Corners shared by 3 faces
cube.fru is cube.front.corner_top_right  # True!
cube.fru is cube.right.corner_top_left   # True!
cube.fru is cube.up.corner_bottom_right  # True!
```

When rotating a face, shared parts automatically reflect the change on adjacent faces.

---

## Caching System

Both Part and PartSlice cache color IDs for performance:

```python
@property
def colors_id(self) -> PartColorsID:
    if self._colors_id_by_colors is None:
        # Recompute from PartEdge colors
        self._colors_id_by_colors = frozenset(e.color for e in self._edges)
    return self._colors_id_by_colors
```

**Reset methods:**
- `reset_colors_id()` - Called after colors change
- `reset_after_faces_changes()` - Called after rotations

---

## Type Aliases

From `src/cube/domain/model/_elements.py`:

```python
PartColorsID = frozenset[Color]              # {WHITE, RED}
PartSliceHashID = frozenset[Hashable]        # {0, FaceName.F, FaceName.U}
PartFixedID = frozenset[PartSliceHashID]     # Multiple PartSliceHashID
SliceIndex = int | tuple[int, int]           # Edge index or center (row, col)
PartSliceColors = tuple[Color, ...]          # 1, 2, or 3 colors
```

---

## Summary Table

| Class | Contains | Has colors_id | Has position_id | Count in 3x3 |
|-------|----------|---------------|-----------------|--------------|
| Part (Edge) | EdgeWing[] | Yes | Yes | 12 |
| Part (Corner) | CornerSlice | Yes | Yes | 8 |
| Part (Center) | CenterSlice[][] | Yes | Yes | 6 |
| EdgeWing | 2 PartEdge | Yes | No | 12 |
| CornerSlice | 3 PartEdge | Yes | No | 8 |
| CenterSlice | 1 PartEdge | Yes | No | 6 |
| PartEdge | - | No | No | 54 |
