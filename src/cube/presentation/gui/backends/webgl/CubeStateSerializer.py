"""
Cube state serializer for the webgl backend.

Extracts face colors and markers from the cube model and returns them
as a JSON-serializable dict. The client uses this to update sticker
colors and marker overlays without needing to understand the cube's
internal structure.

Grid layout (matches _FaceBoard):
    row 2: corner_top_left  | edge_top    | corner_top_right
    row 1: edge_left        | center      | edge_right
    row 0: corner_bottom_left | edge_bottom | corner_bottom_right

For NxN cubes, each cell (corner/edge/center) may contain multiple
stickers. The grid is expanded to a full NxN color array per face.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cube.application.markers import get_markers_from_part_edge
from cube.application.markers._complementary_colors import get_complementary_color
from cube.application.markers._marker_creators import (
    RingMarker, FilledCircleMarker, CrossMarker, ArrowMarker,
    CheckmarkMarker, BoldCrossMarker, CharacterMarker,
    color_float_to_255,
)
from cube.application.markers._outlined_circle_marker import OutlinedCircleMarker
from cube.application.markers._marker_creator_protocol import MarkerCreator
from cube.domain.model.Color import color2rgb_int

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.domain.model.PartEdge import PartEdge


# Type alias for the face color as float RGB (0.0-1.0)
_ColorF = tuple[float, float, float]

# Fallback magenta (matches _resolve_color in _marker_creators.py)
_FALLBACK_MAGENTA: _ColorF = (1.0, 0.0, 1.0)


def _resolve_marker_color(
    color: _ColorF | None,
    use_complementary: bool,
    complementary: _ColorF,
) -> _ColorF:
    """Resolve marker color for serialization.

    Same logic as _resolve_color in _marker_creators.py, but takes
    the pre-computed complementary color directly instead of a toolkit.
    """
    if color is not None:
        return color
    if use_complementary:
        return complementary
    return _FALLBACK_MAGENTA


def extract_cube_state(cube: "Cube") -> dict[str, Any]:
    """Extract the full cube state as a JSON-serializable dict.

    Returns:
        {
            "type": "cube_state",
            "size": N,
            "solved": bool,
            "faces": {
                "U": {"colors": [[r,g,b], ...], "markers": [null, [...], null, ...]},
                ...
            }
        }

    Each face value is a dict with:
      - "colors": flat list of N*N [r,g,b] values (0-255), row-major order
      - "markers": flat list of N*N entries, each null or a list of marker dicts

    The grid is NxN where N = cube.size. Row 0 is the bottom row,
    row N-1 is the top row. Within each row, column 0 is leftmost.
    """
    n = cube.size
    faces: dict[str, dict[str, list[Any]]] = {}

    for face in cube.faces:
        face_name = face.name.name  # "U", "D", "F", "B", "L", "R"
        face_data = _extract_face_data(face, n)
        faces[face_name] = face_data

    return {
        "type": "cube_state",
        "size": n,
        "solved": cube.solved,
        "faces": faces,
    }


def _extract_face_data(face: "Face", n: int) -> dict[str, list[Any]]:
    """Extract NxN grid of RGB colors and markers for one face.

    Returns a dict with:
      - "colors": flat list of [r, g, b] values in row-major order
      - "markers": flat list of marker data (null or list of marker dicts)
    """
    # Build NxN grids initialized to defaults
    color_grid: list[list[list[int]]] = [
        [[0, 0, 0] for _ in range(n)]
        for _ in range(n)
    ]
    edge_grid: list[list[PartEdge | None]] = [
        [None for _ in range(n)]
        for _ in range(n)
    ]

    if n >= 2:
        # Corner stickers (always at the 4 corners of the NxN grid)
        _set_cell(color_grid, edge_grid, face.corner_bottom_left, face, 0, 0, is_corner=True)
        _set_cell(color_grid, edge_grid, face.corner_bottom_right, face, 0, n - 1, is_corner=True)
        _set_cell(color_grid, edge_grid, face.corner_top_left, face, n - 1, 0, is_corner=True)
        _set_cell(color_grid, edge_grid, face.corner_top_right, face, n - 1, n - 1, is_corner=True)

    if n >= 3:
        # Edge stickers — fill the border between corners
        edge_count = n - 2

        # Bottom edge (row=0, cols 1..n-2)
        _set_edge_cells(color_grid, edge_grid, face.edge_bottom, face,
                        row=0, col_start=1, edge_count=edge_count, along_row=True)
        # Top edge (row=n-1, cols 1..n-2)
        _set_edge_cells(color_grid, edge_grid, face.edge_top, face,
                        row=n - 1, col_start=1, edge_count=edge_count, along_row=True)
        # Left edge (col=0, rows 1..n-2)
        _set_edge_cells(color_grid, edge_grid, face.edge_left, face,
                        row=1, col_start=0, edge_count=edge_count, along_row=False)
        # Right edge (col=n-1, rows 1..n-2)
        _set_edge_cells(color_grid, edge_grid, face.edge_right, face,
                        row=1, col_start=n - 1, edge_count=edge_count, along_row=False)

        # Center stickers
        if n < 4:
            # 3x3 — center is 1x1
            center = face.center
            center_slice = center.get_slice((0, 0))
            edge_on_face = center_slice.get_face_edge(face)
            rgb = color2rgb_int(edge_on_face.color)
            color_grid[1][1] = list(rgb)
            edge_grid[1][1] = edge_on_face
        else:
            # NxN — center is (n-2)x(n-2)
            center = face.center
            center_n = center.n_slices
            for cy in range(center_n):
                for cx in range(center_n):
                    center_slice = center.get_slice((cy, cx))
                    edge_on_face = center_slice.get_face_edge(face)
                    rgb = color2rgb_int(edge_on_face.color)
                    color_grid[1 + cy][1 + cx] = list(rgb)
                    edge_grid[1 + cy][1 + cx] = edge_on_face

    # Flatten to row-major lists
    flat_colors: list[list[int]] = [item for row in color_grid for item in row]
    flat_edges: list[PartEdge | None] = [item for row in edge_grid for item in row]

    # Build markers list from PartEdge references
    flat_markers: list[list[dict[str, Any]] | None] = []
    for i, part_edge in enumerate(flat_edges):
        if part_edge is None:
            flat_markers.append(None)
            continue
        markers = get_markers_from_part_edge(part_edge)
        if not markers:
            flat_markers.append(None)
            continue
        # Resolve face color for complementary color lookup
        face_color_float = (
            flat_colors[i][0] / 255.0,
            flat_colors[i][1] / 255.0,
            flat_colors[i][2] / 255.0,
        )
        serialized = [_serialize_marker(m, face_color_float) for m in markers]
        flat_markers.append(serialized)

    return {
        "colors": flat_colors,
        "markers": flat_markers,
    }


def _set_cell(
    color_grid: list[list[list[int]]],
    edge_grid: list[list[PartEdge | None]],
    corner: object,
    face: "Face",
    row: int,
    col: int,
    *,
    is_corner: bool,
) -> None:
    """Set a corner sticker's color and PartEdge in both grids."""
    from cube.domain.model import Corner
    assert isinstance(corner, Corner)
    corner_slice = corner.slice
    edge_on_face = corner_slice.get_face_edge(face)
    rgb = color2rgb_int(edge_on_face.color)
    color_grid[row][col] = list(rgb)
    edge_grid[row][col] = edge_on_face


def _set_edge_cells(
    color_grid: list[list[list[int]]],
    edge_grid: list[list[PartEdge | None]],
    edge: object,
    face: "Face",
    row: int,
    col_start: int,
    edge_count: int,
    along_row: bool,
) -> None:
    """Set edge sticker colors and PartEdges in both grids."""
    from cube.domain.model import Edge
    assert isinstance(edge, Edge)

    for i in range(edge_count):
        edge_wing = edge.get_slice_by_ltr_index(face, i)
        edge_on_face = edge_wing.get_face_edge(face)
        rgb = color2rgb_int(edge_on_face.color)

        if along_row:
            color_grid[row][col_start + i] = list(rgb)
            edge_grid[row][col_start + i] = edge_on_face
        else:
            color_grid[row + i][col_start] = list(rgb)
            edge_grid[row + i][col_start] = edge_on_face


def _serialize_marker(marker: MarkerCreator, face_color_float: _ColorF) -> dict[str, Any]:
    """Serialize a MarkerCreator to a JSON-friendly dict.

    Colors are resolved to RGB 0-255 ints. ``use_complementary_color``
    markers get their actual color computed here so the client never
    needs the complementary color table.
    """
    complementary = get_complementary_color(face_color_float)

    if isinstance(marker, RingMarker):
        c = _resolve_marker_color(marker.color, marker.use_complementary_color, complementary)
        return {
            "type": "ring",
            "color": list(color_float_to_255(c)),
            "inner_radius": marker.radius_factor * (1.0 - marker.thickness),
            "outer_radius": marker.radius_factor,
            "height": marker.height_offset,
            "z_order": marker.z_order,
        }

    if isinstance(marker, FilledCircleMarker):
        c = _resolve_marker_color(marker.color, marker.use_complementary_color, complementary)
        return {
            "type": "filled_circle",
            "color": list(color_float_to_255(c)),
            "radius": marker.radius_factor,
            "height": marker.height_offset,
            "z_order": marker.z_order,
        }

    if isinstance(marker, OutlinedCircleMarker):
        return {
            "type": "outlined_circle",
            "fill_color": list(color_float_to_255(marker.fill_color)),
            "outline_color": list(color_float_to_255(marker.outline_color)),
            "radius": marker.radius_factor,
            "outline_width": marker.outline_width,
            "height": marker.height_offset,
            "z_order": marker.z_order,
        }

    if isinstance(marker, CrossMarker):
        return {
            "type": "cross",
            "color": list(color_float_to_255(marker.color)),
            "z_order": marker.z_order,
        }

    if isinstance(marker, ArrowMarker):
        return {
            "type": "arrow",
            "color": list(color_float_to_255(marker.color)),
            "direction": marker.direction,
            "radius": marker.radius_factor,
            "thickness": marker.thickness,
            "z_order": marker.z_order,
        }

    if isinstance(marker, CheckmarkMarker):
        return {
            "type": "checkmark",
            "color": list(color_float_to_255(marker.color)),
            "radius": marker.radius_factor,
            "thickness": marker.thickness,
            "height": marker.height_offset,
            "z_order": marker.z_order,
        }

    if isinstance(marker, BoldCrossMarker):
        return {
            "type": "bold_cross",
            "color": list(color_float_to_255(marker.color)),
            "radius": marker.radius_factor,
            "thickness": marker.thickness,
            "height": marker.height_offset,
            "z_order": marker.z_order,
        }

    if isinstance(marker, CharacterMarker):
        return {
            "type": "character",
            "char": marker.character,
            "color": list(color_float_to_255(marker.color)),
            "radius": marker.radius_factor,
            "z_order": marker.z_order,
        }

    # Fallback for unknown marker types — serialize what we can
    return {
        "type": "unknown",
        "z_order": marker.get_z_order(),
    }
