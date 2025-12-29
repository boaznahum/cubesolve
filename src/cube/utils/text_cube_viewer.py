"""
Text-based cube viewer for NxN cubes.

Simple ASCII art renderer. Uses the same approach as ConsoleViewer but simpler.
Direction/orientation may need adjustment based on user testing.
"""

from typing import Sequence

try:
    from rich.console import Console
    from rich.text import Text
    _HAS_RICH = True
    _console = Console()
except ImportError:
    _HAS_RICH = False

from cube.domain.model.Color import Color
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face


# Direction config for each face: (flip_rows, flip_cols, invert_lr_idx, invert_tb_idx)
# flip_rows=True: row 0 becomes last row
# flip_cols=True: col 0 becomes last col
# invert_lr_idx=True: left/right edge slice index is inverted
# invert_tb_idx=True: top/bottom edge slice index is inverted
FACE_CONFIG = {
    "U": (False, False, False, False),
    "D": (False, True, False, False),  # D: flip_cols
    "F": (False, False, False, False),
    "L": (False, False, False, False),
    "R": (False, False, False, False),
    "B": (True, False, True, True),  # B: flip_rows + invert both (try different combo)
}


# Rich color mappings
_RICH_COLORS: dict[Color, str] = {
    Color.WHITE: "white",
    Color.YELLOW: "yellow",
    Color.GREEN: "green",
    Color.BLUE: "blue",
    Color.RED: "red",
    Color.ORANGE: "bright_magenta",  # Rich has no orange, use magenta
}


def _color_to_letter(color: Color) -> str:
    """Convert color to single letter."""
    return color.value[0].upper()


def _get_face_grid(face: Face, face_name: str) -> list[list[Color]]:
    """
    Get a 2D grid of colors for a face.

    For an NxN cube, the grid is NxN:
    - Row 0: corners and top edge
    - Rows 1 to N-2: left edge, centers, right edge
    - Row N-1: corners and bottom edge

    Returns grid[row][col] where row 0 is TOP of face.
    Applies FACE_CONFIG flips for the given face_name.
    """
    n = face.cube.size
    n_slices = face.cube.n_slices  # size - 2

    # Get config
    config = FACE_CONFIG.get(face_name, (False, False, False, False))
    invert_lr_idx = config[2] if len(config) > 2 else False
    invert_tb_idx = config[3] if len(config) > 3 else False

    grid: list[list[Color]] = []

    for row in range(n):
        row_colors: list[Color] = []
        for col in range(n):
            color = _get_color_at(face, row, col, n, n_slices, invert_lr_idx, invert_tb_idx)
            row_colors.append(color)
        grid.append(row_colors)

    # Apply flips based on config
    flip_rows, flip_cols = config[0], config[1]

    if flip_rows:
        grid = list(reversed(grid))
    if flip_cols:
        grid = [list(reversed(row)) for row in grid]

    return grid


def _get_color_at(face: Face, row: int, col: int, n: int, n_slices: int,
                   invert_lr_idx: bool = False, invert_tb_idx: bool = False) -> Color:
    """Get color at a specific grid position on a face."""
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
        if invert_tb_idx:
            slice_idx = n_slices - 1 - slice_idx
        return face.edge_top.get_slice(slice_idx).get_face_edge(face).color

    # Bottom edge (row n-1, cols 1 to n-2)
    if row == last and 0 < col < last:
        slice_idx = col - 1
        if invert_tb_idx:
            slice_idx = n_slices - 1 - slice_idx
        return face.edge_bottom.get_slice(slice_idx).get_face_edge(face).color

    # Left edge (col 0, rows 1 to n-2)
    if col == 0 and 0 < row < last:
        slice_idx = row - 1
        if invert_lr_idx:
            slice_idx = n_slices - 1 - slice_idx
        return face.edge_left.get_slice(slice_idx).get_face_edge(face).color

    # Right edge (col n-1, rows 1 to n-2)
    if col == last and 0 < row < last:
        slice_idx = row - 1
        if invert_lr_idx:
            slice_idx = n_slices - 1 - slice_idx
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
        text.append(f"{letter} ", style=f"bold {_RICH_COLORS[color]}")
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
    if _HAS_RICH:
        if title:
            _console.print(f"[cyan]=== {title} ===[/cyan]")
        text = cube_to_rich_text(cube)
        _console.print(text)
    else:
        if title:
            print(f"=== {title} ===")
        print(cube_to_text(cube))


def print_cube_with_info(cube: Cube, alg_str: str = "") -> None:
    """Print cube with status information."""
    if _HAS_RICH:
        status = "[green]SOLVED[/green]" if cube.solved else "[yellow]SCRAMBLED[/yellow]"
        _console.print(f"Size: {cube.size}x{cube.size}  Status: {status}")
        if alg_str:
            _console.print(f"Algorithm: [cyan]{alg_str}[/cyan]")
        text = cube_to_rich_text(cube)
        _console.print(text)
    else:
        status = "SOLVED" if cube.solved else "SCRAMBLED"
        print(f"Size: {cube.size}x{cube.size}  Status: {status}")
        if alg_str:
            print(f"Algorithm: {alg_str}")
        print_cube(cube)
