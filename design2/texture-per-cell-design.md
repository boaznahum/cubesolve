# Texture Per-Cell Design (New Approach)

**Status**: ✅ IMPLEMENTED (with known bug - see bottom)

This document describes the new texture system where each cell has its own texture handle stored in `c_attributes`, allowing textures to "follow" stickers during rotation.

## Problem Statement

**Current behavior**: Textures are position-based. When a face rotates, pieces move but textures "reset" because UV coordinates are recalculated based on new cell positions.

**Desired behavior**: Textures should follow stickers during rotation, just like colors do.

## Solution Overview

1. **Slice face images** into NxN cell textures when loading
2. **Store texture handle** in `PartEdge.c_attributes["cell_texture"]`
3. **Draw per-cell** by reading texture from c_attributes (not by color grouping)
4. **Rotation handling**: Automatic via `copy_color()` which copies c_attributes

## Architecture

```
CURRENT FLOW:
┌──────────────────────────────────────────────────────────────────┐
│ load_texture_set()                                               │
│    └── 6 whole-face textures → _face_textures[FaceName]          │
│                                                                  │
│ draw()                                                           │
│    └── for color in _triangles_per_color:                        │
│            home_face = COLOR_TO_HOME_FACE[color]                 │
│            texture = _face_textures[home_face]                   │
│            draw_textured_triangles(vertices, texture)            │
│                                                                  │
│ Problem: UV = (col/size, row/size) → position-based, not piece   │
└──────────────────────────────────────────────────────────────────┘

NEW FLOW:
┌──────────────────────────────────────────────────────────────────┐
│ load_texture_set()                                               │
│    ├── For each face image:                                      │
│    │      Slice into NxN cell textures                           │
│    │      For each cell (row, col):                              │
│    │          handle = renderer.load_texture(cell_image)         │
│    │          partedge = get_partedge_at(face, row, col)         │
│    │          partedge.c_attributes["cell_texture"] = handle     │
│    └── Store handles for cleanup: _cell_textures[]               │
│                                                                  │
│ draw()                                                           │
│    └── for cell in all_cells:                                    │
│            texture = cell.part_slice.edge.c_attributes.get(...)  │
│            draw_textured_cell(cell, texture)                     │
│                                                                  │
│ Rotation: copy_color() automatically copies c_attributes!        │
└──────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Texture Key in c_attributes

```python
CELL_TEXTURE_KEY = "cell_texture"  # Constant for the attribute key

# Storage
partedge.c_attributes[CELL_TEXTURE_KEY] = texture_handle  # int

# Retrieval
texture_handle = partedge.c_attributes.get(CELL_TEXTURE_KEY)
```

### 2. Texture Slicing Strategy

**Option A: GPU-side slicing (Recommended)**
- Load whole face image once
- Create NxN sub-textures using `glTexSubImage2D` or pixel buffer copy
- Each cell gets its own GL texture ID
- Pro: Clean separation, each cell independent
- Con: More GPU memory (NxN textures per face instead of 1)

**Option B: Shared texture with stored UV**
- Keep 1 texture per face
- Store both handle AND UV rect in c_attributes
- Pro: Less GPU memory
- Con: More complex retrieval, need to pass UV to shader

**Recommendation**: Option A for simplicity. For a 3x3 cube, that's 9 textures per face = 54 total, which is negligible.

### 3. Cell-to-PartEdge Mapping

Need to map (face, row, col) to the correct PartEdge. This exists in `_modern_gl_face.py`:

```python
def _get_cell_part_slice(self, row, col) -> PartSlice | None:
    # Returns PartSlice for the cell at (row, col)
    # PartSlice has edge (PartEdge) for each face it touches
```

For texture storage, we need the PartEdge for the specific face:
```python
part_slice = face._get_cell_part_slice(row, col)
if part_slice:
    part_edge = part_slice.get_face_edge(face)  # PartEdge for THIS face
    part_edge.c_attributes[CELL_TEXTURE_KEY] = handle
```

### 4. Drawing Changes

**Current**: Group triangles by color, one draw call per color with face texture

**New**: Draw cells individually (or batch by texture handle)

```python
# Option A: Individual cells (simple, more draw calls)
for cell in face.cells:
    texture = cell.part_edge.c_attributes.get(CELL_TEXTURE_KEY)
    if texture:
        renderer.draw_textured_cell(cell.vertices, texture)
    else:
        renderer.draw_colored_cell(cell.vertices, cell.color)

# Option B: Batch by texture handle (optimized)
cells_by_texture: dict[int, list[Cell]] = {}
for cell in all_cells:
    handle = cell.part_edge.c_attributes.get(CELL_TEXTURE_KEY, None)
    cells_by_texture.setdefault(handle, []).append(cell)

for handle, cells in cells_by_texture.items():
    vertices = combine_cell_vertices(cells)
    if handle:
        renderer.draw_textured_triangles(vertices, handle)
    else:
        renderer.draw_lit_triangles(vertices)
```

### 5. UV Coordinates for Sliced Textures

When each cell has its own texture (the full cell image), UV coordinates are simple:
- All cells use UV = (0,0) to (1,1)
- The entire texture maps to the entire cell quad

```python
# In ModernGLCell.generate_textured_vertices():
# OLD: u0, v0 = col/size, row/size  (position in face texture)
# NEW: u0, v0 = 0, 0  (full cell texture)
#      u1, v1 = 1, 1
```

### 6. Texture Cleanup

Track all cell textures for proper cleanup:

```python
class ModernGLCubeViewer:
    _cell_textures: list[int] = []  # All cell texture handles

    def _clear_cell_textures(self):
        for handle in self._cell_textures:
            self._renderer.delete_texture(handle)
        self._cell_textures.clear()

        # Also clear from c_attributes
        for part_slice in self._cube.get_all_parts():
            for edge in part_slice.edges:
                edge.c_attributes.pop(CELL_TEXTURE_KEY, None)
```

### 7. When to Assign Textures

Textures should be assigned to c_attributes when:
1. **Loading a texture set** - slice images, assign to current sticker positions
2. **Cube reset** - if textures enabled, re-assign based on home positions
3. **Cube size change** - re-slice for new NxN, re-assign

**Critical insight**: When assigning, we assign based on the CURRENT color's home face, not the cell's position:

```python
def assign_cell_textures(self):
    """Assign cell textures based on current sticker colors."""
    for face in self._cube.faces:
        for row in range(size):
            for col in range(size):
                part_slice = self._get_cell_part_slice(face, row, col)
                if part_slice:
                    part_edge = part_slice.get_face_edge(face)
                    color = part_edge.color  # Current color of this sticker
                    home_face = COLOR_TO_HOME_FACE[color]

                    # Get the cell texture for this color's home position
                    # (where this sticker would be in a solved cube)
                    # This is the tricky part - see below
```

Wait - this is more complex. Let me think...

### 8. The "Home Position" Problem

When we slice a face image into NxN cells, we're creating:
- `F_cell_0_0`, `F_cell_0_1`, ..., `F_cell_2_2` (for 3x3)

When a GREEN sticker at position (1,1) on the FRONT face rotates to the RIGHT face:
- It should KEEP showing `F_cell_1_1` (its original cell texture)
- This is what c_attributes gives us automatically!

**Assignment strategy**:
1. For a SOLVED cube, sticker at (face, row, col) gets texture `{face}_cell_{row}_{col}`
2. Store this handle in the PartEdge's c_attributes
3. When face rotates, c_attributes moves with color
4. Sticker now at new position still has its original texture handle

**But what about scrambled cubes?**

If the user loads textures on a scrambled cube:
- Each sticker has a color (e.g., GREEN)
- That GREEN sticker's "home" is the FRONT face
- We need to figure out WHICH cell of the FRONT face this sticker originally came from

This requires tracking the sticker's "original position" - which we don't have!

### 9. Simplified Approach: Assign on Solved State Only

**Rule**: Textures can only be loaded/assigned when cube is in solved state (or becomes solved)

1. User loads texture set
2. If cube is solved: assign `face_cell_row_col` to each (face, row, col)
3. If cube is scrambled:
   - Option A: Reset cube first, then assign
   - Option B: Store textures but don't assign until solved
   - Option C: Use color-based assignment (all GREEN cells get same F texture - current behavior)

**Recommendation**: Option A is cleanest. When user loads textures:
1. If cube not solved, show message "Textures loaded. Reset cube (Escape) to apply."
2. On reset, assign textures
3. On scramble/solve, textures follow stickers via c_attributes

### 10. Alternative: Home Position Tracking

If we want to support assigning textures to scrambled cubes:

Add a `home_position` attribute to PartEdge that tracks where the sticker ORIGINALLY came from:

```python
# In PartEdge.__init__:
self.home_face: FaceName = face.name  # The face this sticker belongs to
self.home_row: int = row
self.home_col: int = col
```

This would NOT be copied by copy_color() (it's fixed, like `attributes`).

Then texture assignment becomes:
```python
home_face = part_edge.home_face
home_row = part_edge.home_row
home_col = part_edge.home_col
texture = cell_textures[home_face][home_row][home_col]
part_edge.c_attributes[CELL_TEXTURE_KEY] = texture
```

But this adds complexity to the model. **Recommend starting with solved-only approach**.

---

## Implementation Plan

### Phase 1: Texture Slicing

**File**: `ModernGLRenderer.py`

Add method to slice an image into NxN textures:

```python
def slice_texture(self, file_path: str, n: int) -> list[list[int]] | None:
    """
    Slice an image into NxN cell textures.

    Returns: 2D list of texture handles [row][col], or None on failure.
    """
    # Load image with PIL or pyglet
    # For each (row, col):
    #   Crop to cell region
    #   Create GL texture
    #   Store handle
    # Return 2D array of handles
```

### Phase 2: Storage in c_attributes

**File**: `ModernGLCubeViewer.py`

```python
CELL_TEXTURE_KEY = "cell_texture"

def _assign_cell_textures(self, cell_textures: dict[FaceName, list[list[int]]]):
    """Assign sliced textures to PartEdge c_attributes."""
    for face_name, face in self._cube.faces.items():
        textures = cell_textures.get(face_name)
        if not textures:
            continue
        for row in range(self._size):
            for col in range(self._size):
                part_slice = self._get_cell_part_slice(face, row, col)
                if part_slice:
                    part_edge = part_slice.get_face_edge(face)
                    part_edge.c_attributes[CELL_TEXTURE_KEY] = textures[row][col]
```

### Phase 3: Modified Drawing

**File**: `_modern_gl_board.py`

Change from color-grouping to per-cell texture lookup:

```python
def generate_textured_geometry_v2(self, animated_parts):
    """Generate geometry with per-cell textures from c_attributes."""
    # Group by texture handle instead of color
    verts_per_texture: dict[int | None, list[float]] = {}

    for face in self._faces.values():
        for cell in face.cells:
            texture = cell.part_edge.c_attributes.get(CELL_TEXTURE_KEY)
            verts_per_texture.setdefault(texture, [])
            cell.generate_full_uv_vertices(verts_per_texture[texture])

    return verts_per_texture
```

**File**: `_modern_gl_cell.py`

Add method for full-UV generation:

```python
def generate_full_uv_vertices(self, dest: list[float]) -> None:
    """Generate vertices with UV = (0,0) to (1,1) for per-cell textures."""
    # Same as generate_textured_vertices but with u0,v0=0,0 and u1,v1=1,1
```

### Phase 4: Load/Reset Handling

**File**: `ModernGLCubeViewer.py`

```python
def load_texture_set(self, directory: str) -> int:
    """Load and slice textures, assign to c_attributes."""
    self._clear_cell_textures()

    cell_textures: dict[FaceName, list[list[int]]] = {}

    for face_name in FaceName:
        path = self._find_face_texture_file(directory, face_name)
        if path:
            sliced = self._renderer.slice_texture(path, self._size)
            if sliced:
                cell_textures[face_name] = sliced
                # Track for cleanup
                for row in sliced:
                    self._cell_textures.extend(row)

    if cell_textures:
        self._assign_cell_textures(cell_textures)
        self._texture_mode = True
        self._dirty = True

    return len(cell_textures)
```

---

## File Changes Summary

| File | Changes |
|------|---------|
| `ModernGLRenderer.py` | Add `slice_texture()` method |
| `ModernGLCubeViewer.py` | Add `_assign_cell_textures()`, modify `load_texture_set()`, add `_cell_textures` tracking |
| `_modern_gl_board.py` | Add `generate_textured_geometry_v2()` or modify existing |
| `_modern_gl_cell.py` | Add `generate_full_uv_vertices()` |
| `_modern_gl_constants.py` | Add `CELL_TEXTURE_KEY` constant |

---

## Open Questions for User

1. **Scrambled cube handling**: Assign textures only when solved, or implement home position tracking?

2. **GPU memory**: OK to create NxN textures per face (e.g., 54 textures for 3x3)?

3. **Fallback**: When c_attributes has no texture, fall back to solid color?

4. **Animation**: During rotation animation, textures should visually rotate with the pieces - this should work automatically since geometry includes the animated parts.

---

## See Also

- `design2/texture-drawing-flow.md` - Original texture flow documentation
- `design2/partedge-attribute-system.md` - c_attributes mechanism
- `src/cube/domain/model/PartEdge.py` - c_attributes implementation

---

## Implementation Status (2025-12-07)

### Files Changed

| File | Changes |
|------|---------|
| `_modern_gl_constants.py` | Added `CELL_TEXTURE_KEY = "cell_texture"` constant |
| `ModernGLRenderer.py` | Added `slice_texture(file_path, n)` method using PIL |
| `_modern_gl_cell.py` | Added `part_edge` attribute, `cell_texture` property, `generate_full_uv_vertices()` |
| `_modern_gl_face.py` | Passes `part_edge` when creating cells in `update()` |
| `_modern_gl_board.py` | Added `generate_per_cell_textured_geometry()` method |
| `ModernGLCubeViewer.py` | New texture system with auto-reload detection |
| `PygletAppWindow.py` | Changed to use `load_texture_set_per_cell()` |

### Key Implementation Details

**ModernGLCubeViewer** new members:
- `_use_per_cell_textures: bool` - Whether per-cell textures are active
- `_cell_textures: list[int]` - All cell texture handles for cleanup
- `_texture_directory: str | None` - Stored for auto-reload after reset
- `load_texture_set_per_cell(directory)` - Main entry point
- `_assign_cell_textures(face_name, sliced_textures)` - Assigns handles to c_attributes
- `clear_cell_textures()` - Cleans up textures and clears c_attributes
- `_textures_need_reload()` - Detects if c_attributes lost (after cube reset)

**Auto-reload mechanism** in `_rebuild_geometry()`:
```python
if self._use_per_cell_textures and self._texture_directory:
    if self._textures_need_reload():
        self.load_texture_set_per_cell(self._texture_directory)
```

This ensures textures reload automatically when:
- Cube is reset (Escape key)
- Cube size changes
- Any event that creates new PartEdge objects (losing c_attributes)

### Decisions Made

1. **Texture assignment timing**: Solved state only - textures assigned on load/reset
2. **GPU memory**: Accepted NxN textures per face (54 for 3x3)
3. **Fallback**: Cells without texture use solid color rendering
4. **Commands kept simple**: Auto-reload logic in viewer, not in commands

---

## Known Bug

_Bug details to be added after user description_
