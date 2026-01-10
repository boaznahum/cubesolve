# Geometry Package - Two-Layer Architecture

This document describes the two-layer architecture for cube geometry calculations.

## Overview

The geometry package is organized into two distinct layers based on **size dependency**:

| Layer | Size Dependency | Access | Purpose |
|-------|-----------------|--------|---------|
| **Layout** | None (pure topology) | `cube.layout` | Face relationships, slice properties |
| **Geometric** | Requires n_slices | `cube.geometric` | Coordinate calculations, walking info |

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
cube.layout.derive_transform_type(F, U)              # → TransformType.IDENTITY
```

### Key Insight

`derive_transform_type()` is in the Layout layer because the **transformation type**
(IDENTITY, ROT_90_CW, etc.) is the same for all cube sizes. Only the actual coordinate
values differ (e.g., `inv(x)` = `n_slices - 1 - x` depends on size).

---

## Layer 2: Geometric (Size-Dependent)

**Principle:** Calculations that require knowledge of cube size (n_slices).

### Protocol

- **`CubeGeometric`** (`cube_geometric.py`) - Size-dependent coordinate calculations

### Implementation

- **`_CubeGeometric`** (`_CubeGeometric.py`) - Implements CubeGeometric

### Example Questions (Geometric Layer)

```python
# These answers DEPEND on cube size
cube.geometric.create_walking_info(SliceName.M)      # Reference points vary by n_slices
cube.geometric.iterate_orthogonal_face_center_pieces(...)  # Row/col values vary
cube.geometric.translate_target_from_source(...)     # FUnitRotation needs n_slices
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Cube Instance                              │
│                                                                      │
│   ┌─────────────────────────┐     ┌─────────────────────────┐       │
│   │     cube.layout         │     │     cube.geometric      │       │
│   │    (CubeLayout)         │     │    (CubeGeometric)      │       │
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
    │   • derive_transform_type │   │   • translate_target_*    │
    │   • does_slice_cut_*      │   │                           │
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
│
├── # LAYOUT LAYER (Size-Independent)
├── cube_layout.py              # CubeLayout protocol
├── slice_layout.py             # SliceLayout protocol + _SliceLayout implementation
├── _CubeLayout.py              # _CubeLayout implementation
│
├── # GEOMETRIC LAYER (Size-Dependent)
├── cube_geometric.py           # CubeGeometric protocol
├── _CubeGeometric.py           # _CubeGeometric implementation
│
├── # SHARED UTILITIES
├── cube_walking.py             # CubeWalkingInfo, FaceWalkingInfo
├── FRotation.py                # FUnitRotation for coordinate transforms
├── Face2FaceTranslator.py      # Translation utilities (uses both layers)
├── types.py                    # Point type alias
│
└── # REFERENCE
    ├── cube_boy.py             # BOY color scheme
    └── HARDCODED_ANALYSIS.md   # Analysis of hardcoded constants
```

---

## Design Principles

### 1. No Size at Layout Level

Layout layer methods **never** take `Cube` or `n_slices` parameters. They work purely
with `FaceName` and `SliceName` enums.

```python
# CORRECT - Layout layer
def derive_transform_type(self, source: FaceName, target: FaceName) -> TransformType

# WRONG - This would be Geometric layer
def derive_transform_type(self, cube: Cube, source: FaceName, target: FaceName)
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
cube.geometric   # → CubeGeometric (size-dependent)
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
- `_SLICE_FACES` - Faces each slice affects (derived from `_SLICE_ROTATION_FACE` + `_ADJACENT`)

**BOY color scheme in `cube_boy.py`:**
- Face → Color mapping for standard Rubik's cube

### To Be Derived (Goal: Remove Hardcoding)

The following tables in `Face2FaceTranslator.py` should be derived, not hardcoded:
- `_TRANSFORMATION_TABLE` - **DONE** (derived via `derive_transform_type`)
- `_SLICE_INDEX_TABLE` - TODO (derive from edge geometry)
- `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` - TODO (derive from rotation faces)

---

## Migration Notes

When moving code between layers, ask:

> "Does this calculation give the same answer for a 3x3 and a 7x7 cube?"

- **Yes** → Layout layer
- **No** → Geometric layer
