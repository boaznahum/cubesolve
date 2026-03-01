"""
Cube state serializer for the webgl backend.

Extracts face colors from the cube model and returns them as a JSON-
serializable dict. The client uses this to update sticker colors without
needing to understand the cube's internal structure.

Grid layout (matches _FaceBoard):
    row 2: corner_top_left  | edge_top    | corner_top_right
    row 1: edge_left        | center      | edge_right
    row 0: corner_bottom_left | edge_bottom | corner_bottom_right

For NxN cubes, each cell (corner/edge/center) may contain multiple
stickers. The grid is expanded to a full NxN color array per face.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.model.Color import color2rgb_int

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


def extract_cube_state(cube: "Cube") -> dict:
    """Extract the full cube state as a JSON-serializable dict.

    Returns:
        {
            "type": "cube_state",
            "size": N,
            "faces": {
                "U": [[r,g,b], ...],  # N*N colors, row-major (top-left first)
                "D": [...], "F": [...], "B": [...], "L": [...], "R": [...]
            }
        }

    The grid is NxN where N = cube.size. Row 0 is the bottom row,
    row N-1 is the top row. Within each row, column 0 is leftmost.
    """
    n = cube.size
    faces: dict[str, list[list[int]]] = {}

    for face in cube.faces:
        face_name = face.name.name  # "U", "D", "F", "B", "L", "R"
        grid = _extract_face_colors(face, n)
        faces[face_name] = grid

    return {
        "type": "cube_state",
        "size": n,
        "faces": faces,
    }


def _extract_face_colors(face: "Face", n: int) -> list[list[int]]:
    """Extract NxN grid of RGB colors for one face.

    Returns a flat list of [r, g, b] values in row-major order,
    from bottom-left (row=0, col=0) to top-right (row=N-1, col=N-1).

    The mapping from grid (row, col) to part/slice matches the _FaceBoard layout.
    """
    # Build NxN grid initialized to black
    grid: list[list[list[int]]] = [
        [[0, 0, 0] for _ in range(n)]
        for _ in range(n)
    ]

    if n < 2:
        return [item for row in grid for item in row]

    # Corner stickers (always at the 4 corners of the NxN grid)
    _set_corner_color(grid, face.corner_bottom_left, face, 0, 0)
    _set_corner_color(grid, face.corner_bottom_right, face, 0, n - 1)
    _set_corner_color(grid, face.corner_top_left, face, n - 1, 0)
    _set_corner_color(grid, face.corner_top_right, face, n - 1, n - 1)

    if n < 3:
        # 2x2 cube — only corners, no edges or centers
        return [item for row in grid for item in row]

    # Edge stickers — fill the border between corners
    edge_count = n - 2  # number of edge stickers per edge

    # Bottom edge (row=0, cols 1..n-2)
    _set_edge_colors(grid, face.edge_bottom, face, row=0, col_start=1, edge_count=edge_count,
                     along_row=True)
    # Top edge (row=n-1, cols 1..n-2)
    _set_edge_colors(grid, face.edge_top, face, row=n - 1, col_start=1, edge_count=edge_count,
                     along_row=True)
    # Left edge (col=0, rows 1..n-2)
    _set_edge_colors(grid, face.edge_left, face, row=1, col_start=0, edge_count=edge_count,
                     along_row=False)
    # Right edge (col=n-1, rows 1..n-2)
    _set_edge_colors(grid, face.edge_right, face, row=1, col_start=n - 1, edge_count=edge_count,
                     along_row=False)

    if n < 4:
        # 3x3 — center is 1x1
        center = face.center
        center_slice = center.get_slice((0, 0))
        edge_on_face = center_slice.get_face_edge(face)
        rgb = color2rgb_int(edge_on_face.color)
        grid[1][1] = list(rgb)
    else:
        # NxN — center is (n-2)x(n-2)
        center = face.center
        center_n = center.n_slices
        for cy in range(center_n):
            for cx in range(center_n):
                center_slice = center.get_slice((cy, cx))
                edge_on_face = center_slice.get_face_edge(face)
                rgb = color2rgb_int(edge_on_face.color)
                grid[1 + cy][1 + cx] = list(rgb)

    # Flatten to list of [r, g, b] in row-major order
    return [item for row in grid for item in row]


def _set_corner_color(
    grid: list[list[list[int]]],
    corner: object,  # Corner part
    face: "Face",
    row: int,
    col: int,
) -> None:
    """Set a corner sticker's color in the grid."""
    from cube.domain.model import Corner
    assert isinstance(corner, Corner)
    corner_slice = corner.slice
    edge_on_face = corner_slice.get_face_edge(face)
    rgb = color2rgb_int(edge_on_face.color)
    grid[row][col] = list(rgb)


def _set_edge_colors(
    grid: list[list[list[int]]],
    edge: object,  # Edge part
    face: "Face",
    row: int,
    col_start: int,
    edge_count: int,
    along_row: bool,
) -> None:
    """Set edge sticker colors in the grid.

    For edges along a row, col varies from col_start to col_start+edge_count-1.
    For edges along a column, row varies from row to row+edge_count-1.
    """
    from cube.domain.model import Edge
    assert isinstance(edge, Edge)

    for i in range(edge_count):
        edge_wing = edge.get_slice_by_ltr_index(face, i)
        edge_on_face = edge_wing.get_face_edge(face)
        rgb = color2rgb_int(edge_on_face.color)

        if along_row:
            grid[row][col_start + i] = list(rgb)
        else:
            grid[row + i][col_start] = list(rgb)
