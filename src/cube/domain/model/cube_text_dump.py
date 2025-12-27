"""
Cube state text dump with coordinate system visualization.

Shows for each face:
- Row indexes on left side
- Column indexes on top
- c_attributes["n"] markers that move with color
- Edge information (f1, same_direction)

This is the SOURCE OF TRUTH for verifying coordinate translations.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Cube import Cube
    from .Face import Face


def dump_face(face: "Face", n: int) -> list[str]:
    """
    Generate text representation of a face.

    Shows c_attributes["n"] - the marker that moves with the color.
    Format: "color:n" e.g. "G:12" means Green with original position 12
    """
    lines = []
    face_name = face.name.name
    center = face.center
    n_slices = n - 2  # Center grid size

    # Face header
    lines.append(f"═══ {face_name} ({face.color.name}) ═══")

    # Column headers - wider to fit "G:00" format
    col_header = "       " + "   ".join(f"c{c}" for c in range(n_slices))
    lines.append(col_header)

    # Top border
    lines.append("      ┌" + "────┬" * (n_slices - 1) + "────┐")

    # Rows with color:n format
    for row in range(n_slices):
        row_cells = []
        for col in range(n_slices):
            cs = center.get_center_slice((row, col))
            color_char = cs.color.name[0]
            marker_n = cs.edge.c_attributes.get("n", "?")
            # Format: "G:02" - color and 2-digit marker
            row_cells.append(f"{color_char}:{marker_n:02d}" if isinstance(marker_n, int) else f"{color_char}:??")

        row_str = "│".join(row_cells)
        lines.append(f"  r{row}  │{row_str}│")

        # Row separator (except last)
        if row < n_slices - 1:
            lines.append("      ├" + "────┼" * (n_slices - 1) + "────┤")

    # Bottom border
    lines.append("      └" + "────┴" * (n_slices - 1) + "────┘")

    return lines


def dump_face_edges(face: "Face") -> list[str]:
    """Dump edge info for a face."""
    lines = []
    face_name = face.name.name

    lines.append(f"  Edges of {face_name}:")

    for edge_name in ['top', 'right', 'bottom', 'left']:
        edge = getattr(face, f'edge_{edge_name}')
        is_horiz = edge_name in ('top', 'bottom')
        axis = "COL" if is_horiz else "ROW"
        is_f1 = (edge._f1 == face)
        same = "same" if edge.right_top_left_same_direction else "inv"

        lines.append(f"    {edge_name:6} → ltr selects {axis}, f1={is_f1}, {same}")

    return lines


def dump_cube(cube: "Cube") -> str:
    """Complete cube state dump."""
    lines = []
    n = cube.size

    lines.append("╔════════════════════════════════════════╗")
    lines.append(f"║  CUBE STATE (size={n})                   ║")
    lines.append("╚════════════════════════════════════════╝")
    lines.append("")

    # LTR reminder
    lines.append("LTR System:")
    lines.append("  Horizontal edge (top/bottom): ltr 0→1→2 left to right")
    lines.append("  Vertical edge (left/right): ltr 0→1→2 bottom to top")
    lines.append("")

    faces = [
        cube.front, cube.up, cube.right,
        cube.back, cube.down, cube.left
    ]

    for face in faces:
        lines.extend(dump_face(face, n))
        lines.extend(dump_face_edges(face))
        lines.append("")

    return "\n".join(lines)
