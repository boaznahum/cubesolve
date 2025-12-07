# Q11: ModernGLCubeViewer Code Quality Cleanup Plan

## Problem Analysis

### Current State (ModernGLCubeViewer.py)
- **1211 lines** in a single file with no layer separation
- Magic numbers everywhere (50.0, 0.02, 4.0, etc.)
- No coordinate system documentation
- Code duplication in 3x3 vs NxN methods
- Long methods (90-130 lines)
- Hard to understand face transforms without context

### Legacy Implementation (Beautiful Code)
The legacy `GCubeViewer` uses elegant layer separation:

```
GCubeViewer
    └── _Board          (manages all faces, coordinate system)
        └── _FaceBoard  (manages one face, 9 cells)
            └── _Cell   (manages one cell, facets, markers)
```

**Key Features of Legacy Code:**

1. **ASCII Diagrams for Coordinates:**
```
Face coordinates:
       0  1  2
   0:     U
   1:  L  F  R
   2:     D
   3:     B

Cell layout:
 0,0 | 0,1 | 0,2
 ---------------
 1,0 | 1,1 | 1,2
 ---------------
 2,0 | 2,1 | 2,2
```

2. **Named Constants:**
```python
_CELL_SIZE: int = config.CELL_SIZE
_CORNER_SIZE = config.CORNER_SIZE
_FACE_SIZE = 3
```

3. **Self-Documenting Face Creation:**
```python
# left_bottom is in units of faces, we convert to pixel size
self._create_face(lambda: cube.up, [0, 1, 1], [1, 0, 0], [0, 0, -1], [0, 1, 0])
# -0.75 from x location, so we can see it in isometric view
self._create_face(lambda: cube.left, [-0.75, 0, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])
```

4. **Geometry Classes:**
```python
class _RectGeometry:
    _two_d_draw_rect: Sequence[ndarray]
    three_d_search_box: ...
```

---

## Refactoring Plan

### Phase 1: Document Current Magic Numbers

Add comments explaining current hardcoded values:

```python
# Current magic numbers to document:
FACE_OFFSET = 50.0  # Half the cube size (cube spans -50 to +50 on each axis)
gap = cell_size * 0.02  # 2% gap between cells for grid lines
line_width = 4.0  # Border thickness matching legacy GL
shadow_offsets:
    L: -0.75  # 75% face width to the left (isometric visibility)
    D: -0.5   # 50% face height below
    B: -2.0   # 2 face depths behind
```

### Phase 2: Extract Constants to Module Level

Create named constants at module level with docstrings:

```python
# === Cube Geometry Constants ===
# The cube is centered at origin, spanning [-HALF_CUBE_SIZE, +HALF_CUBE_SIZE]
HALF_CUBE_SIZE = 50.0  # Each face is at distance 50 from origin

# Cell rendering
CELL_GAP_RATIO = 0.02  # 2% gap between cells for grid effect
BORDER_LINE_WIDTH = 4.0  # Black border around each cell

# Shadow offsets (in face units) for isometric visibility
# When shadow mode is enabled (F10/F11/F12), we render duplicate faces
SHADOW_OFFSET_L = -0.75  # Left face: 75% to the left
SHADOW_OFFSET_D = -0.50  # Down face: 50% below
SHADOW_OFFSET_B = -2.00  # Back face: 2 face-depths behind
```

### Phase 3: Add Coordinate System Documentation

Add ASCII diagrams matching legacy style:

```python
"""
ModernGL Cube Viewer - Coordinate System
========================================

World Space (OpenGL right-handed):
  Y+  (Up)
  |   Z+ (Front, toward viewer)
  |  /
  | /
  +------ X+ (Right)

Face Layout (same as legacy):
       0  1  2
   0:     U
   1:  L  F  R
   2:     D
   3:     B

Face Transforms:
  Each face defined by (center, right_direction, up_direction)

  Face F (Front): center=(0,0,+50), right=(1,0,0), up=(0,1,0)
       +Y
        |
    +---+---+
    |   |   |
    +---+---+---> +X
    |   |   |
    +---+---+
       (Z = +50)

Cell Indexing (row=0 is bottom, col=0 is left):
  row 2: [TL] [T ] [TR]  (top row)
  row 1: [L ] [C ] [R ]  (middle row)
  row 0: [BL] [B ] [BR]  (bottom row)
         col0 col1 col2
"""
```

### Phase 4: Create Layer Separation (New Files)

Create new files mirroring legacy structure:

```
src/cube/presentation/gui/backends/pyglet2/
├── ModernGLCubeViewer.py  (keep as high-level interface)
├── _modern_gl_board.py    (NEW: manages all faces)
├── _modern_gl_face.py     (NEW: manages one face, cells)
└── _modern_gl_cell.py     (NEW: manages one cell geometry)
```

**_modern_gl_board.py:**
```python
class ModernGLBoard:
    """Manages all 6 cube faces for ModernGL rendering.

    Coordinate System:
        Face coordinates:
               0  1  2
           0:     U
           1:  L  F  R
           2:     D
           3:     B
    """
    def __init__(self, cube: Cube, vs: ApplicationAndViewState):
        self._faces: list[ModernGLFace] = []
        self._create_faces()

    def _create_faces(self):
        # Up face: center at (0, +50, 0), looks down
        self._create_face(FaceName.U, center=(0, HALF_CUBE_SIZE, 0), ...)

        # Front face: center at (0, 0, +50), looks toward viewer
        self._create_face(FaceName.F, center=(0, 0, HALF_CUBE_SIZE), ...)
        # ... etc with comments explaining each
```

**_modern_gl_face.py:**
```python
class ModernGLFace:
    """One face of the cube, containing size×size cells.

    Cell Layout:
      row 2: [TL] [T ] [TR]
      row 1: [L ] [C ] [R ]
      row 0: [BL] [B ] [BR]
             col0 col1 col2
    """
    def __init__(self, face_name: FaceName, center: ndarray,
                 right: ndarray, up: ndarray, size: int):
        self._cells: list[ModernGLCell] = []
        self._create_cells()
```

**_modern_gl_cell.py:**
```python
class ModernGLCell:
    """One cell (facelet) on a face.

    Geometry: 4 corners defining a quad
      left_top ---- right_top
          |            |
          |   center   |
          |            |
      left_bottom -- right_bottom
    """
    def __init__(self, row: int, col: int, part_slice: PartSlice):
        self.row = row
        self.col = col
        self._part_slice = part_slice
```

### Phase 5: Consolidate Duplicate Methods

The following methods are nearly identical and should be unified:

1. **Cell color getters:**
   - `_get_cell_color_3x3()` → `_get_cell_color()` with size param
   - `_get_cell_color_nxn()` → merge into unified method

2. **PartSlice getters:**
   - `_get_cell_part_slice_3x3()` → `_get_cell_part_slice()`
   - `_get_cell_part_slice_nxn()` → merge into unified method

3. **PartEdge getters:**
   - `_get_part_edge_at_cell()` duplicates logic from above

**Unified approach:**
```python
def _get_cell_part_slice(self, face: Face, row: int, col: int) -> PartSlice | None:
    """Get PartSlice at (row, col) on face.

    Works for any cube size. Corners at corners, edges on borders,
    center fills the middle.
    """
    size = face.cube.size
    last = size - 1

    # Corners (4 fixed positions)
    if (row, col) == (0, 0):
        return face.corner_bottom_left.slice
    if (row, col) == (0, last):
        return face.corner_bottom_right.slice
    # ... etc

    # Edges (borders excluding corners)
    if row == 0:  # Bottom edge
        return face.edge_bottom.get_slice_by_ltr_index(face, col - 1)
    # ... etc

    # Center (interior)
    return face.center.get_slice((row - 1, col - 1))
```

### Phase 6: Break Up Long Methods

**`_generate_face_geometry()`** (90+ lines) → split into:
- `_calc_cell_corners()` - compute corner positions
- `_add_cell_triangles()` - add triangles to vertex list
- `_add_cell_lines()` - add border lines

**`create_animation()`** (130+ lines) → split into:
- `_compute_rotation_matrices()` - axis transform math
- `_create_animation_callbacks()` - _update and _draw functions

---

## Implementation Order

1. **Phase 1-2** (Low risk): Add documentation and extract constants
   - No behavior change, just comments and named constants
   - Run all tests to verify no regressions

2. **Phase 3** (Low risk): Add coordinate system documentation
   - Module-level docstring with diagrams
   - Run tests

3. **Phase 5** (Medium risk): Consolidate duplicate methods
   - Replace 3x3/NxN variants with unified methods
   - Add comprehensive unit tests first
   - Run all tests

4. **Phase 6** (Medium risk): Break up long methods
   - Extract helper methods
   - Run tests after each extraction

5. **Phase 4** (Higher risk): Layer separation
   - This is the largest change
   - Create new files one at a time
   - Move functionality incrementally
   - Run tests after each move

---

## Success Criteria

After refactoring:
- [ ] No magic numbers without explanatory comments
- [ ] Coordinate systems documented with ASCII diagrams
- [ ] Layer separation similar to legacy (Board → Face → Cell)
- [ ] No duplicate 3x3/NxN methods
- [ ] No method longer than 50 lines
- [ ] All tests pass (mypy, pyright, pytest)
- [ ] Code is readable without needing to trace through math

---

## Files to Modify

1. `src/cube/presentation/gui/backends/pyglet2/ModernGLCubeViewer.py` - main refactoring
2. (NEW) `src/cube/presentation/gui/backends/pyglet2/_modern_gl_board.py`
3. (NEW) `src/cube/presentation/gui/backends/pyglet2/_modern_gl_face.py`
4. (NEW) `src/cube/presentation/gui/backends/pyglet2/_modern_gl_cell.py`
5. `__todo.md` - update status
