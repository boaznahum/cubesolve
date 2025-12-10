# Texture Bug Investigation

**Bug Status**: PARTIALLY FIXED
**Last Updated**: 2025-12-10
**Branch**: `image-texture-bug`

## Current State

**F Face rotation: WORKING** ✅

After systematic testing, we found the correct UV mapping for texture rotation on the F face:
- direction=0 → UP (no rotation)
- direction=1 → RIGHT (after 1 CW rotation)
- direction=2 → DOWN (after 2 CW rotations)
- direction=3 → LEFT (after 3 CW rotations)

The fix is in `_modern_gl_cell.py` using UV_INDICES = [0, 3, 2, 1]

## Remaining Work

### Phase 1: Test all faces
- [x] F face rotation
- [ ] B face rotation
- [ ] R face rotation
- [ ] L face rotation
- [ ] U face rotation
- [ ] D face rotation

### Phase 2: Adjacent pieces
- [ ] Test edges/corners that move between faces during rotation
- [ ] Verify texture orientation is correct for pieces that cross face boundaries

### Phase 3: Large cube testing
- [ ] Test on 5x5 cube
- [ ] Verify all cell textures rotate correctly

## Bug Description

When rotating the Front face (F), the face texture becomes corrupted. Another rotation "fixes" the corruption.

**Key Observations:**
- Corruption happens after FIRST rotation
- Second rotation restores correct appearance
- Setting `direction = 0` in `_modern_gl_cell.py:178-180` does NOT fix the bug
- Therefore, this is NOT related to texture direction/UV rotation

```python
# In _modern_gl_cell.py lines 177-180:
direction = 0
#  if self.part_edge is not None:
#     direction = self.part_edge.texture_direction
```

## Architecture Understanding

### Texture System Flow (Per-Cell Textures)

1. **Loading**: `load_texture_set_per_cell(directory)`
   - Slices face images into NxN cell textures
   - Assigns texture handles to `PartEdge.c_attributes[CELL_TEXTURE_KEY]`
   - Also stores debug ID: `c_attributes[CELL_DEBUG_KEY] = "F(row,col)"`

2. **Storage**:
   - Texture handles live in `PartEdge.c_attributes["cell_texture"]`
   - During rotation, `copy_color()` copies entire `c_attributes` dict
   - Textures should "follow" stickers automatically

3. **Rendering**:
   - `_rebuild_geometry()` calls `_board.update()` which recreates cells
   - Each cell stores `part_edge` reference
   - `cell.cell_texture` property reads from `part_edge.c_attributes`

### Key Files

| File | Role |
|------|------|
| `ModernGLCubeViewer.py` | Main viewer, texture loading, animation |
| `_modern_gl_board.py` | Manages all 6 faces, generates geometry |
| `_modern_gl_face.py` | One face, creates cells |
| `_modern_gl_cell.py` | One cell, UV generation |
| `PartEdge.py` | Domain model, c_attributes storage |

### Animation Flow (CRITICAL)

```python
# In AnimationManager._op_and_play_animation():

animation = viewer.create_animation(alg, vs)  # Step 1: Create animation
animation_sink(animation)                      # Step 2: Set current animation

# Animation loop - visual rotation only
while not animation.done:
    event_loop.step()  # Triggers on_draw -> animation.draw()

animation.cleanup()     # Step 3: unhidden_all() - sets _dirty = True
operator(alg, False)    # Step 4: DOMAIN ROTATION HAPPENS HERE
window.update_gui_elements()  # Step 5: viewer.update() -> _dirty = True
```

**Key Insight**: Domain rotation happens AFTER visual animation ends.

### _rebuild_geometry() Sequence

1. Called when `_dirty = True`
2. Checks if textures need reload (for reset)
3. `_board.update()` - recreates ALL cells with fresh `part_edge` references
4. `generate_per_cell_textured_geometry()` - groups cells by texture handle

### Cell Creation in _modern_gl_face.py

```python
def update(self, cube_face: "Face") -> None:
    self._cells.clear()
    for row in range(size):
        for col in range(size):
            part_slice = self._get_cell_part_slice(cube_face, row, col)
            part_edge = part_slice.get_face_edge(cube_face) if part_slice else None
            # part_edge is stored in cell
```

The `part_edge` reference points to a FIXED PartEdge object. After rotation:
- The PartEdge object is the SAME
- But its `c_attributes` have changed (via `copy_color()`)

## Hypotheses

### Hypothesis 1: Timing Issue (INVESTIGATING)

The corruption appears because geometry is rebuilt at the wrong time relative to domain rotation.

**Timeline:**
1. Animation starts - cells created with PRE-rotation c_attributes
2. Animation plays - visual rotation
3. `unhidden_all()` - clears animation state, `_dirty = True`
4. Domain rotation - c_attributes move via `copy_color()`
5. `update_gui_elements()` - `_dirty = True` (already)
6. Next draw - `_rebuild_geometry()` with POST-rotation state

**Question**: Is there a draw happening between step 3 and step 4?

### Hypothesis 2: Cell Reference Staleness (LESS LIKELY)

Cells might keep stale `part_edge` references. But `_board.update()` recreates all cells, so this shouldn't happen.

### Hypothesis 3: Texture Handle Corruption (UNLIKELY)

GL texture handles might be getting corrupted. But second rotation wouldn't fix this.

### Hypothesis 4: Double Rotation (TO TEST)

Could the operator be called twice somehow?

## Debug Code Added

### In ModernGLCubeViewer._rebuild_geometry():

```python
if self._use_per_cell_textures:
    print(f"\n=== _rebuild_geometry called ===")
    print(f"  animated_parts: {self._animated_parts is not None}")
    self._debug_print_texture_state("BEFORE board.update()")

# After _board.update():
if self._use_per_cell_textures:
    self._debug_print_texture_state("AFTER board.update()")
    # Print what cells see from their part_edge references
```

### In ModernGLCubeViewer.unhidden_all():

```python
if self._use_per_cell_textures:
    print(f"\n=== unhidden_all() called ===")
    self._debug_print_texture_state("BEFORE unhidden_all clears state")
```

### Helper Method _debug_print_texture_state():

Prints Front face c_attributes in grid format showing debug_id values.

## Expected Debug Output Pattern

### Initial state (after texture load):
```
Front face c_attributes:
  ['F(2,0)', 'F(2,1)', 'F(2,2)']
  ['F(1,0)', 'F(1,1)', 'F(1,2)']
  ['F(0,0)', 'F(0,1)', 'F(0,2)']
```

### After F rotation CW:
```
Front face c_attributes (positions -> textures that moved there):
  ['F(0,2)', 'F(1,2)', 'F(2,2)']   # from: TL->TR, L->T, BL->TR
  ['F(0,1)', 'F(1,1)', 'F(2,1)']   # Center column rotates
  ['F(0,0)', 'F(1,0)', 'F(2,0)']   # from: BL->BL, B->L, BR->BL
```

Wait, this doesn't look right. Let me reconsider...

### F Rotation CW Mapping:
```
Before:          After (CW):
TL T  TR         BL L  TL
L  C  R    ->    B  C  T
BL B  BR         BR R  TR

Position (2,0) = TL <- gets content from BL (0,0)
Position (2,1) = T  <- gets content from L  (1,0)
Position (2,2) = TR <- gets content from TL (2,0)
Position (1,0) = L  <- gets content from B  (0,1)
Position (1,1) = C  <- stays C  (1,1)
Position (1,2) = R  <- gets content from T  (2,1)
Position (0,0) = BL <- gets content from BR (0,2)
Position (0,1) = B  <- gets content from R  (1,2)
Position (0,2) = BR <- gets content from TR (2,2)
```

## Tests to Run

1. Run GUI with debug output enabled
2. Press F (front rotation)
3. Check console for:
   - When `_rebuild_geometry()` is called
   - What c_attributes look like before/after
   - Whether cells see correct values

## Previous Attempts

### 1. Set direction = 0
**Result**: Bug persists. Ruled out UV rotation as cause.

### 2. Missing _animated_triangles_per_texture.clear() in unhidden_all()
**Found**: `unhidden_all()` was clearing `_animated_triangles_per_color` but NOT `_animated_triangles_per_texture`.
**Fixed**: Added `self._animated_triangles_per_texture.clear()` to `unhidden_all()`.
**Result**: TO TEST - may or may not be the root cause.

## Next Steps

1. Run GUI and capture debug output during F rotation
2. Compare expected vs actual c_attributes after rotation
3. Check if cells are getting correct part_edge references
4. Trace exact timing of _rebuild_geometry calls

## Related Files

- `design2/texture-per-cell-design.md` - Design document
- `design2/partedge-attribute-system.md` - c_attributes mechanism
- `src/cube/domain/model/PartEdge.py` - copy_color() implementation

## copy_color() Implementation Reference

```python
# In PartEdge.py:
def copy_color(self, source: "PartEdge"):
    self._color = source._color
    self._annotated_by_color = source._annotated_by_color
    self._texture_direction = source._texture_direction
    self.c_attributes.clear()
    self.c_attributes.update(source.c_attributes)
```

This copies the ENTIRE c_attributes dict, so texture handles should move correctly.

## Rotation Call Chain

```
Face.rotate(quarter_turns)
  -> corner_top_right.replace_colors(...)
     -> Part._replace_colors(source_part, *source_dest)
        -> target_slice.copy_colors(source_slice, *source_dest)
           -> target_edge.copy_color(source_edge)  # c_attributes copied here!
```

## Session Notes

### 2025-12-10 Session
- Analyzed full texture system architecture
- Traced animation flow and timing
- Added debug output to key methods
- Created this bug tracking document
- Key insight: Domain rotation happens AFTER animation visual completes
- Hypothesis: Timing issue between unhidden_all() and domain rotation
- **Fixed**: Missing `_animated_triangles_per_texture.clear()` in `unhidden_all()`

**Debug Output Added to ModernGLCubeViewer.py:**

The following debug prints will appear when running with per-cell textures:

```
=== _rebuild_geometry #N ===
  animated_parts: True/False
  BEFORE board.update():
    Front face c_attributes (format: debug_id):
      ['F(2,0)', 'F(2,1)', 'F(2,2)']  <- top row
      ['F(1,0)', 'F(1,1)', 'F(1,2)']  <- middle row
      ['F(0,0)', 'F(0,1)', 'F(0,2)']  <- bottom row
  AFTER board.update():
    [same format - should match BEFORE]
    Front face CELLS part_edge.c_attributes:
      [debug_ids that cells see - should match domain model]
    Generated geometry:
      static texture_handles: [1, 2, 3, ...]
      animated texture_handles: [4, 5, 6, ...]

=== unhidden_all() called ===
  BEFORE unhidden_all clears state:
    [c_attributes state - still PRE-rotation]
```

**How to interpret:**

1. **Initial load**: All debug_ids should match positions: F(row,col) at (row,col)
2. **During animation**: animated_parts = True, cells split between static/animated
3. **At unhidden_all()**: c_attributes still show PRE-rotation state
4. **After domain rotation**: _rebuild_geometry should show POST-rotation c_attributes
5. **Key check**: CELLS should see same values as domain model

**What to look for:**
- Mismatch between domain model c_attributes and cell.part_edge.c_attributes
- Unexpected texture_handles in geometry (None, duplicate handles)
- Debug_ids not rotating correctly after F move

**Expected F CW Rotation Mapping:**
```
Before:             After:
F(2,0) F(2,1) F(2,2)    F(0,2) F(1,2) F(2,2)
F(1,0) F(1,1) F(1,2) -> F(0,1) F(1,1) F(2,1)
F(0,0) F(0,1) F(0,2)    F(0,0) F(1,0) F(2,0)
```

**TODO for next session:**
- [x] Run GUI: `python -m cube.main_pyglet` ✅
- [x] Press F to rotate front face ✅
- [x] Check console output - does c_attributes rotate correctly? ✅ YES
- [x] Do cells see the rotated c_attributes? ✅ YES
- [x] Test if the missing .clear() fix resolved the bug ✅ Partial

## Solution Found (2025-12-10)

### Root Cause
The UV mapping for texture rotation was incorrect. The UV_BY_DIRECTION array had wrong mappings that produced incorrect visual rotations.

### The Fix
In `_modern_gl_cell.py`, we use 4 UV mapping options (A, B, C, D) that produce different visual rotations:
- Option A (index 0) → UP arrows
- Option B (index 1) → LEFT arrows
- Option C (index 2) → DOWN arrows
- Option D (index 3) → RIGHT arrows

The correct mapping for texture_direction is:
```python
UV_INDICES = [0, 3, 2, 1]  # direction 0→UP, 1→RIGHT, 2→DOWN, 3→LEFT
```

This produces the expected "painted on sticker" behavior where:
- direction=0: texture appears in original orientation (UP)
- direction=1: texture rotated 90° CW (RIGHT) - matches 1 CW face rotation
- direction=2: texture rotated 180° (DOWN) - matches 2 CW face rotations
- direction=3: texture rotated 270° CW (LEFT) - matches 3 CW face rotations

### Debug Texture Set Created
Created `src/cube/resources/faces/debug3x3/` with clear directional arrows and coordinates for easier debugging.

### Test Configuration
- CUBE_SIZE = 3 in config.py
- TEXTURE_SETS starts with "debug3x3"
