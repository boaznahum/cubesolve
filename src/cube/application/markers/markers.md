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
- `shape`: MarkerShape enum (RING, FILLED_CIRCLE, CROSS, ARROW, CHARACTER)
- `color`: RGB tuple (0.0-1.0) or None for complementary color
- `radius_factor`: Size relative to cell (0.0-1.0)
- `thickness`: For rings, ratio of ring width to radius
- `height_offset`: 3D height above face surface
- `use_complementary_color`: Derive color from sticker color
- `z_order`: Drawing order (higher draws on top)
- `direction`: For ARROW shape, angle in degrees
- `character`: For CHARACTER shape, the character to display

Note: Marker names are NOT part of the config. Names are provided by callers when
adding markers via MarkerManager.

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
- `add_marker(part_edge, name, marker, moveable)` - Add marker with given name
- `add_fixed_marker(part_edge, name, marker)` - Add structural marker
- `remove_marker(part_edge, name, moveable)` - Remove marker by name
- `remove_all(name, parts, moveable)` - Remove marker from multiple parts
- `get_markers(part_edge)` - Get unique markers, deduplicated and sorted by z_order
- `has_markers(part_edge)` - Check if has any markers
- `has_marker(part_edge, name)` - Check if has marker with given name
- `clear_markers(part_edge, moveable)` - Remove all markers

## Marker Storage

Markers are stored in PartEdge attribute dictionaries under the key `"markers"` as `dict[name, config]`:

| Dictionary | Use Case | Behavior |
|------------|----------|----------|
| `attributes` | Fixed structural markers (LTR coords) | Never changes |
| `c_attributes` | Moveable markers (`moveable=True`) | Follows piece color during rotation |
| `f_attributes` | Fixed position markers (`moveable=False`) | Stays at physical position |

## Marker Names and Uniqueness

Markers are stored by name (dictionary). The same config can be stored under different names:
- Adding a marker with an existing name replaces the old marker
- Different names can reference the same config instance (singleton pattern)
- Factory methods use caching to return same instance for same parameters

**Rendering Deduplication:**
- `get_markers()` deduplicates visually identical configs
- Keeps highest z_order for each unique config
- Returns sorted by z_order for proper layering

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

# Add animation markers with name
mm.add_marker(part_edge, "c1", mf.c1(), moveable=True)

# Add coordinate markers (fixed)
mm.add_fixed_marker(corner_edge, "ltr_origin", mf.ltr_origin())

# Add character marker (name "idx_0" replaces any existing "idx_0")
mm.add_marker(center_edge, "idx_0", mf.char("5"), moveable=False)

# Remove marker by name
mm.remove_marker(part_edge, "c1")

# Remove from multiple parts at once
mm.remove_all("c1", [edge1, edge2, edge3])

# Get all markers for rendering (deduplicated, sorted by z_order)
markers = mm.get_markers(part_edge)
```
