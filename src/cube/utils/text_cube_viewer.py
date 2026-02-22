"""
Text-based cube viewer for NxN cubes.

Simple ASCII art renderer. Uses the same approach as ConsoleViewer but simpler.
Direction/orientation may need adjustment based on user testing.
"""

from dataclasses import dataclass

from rich.console import Console
from rich.text import Text

from cube.domain.model.Color import Color, TEXT_RICH_COLORS
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face

_console = Console()


@dataclass(frozen=True)
class FaceRenderConfig:
    """Configuration for mapping cube face coordinates to 2D paper/console.

    When rendering a cube face to 2D:
    - Paper has X (horizontal, left-to-right) and Y (vertical, top-to-bottom)
    - Cube face has its own coordinate system

    Attributes:
        reverse_x: Paper X goes opposite direction to cube X
        reverse_y: Paper Y goes opposite direction to cube Y
        swap_xy: Paper X maps to cube Y, paper Y maps to cube X (90° rotation)
    """
    reverse_x: bool = False
    reverse_y: bool = False
    swap_xy: bool = False


FACE_CONFIG: dict[str, FaceRenderConfig] = {
    "U": FaceRenderConfig(),
    "D": FaceRenderConfig(reverse_x=False),
    "F": FaceRenderConfig(),
    "L": FaceRenderConfig(),
    "R": FaceRenderConfig(),
    "B": FaceRenderConfig(reverse_x=False, reverse_y=False),
}


def _color_to_letter(color: Color) -> str:
    """Convert color to single letter."""
    return color.value[0].upper()


def _get_face_grid(face: Face, face_name: str) -> list[list[Color]]:
    """
    Get a 2D grid of colors for a face.

    Returns grid[paper_row][paper_col] for console output.
    Uses FaceRenderConfig to map paper coordinates to face LTR coordinates.
    """
    n = face.cube.size
    last = n - 1

    config = FACE_CONFIG.get(face_name, FaceRenderConfig())

    grid: list[list[Color]] = []

    for paper_row in range(n):
        row_colors: list[Color] = []
        for paper_col in range(n):
            # Map paper coords to face LTR coords
            if config.swap_xy:
                face_row, face_col = paper_col, paper_row
            else:
                face_row, face_col = paper_row, paper_col

            if config.reverse_x:
                face_col = last - face_col
            if config.reverse_y:
                face_row = last - face_row

            color = get_color_ltr(face, face_row, face_col)
            row_colors.append(color)
        grid.append(row_colors)

    return grid


def get_color_ltr(face: Face, row: int, col: int) -> Color:
    """Get color at (row, col) using left-to-right, top-to-bottom coordinates.

    Coordinate system (looking directly at the face):
    - row 0 = top row, row n-1 = bottom row
    - col 0 = left column, col n-1 = right column

    For a 3x3:
        col:  0   1   2
    row 0:  [TL] [T] [TR]
    row 1:  [L]  [C] [R]
    row 2:  [BL] [B] [BR]

    Args:
        face: The cube face
        row: Row index (0 = top)
        col: Column index (0 = left)

    Returns:
        Color at that position
    """
    n = face.cube.size
    last = n - 1

    # Corners
    if row == 0 and col == 0:
        return face.corner_top_left.get_face_edge(face).color
    if row == 0 and col == last:
        return face.corner_top_right.get_face_edge(face).color
    if row == last and col == 0:
        return face.corner_bottom_left.get_face_edge(face).color
    if row == last and col == last:
        return face.corner_bottom_right.get_face_edge(face).color

    # Top edge (row 0, cols 1 to n-2)
    if row == 0 and 0 < col < last:
        slice_idx = col - 1
        return face.edge_top.get_slice(slice_idx).get_face_edge(face).color

    # Bottom edge (row n-1, cols 1 to n-2)
    if row == last and 0 < col < last:
        slice_idx = col - 1
        return face.edge_bottom.get_slice(slice_idx).get_face_edge(face).color

    # Left edge (col 0, rows 1 to n-2)
    if col == 0 and 0 < row < last:
        slice_idx = row - 1
        return face.edge_left.get_slice(slice_idx).get_face_edge(face).color

    # Right edge (col n-1, rows 1 to n-2)
    if col == last and 0 < row < last:
        slice_idx = row - 1
        return face.edge_right.get_slice(slice_idx).get_face_edge(face).color

    # Center (rows 1 to n-2, cols 1 to n-2)
    center_row = row - 1
    center_col = col - 1
    return face.center.get_center_slice((center_row, center_col)).get_face_edge(face).color


def _render_face_row_rich(grid: list[list[Color]], row: int) -> Text:
    """Render a single row of a face using Rich Text."""
    text = Text()
    for color in grid[row]:
        letter = _color_to_letter(color)
        text.append(f"{letter} ", style=f"bold {TEXT_RICH_COLORS[color]}")
    return text


def _render_face_row_plain(grid: list[list[Color]], row: int) -> str:
    """Render a single row without colors."""
    return " ".join(_color_to_letter(c) for c in grid[row]) + " "


def _empty_space(n: int) -> str:
    """Return empty space the width of a face row."""
    return "  " * n


def cube_to_rich_text(cube: Cube) -> Text:
    """
    Convert a cube to Rich Text object.

    Layout (U/D aligned with F, labels above faces):
              U:
              xxx
          L:      R:  B:
          xxx xxx xxx xxx
              D:
              xxx
    """
    n = cube.size

    # Get color grids for each face
    up_grid = _get_face_grid(cube.up, "U")
    down_grid = _get_face_grid(cube.down, "D")
    front_grid = _get_face_grid(cube.front, "F")
    left_grid = _get_face_grid(cube.left, "L")
    right_grid = _get_face_grid(cube.right, "R")
    back_grid = _get_face_grid(cube.back, "B")

    result = Text()
    face_width = 2 * n  # each cell is "X "

    # U/D offset to align with F (after L face)
    ud_offset = face_width

    # Top section: U label and face
    result.append(" " * ud_offset + "U:\n")
    for row in range(n):
        result.append(" " * ud_offset)
        result.append_text(_render_face_row_rich(up_grid, row))
        result.append("\n")

    # Labels row for L, R, B (F is center, no label needed)
    result.append("L:" + " " * (face_width - 2))
    result.append(" " * face_width)  # space for F (no label)
    result.append("R:" + " " * (face_width - 2))
    result.append("B:\n")

    # Middle section: L F R B faces
    for row in range(n):
        result.append_text(_render_face_row_rich(left_grid, row))
        result.append_text(_render_face_row_rich(front_grid, row))
        result.append_text(_render_face_row_rich(right_grid, row))
        result.append_text(_render_face_row_rich(back_grid, row))
        result.append("\n")

    # Bottom section: D label and face
    result.append(" " * ud_offset + "D:\n")
    for row in range(n):
        result.append(" " * ud_offset)
        result.append_text(_render_face_row_rich(down_grid, row))
        result.append("\n")

    return result


def cube_to_text(cube: Cube) -> str:
    """Convert a cube to ASCII art text string (no colors)."""
    n = cube.size

    up_grid = _get_face_grid(cube.up, "U")
    down_grid = _get_face_grid(cube.down, "D")
    front_grid = _get_face_grid(cube.front, "F")
    left_grid = _get_face_grid(cube.left, "L")
    right_grid = _get_face_grid(cube.right, "R")
    back_grid = _get_face_grid(cube.back, "B")

    lines: list[str] = []
    face_width = 2 * n
    ud_offset = face_width

    # U label and face
    lines.append(" " * ud_offset + "U:")
    for row in range(n):
        lines.append(" " * ud_offset + _render_face_row_plain(up_grid, row))

    # Labels row for L, R, B
    lines.append("L:" + " " * (face_width - 2) + " " * face_width + "R:" + " " * (face_width - 2) + "B:")

    # L F R B faces
    for row in range(n):
        lines.append(
            _render_face_row_plain(left_grid, row) +
            _render_face_row_plain(front_grid, row) +
            _render_face_row_plain(right_grid, row) +
            _render_face_row_plain(back_grid, row)
        )

    # D label and face
    lines.append(" " * ud_offset + "D:")
    for row in range(n):
        lines.append(" " * ud_offset + _render_face_row_plain(down_grid, row))

    return "\n".join(lines)


def print_cube(cube: Cube, title: str | None = None) -> None:
    """Print a cube to the console with rich formatting."""
    if title:
        _console.print(f"[cyan]=== {title} ===[/cyan]")
    text = cube_to_rich_text(cube)
    _console.print(text)


def print_cube_with_info(cube: Cube, alg_str: str = "") -> None:
    """Print cube with status information."""
    status = "[green]SOLVED[/green]" if cube.solved else "[yellow]SCRAMBLED[/yellow]"
    _console.print(f"Size: {cube.size}x{cube.size}  Status: {status}")
    if alg_str:
        _console.print(f"Algorithm: [cyan]{alg_str}[/cyan]")
    text = cube_to_rich_text(cube)
    _console.print(text)
