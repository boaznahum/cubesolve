# Markers Package Design Documentation

## Overview

The markers package provides a centralized system for adding visual markers to cube stickers (PartEdges). Markers are used for:
- Solver animations (tracking pieces being moved)
- Coordinate system visualization (LTR origin, X/Y arrows)
- Debug/development aids (center indexes, sample markers)

## Architecture

### Core Components

```
IMarkerFactory (Protocol)     IMarkerManager (Protocol)
        ↑                              ↑
        │                              │
  MarkerFactory                 MarkerManager
        │                              │
        └──────→ MarkerConfig ←────────┘
                     │
                 MarkerShape (Enum)
```

### Classes

#### MarkerConfig (dataclass, frozen=True)
Immutable configuration for a marker's visual properties:
- `name`: Type identifier (e.g., "C0", "CHAR", "LTR_ORIGIN")
- `shape`: MarkerShape enum (RING, FILLED_CIRCLE, CROSS, ARROW, CHARACTER)
- `color`: RGB tuple (0.0-1.0) or None for complementary color
- `radius_factor`: Size relative to cell (0.0-1.0)
- `thickness`: For rings, ratio of ring width to radius
- `height_offset`: 3D height above face surface
- `use_complementary_color`: Derive color from sticker color
- `z_order`: Drawing order (higher draws on top)
- `direction`: For ARROW shape, angle in degrees
- `character`: For CHARACTER shape, the character to display

#### MarkerShape (Enum)
Available marker shapes:
- `RING`: Hollow ring (3D cylinder)
- `FILLED_CIRCLE`: Solid disk (3D cylinder)
- `CROSS`: X shape through corners
- `ARROW`: Directional arrow
- `CHARACTER`: Line-drawn text character (A-Z, 0-9, symbols)

#### MarkerFactory (implements IMarkerFactory)
Factory providing predefined markers:
- Animation: `c0()`, `c1()`, `c2()`
- Coordinates: `origin()`, `on_x()`, `on_y()`
- LTR System: `ltr_origin()`, `ltr_arrow_x()`, `ltr_arrow_y()`
- Custom: `create_ring()`, `create_filled_circle()`, `create_cross()`, `char()`

#### MarkerManager (implements IMarkerManager)
Central manager for marker operations:
- `add_marker(part_edge, marker, moveable, remove_same_name)`
- `add_fixed_marker(part_edge, marker)`
- `remove_marker(part_edge, marker, moveable)`
- `remove_markers_by_name(part_edge, name, moveable)`
- `get_markers(part_edge)`
- `has_markers(part_edge)`
- `clear_markers(part_edge, moveable)`

## Marker Storage

Markers are stored in PartEdge attribute dictionaries under the key `"markers"`:

| Dictionary | Use Case | Behavior |
|------------|----------|----------|
| `attributes` | Fixed structural markers (LTR coords) | Never changes |
| `c_attributes` | Moveable markers (`moveable=True`) | Follows piece color during rotation |
| `f_attributes` | Fixed position markers (`moveable=False`) | Stays at physical position |

## Marker Uniqueness

Markers use **full dataclass equality** (all fields must match):
- Adding a duplicate marker (exact same config) is silently skipped
- Two markers with same name but different properties are both added
- `remove_same_name=True` removes all markers with matching name before adding

This allows:
- Multiple CHARACTER markers with different characters on same cell
- Multiple markers of same type with different colors

## Configuration

`MarkersConfig` class (in `cube/utils/markers_config.py`) controls marker visibility:
- `GUI_DRAW_MARKERS`: Enable legacy debug markers
- `GUI_DRAW_SAMPLE_MARKERS`: Enable sample markers
- `GUI_DRAW_LTR_COORDS`: Enable LTR coordinate system markers
- `DRAW_CENTER_INDEXES`: Enable center index markers during rotation

Access via: `config.markers_config.GUI_DRAW_MARKERS`

## Rendering

Markers are rendered by the pyglet2 backend in `_modern_gl_cell.py`:
- `generate_marker_vertices()`: RING and FILLED_CIRCLE shapes
- `generate_cross_line_vertices()`: CROSS shapes
- `generate_arrow_marker_vertices()`: ARROW shapes (filled triangles)
- `generate_character_line_vertices()`: CHARACTER shapes (line segments)

Characters use a line-based font defined in `_CHAR_SEGMENTS` dictionary.

## Session Changes Summary

### What Was Done

1. **Created markers package** with proper protocol/implementation separation
2. **Added CHARACTER shape** for displaying text on stickers
3. **Implemented line-based font** for A-Z, 0-9, and common symbols
4. **Fixed marker uniqueness** - changed from name-based to full dataclass equality
5. **Added `remove_same_name` parameter** to `add_marker()` for replacing markers
6. **Consolidated marker config flags** into single `MarkersConfig` class
7. **Fixed CHARACTER rendering bug** - was incorrectly rendering as filled circles

### Known Issues / OOP Problems to Fix

#### 1. Marker Storage Coupling
Markers are stored directly in PartEdge attribute dictionaries. This creates tight coupling between:
- Domain model (PartEdge) and application logic (markers)
- The marker system "knows" about c_attributes/f_attributes implementation detail

**Proposed Fix**: Consider a separate MarkerStore that maps PartEdge identity to markers, rather than storing in PartEdge attributes.

#### 2. Renderer Knowledge of Shapes
Each renderer backend must implement rendering for all marker shapes. Adding a new shape requires:
- Adding enum value to MarkerShape
- Updating MarkerFactory
- Updating each renderer backend

**Proposed Fix**: Consider a visitor pattern or shape-specific renderer plugins.

#### 3. Configuration Location
`MarkersConfig` is in `cube/utils/` but logically belongs with markers. However, it's needed by `ConfigProtocol` in utils layer.

**Proposed Fix**: Consider if MarkersConfig should be part of the markers package with proper import structure.

## Usage Examples

```python
# Get manager from service provider
mm = cube.sp.marker_manager
mf = cube.sp.marker_factory

# Add animation markers
mm.add_marker(part_edge, mf.c1(), moveable=True)

# Add coordinate markers (fixed)
mm.add_fixed_marker(corner_edge, mf.ltr_origin())

# Add character marker, replacing any existing CHAR markers
mm.add_marker(center_edge, mf.char("5"), moveable=False, remove_same_name=True)

# Get all markers for rendering
markers = mm.get_markers(part_edge)
```
