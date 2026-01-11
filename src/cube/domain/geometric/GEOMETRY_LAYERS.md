# Geometry Package - Two-Layer Architecture

This document describes the two-layer architecture for cube geometry calculations.

## Overview

The geometry package is organized into two distinct layers based on **size dependency**:

| Layer | Size Dependency | Access | Purpose |
|-------|-----------------|--------|---------|
| **Layout** | None (pure topology) | `cube.layout` | Face relationships, slice properties |
| **Geometric** | Requires n_slices | `cube.sized_layout` | Coordinate calculations, walking info |

## Layer 1: Layout (Size-Independent)

**Principle:** Questions about cube topology that have the same answer for ALL cube sizes.

### Protocols

- **`CubeLayout`** (`cube_layout.py`) - Face-color mapping and topological queries
- **`SliceLayout`** (`slice_layout.py`) - Slice-face relationship queries

### Implementations

- **`_CubeLayout`** (`_CubeLayout.py`) - Implements CubeLayout
- **`_SliceLayout`** (`slice_layout.py`) - Implements SliceLayout

### Example Questions (Layout Layer)

```python
# All these answers are the same for 3x3, 5x5, 7x7, etc.
cube.layout.is_adjacent(FaceName.F, FaceName.U)      # → True
cube.layout.opposite(FaceName.F)                      # → FaceName.B
cube.layout.does_slice_cut_rows_or_columns(M, F)     # → CLGColRow.ROW
```

---

## Layer 2: Geometric (Size-Dependent)

**Principle:** Calculations that require knowledge of cube size (n_slices).

### Protocol

- **`SizedCubeLayout`** (`sized_cube_layout.py`) - Size-dependent coordinate calculations

### Implementation

- **`_SizedCubeLayout`** (`_SizedCubeLayout.py`) - Implements SizedCubeLayout

### Example Questions (Geometric Layer)

```python
# These answers DEPEND on cube size
cube.sized_layout.create_walking_info(SliceName.M)      # Reference points vary by n_slices
cube.sized_layout.iterate_orthogonal_face_center_pieces(...)  # Row/col values vary
cube.sized_layout.translate_target_from_source(...)     # FUnitRotation needs n_slices
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Cube Instance                              │
│                                                                      │
│   ┌─────────────────────────┐     ┌─────────────────────────┐       │
│   │     cube.layout         │     │     cube.sized_layout      │       │
│   │    (CubeLayout)         │     │    (SizedCubeLayout)      │       │
│   └───────────┬─────────────┘     └───────────┬─────────────┘       │
│               │                               │                      │
└───────────────┼───────────────────────────────┼──────────────────────┘
                │                               │
    ┌───────────▼───────────────┐   ┌───────────▼───────────────┐
    │   LAYOUT LAYER            │   │   GEOMETRIC LAYER         │
    │   (Size-Independent)      │   │   (Size-Dependent)        │
    │                           │   │                           │
    │   • opposite()            │   │   • create_walking_info() │
    │   • is_adjacent()         │   │   • iterate_orthogonal_*  │
    │   • does_slice_cut_*      │   │   • translate_target_*    │
    │                           │   │                           │
    │                           │   │   Uses: n_slices, Face,   │
    │   Uses: FaceName,         │   │         Edge objects      │
    │         SliceName only    │   │                           │
    └───────────────────────────┘   └───────────────────────────┘
```

---

## File Organization

```
src/cube/domain/geometric/
├── GEOMETRY_LAYERS.md          # This document
├── UNIT_WALKING_INFO.md        # Unit walking info pattern (size-independent geometry)
├── CUBELAYOUT_INTERNAL_CUBE.md # Internal 3x3 cube for geometry queries
│
├── # LAYOUT LAYER (Size-Independent)
├── cube_layout.py              # CubeLayout protocol
├── slice_layout.py             # SliceLayout protocol + _SliceLayout implementation
├── _CubeLayout.py              # _CubeLayout implementation
│
├── # GEOMETRIC LAYER (Size-Dependent)
├── sized_cube_layout.py           # SizedCubeLayout protocol
├── _SizedCubeLayout.py           # _SizedCubeLayout implementation
│
├── # SHARED UTILITIES
├── cube_walking.py             # CubeWalkingInfo, CubeWalkingInfoUnit, FaceWalkingInfo
├── FRotation.py                # FUnitRotation for coordinate transforms
├── Face2FaceTranslator.py      # Translation utilities (uses both layers)
├── types.py                    # Point type alias
│
└── # REFERENCE
    ├── cube_boy.py             # BOY color scheme
    └── HARDCODED_ANALYSIS.md   # Analysis of hardcoded constants
```

## Key Pattern: Unit Walking Info

The `create_walking_info()` method uses a two-phase approach:

1. **Phase 1:** `_create_walking_info_unit()` computes walking info using a fake `n_slices` value.
   This captures the TOPOLOGY (faces, edges, coordinate inversion rules) without binding to a specific size.

2. **Phase 2:** `create_walking_info()` converts the unit info to actual cube size by:
   - Scaling reference points (0 → 0, fake_max → actual_max)
   - Binding compute functions to actual n_slices

**See:** `UNIT_WALKING_INFO.md` for detailed explanation.

---

## Design Principles

### 1. No Size at Layout Level

Layout layer methods **never** take `Cube` or `n_slices` parameters. They work purely
with `FaceName` and `SliceName` enums.

```python
# CORRECT - Layout layer
def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool

# Geometric layer uses Face/Edge objects and n_slices
def translate_target_from_source(self, source_face: Face, ...) -> FUnitRotation
```

### 2. Geometric Owns Coordinate Calculations

Any method that yields actual `(row, col)` coordinates belongs in the Geometric layer.

### 3. Protocol + Private Implementation

Each layer follows the pattern:
- **Protocol** (e.g., `CubeLayout`) - Public interface in separate file
- **Implementation** (e.g., `_CubeLayout`) - Private class with underscore prefix

### 4. Cube Owns Both

The `Cube` class provides access to both layers:
```python
cube.layout      # → CubeLayout (size-independent)
cube.sized_layout   # → SizedCubeLayout (size-dependent)
```

---

## Constants Location

**All topology constants are in `cube_layout.py`:**

Fundamental (hand-defined):
- `_OPPOSITE` - Canonical opposite pairs: F↔B, U↔D, L↔R
- `_SLICE_ROTATION_FACE` - Slice → rotation face: M→L, E→D, S→F
- `_AXIS_ROTATION_FACE` - Slice → axis face: M→R, E→U, S→F

Derived (computed from fundamental):
- `_ALL_OPPOSITE` - Bidirectional opposite mapping
- `_ADJACENT` - Adjacent faces (derived from `_OPPOSITE`)

Note: `_SLICE_FACES` was removed - now derived on demand in `get_slice_for_faces()`.

**BOY color scheme in `cube_boy.py`:**
- Face → Color mapping for standard Rubik's cube

### To Be Derived (Goal: Remove Hardcoding)

The following tables in `Face2FaceTranslator.py` should be derived, not hardcoded:
- `_TRANSFORMATION_TABLE` - **REMOVED** (was dead code, transforms computed dynamically)
- `_SLICE_INDEX_TABLE` - TODO (derive from edge geometry)
- `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` - TODO (derive from rotation faces)

---

## Migration Notes

When moving code between layers, ask:

> "Does this calculation give the same answer for a 3x3 and a 7x7 cube?"

- **Yes** → Layout layer
- **No** → Geometric layer
