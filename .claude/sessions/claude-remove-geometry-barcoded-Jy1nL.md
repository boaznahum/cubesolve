# Session Notes: Remove Hardcoded Geometry

**Branch:** `claude/remove-geometry-barcoded-Jy1nL`
**Issue:** #55 - Replace hard-coded lookup tables with mathematical derivation
**Status:** In Progress - Core derivation complete, needs user approval

---

## Overview

The task is to replace hardcoded starting face and starting edge in `create_walking_info()` with mathematical derivation from the rotation face geometry.

### Original Hardcoded Code (REMOVED)
```python
match slice_name:
    case SliceName.M:
        current_face = cube.front
        current_edge = current_face.edge_bottom
    case SliceName.E:
        current_face = cube.right
        current_edge = current_face.edge_left
    case SliceName.S:
        current_face = cube.up
        current_edge = current_face.edge_left
```

---

## Key Concepts

### Rotation Face
Each slice rotates like a specific face (its "rotation face"):
- M rotates like L: content flow F → U → B → D
- E rotates like D: content flow R → B → L → F
- S rotates like F: content flow U → R → D → L

### Algorithm Developed

1. **Get rotation face** from SliceLayout (M→L, E→D, S→F)

2. **Determine edge order** based on Front face's position relative to rotation face:
   - If rotation face IS Front, or Front is top/bottom edge → use clockwise
   - If Front is left/right edge → use counter-clockwise

3. **Get cycle faces** from rotation face's edges in that order

4. **Pick first two consecutive faces** from the cycle

5. **Find shared edge** between them = starting edge

6. **Traverse**: follow edge directly to next face, get opposite on new face

---

## Key File Modified

**`src/cube/domain/geometric/_CubeLayoutGeometry.py`** - `create_walking_info()` method (lines 378-552)

### Current Implementation (lines 419-455)

```python
# Determine edge order based on rotation face's geometric relationship to Front face
front_face = cube.front
if rotation_face == front_face:
    use_clockwise = True
elif (rotation_face.edge_top.get_other_face(rotation_face) == front_face or
      rotation_face.edge_bottom.get_other_face(rotation_face) == front_face):
    use_clockwise = True
else:
    use_clockwise = False

if use_clockwise:
    rotation_edges = [rotation_face.edge_top, rotation_face.edge_right,
                     rotation_face.edge_bottom, rotation_face.edge_left]
else:
    rotation_edges = [rotation_face.edge_right, rotation_face.edge_top,
                     rotation_face.edge_left, rotation_face.edge_bottom]
cycle_faces_ordered = [edge.get_other_face(rotation_face) for edge in rotation_edges]

# Pick first two consecutive faces
first_face = cycle_faces_ordered[0]
second_face = cycle_faces_ordered[1]

# Find shared edge between first two faces - this IS the starting edge
shared_edge = None
for edge in [first_face.edge_top, first_face.edge_right, first_face.edge_bottom, first_face.edge_left]:
    if edge.get_other_face(first_face) == second_face:
        shared_edge = edge
        break

current_face = first_face
current_edge = shared_edge
```

### Traversal Logic (lines 474-491)

```python
# Move to next face (except after the 4th)
if len(face_infos) < 4:
   # Follow current_edge to next face, then get opposite on new face
   next_face = current_edge.get_other_face(current_face)
   next_edge: Edge = current_edge.opposite(next_face)

   # Translate slice index through the edge
   next_slice_index = current_edge.get_edge_slice_index_from_face_ltr_index(
      current_face, current_index
   )
   current_index = current_edge.get_face_ltr_index_from_edge_slice_index(
      next_face, next_slice_index
   )
   current_edge = next_edge
   current_face = next_face
```

---

## Test Status

**All tests pass:**
- `tests/geometry/`: 346 passed
- `tests/solvers/`: 272 passed, 139 skipped
- `tests/algs/`: 48 passed, 9 skipped

Total: 618+ tests passing

---

## Debug Output (still in code)

The code contains DEBUG print statements showing:
- Rotation face
- Cycle faces
- First two faces
- Shared edge = Starting edge
- Each iteration's face, edge, reference_point

**TODO:** Remove DEBUG prints before final commit

---

## Commits Made

1. `5e662ee` - Derive starting face and edge from rotation face geometry
2. `3fc3e1b` - Fix starting edge derivation: use opposite of shared edge
3. `943f667` - Simplify traversal: follow edge directly, get opposite on new face
4. `eeabefd` - Remove hardcoded face names from edge order derivation

---

## Key Insight: Clockwise vs Counter-Clockwise

The edge order depends on the rotation face's axis:
- **Y-axis faces (U, D)** and **Z-axis faces (F, B)**: use clockwise edge order
- **X-axis faces (L, R)**: use counter-clockwise edge order

This is detected geometrically by checking where the Front face is relative to the rotation face:
- Front at top/bottom edge → clockwise (Y/Z axis)
- Front at left/right edge → counter-clockwise (X axis)

---

## Next Steps

1. **User approval** - User needs to review the code before final commit
2. **Remove DEBUG prints** - Clean up the debug output
3. **Update documentation** - Update any relevant docs about the geometry derivation
4. **Potential further work** - The `is_slot_inverted` and `is_index_inverted` logic could potentially also be derived rather than computed per-iteration

---

## Session History Summary

1. Started with hardcoded match statement for each slice
2. User guided step-by-step debugging approach
3. Discovered cycle faces come from rotation face's edges
4. Found that L/R faces need counter-clockwise, others need clockwise
5. Replaced face name check with geometric Front face position check
6. Changed traversal from "opposite then follow" to "follow then opposite"
7. Shared edge IS the starting edge directly (no opposite needed for start)
