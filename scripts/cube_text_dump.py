#!/usr/bin/env python3
"""
Cube state text dump with coordinate system visualization.

Shows for each face:
- Row indexes on left side
- Column indexes on top
- LTR numbering on edges
- Colors at each position

This is the SOURCE OF TRUTH for verifying coordinate translations.

Usage:
    python scripts/cube_text_dump.py
"""

import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)


def dump_face(face, n: int) -> list[str]:
    """
    Generate text representation of a face.

    Format:
           c0  c1  c2   (columns)
          ─────────────
       r0 │ G │ G │ G │
       r1 │ G │ G │ G │
       r2 │ G │ G │ G │
          ─────────────
    """
    lines = []
    face_name = face.name.name
    center = face.center
    n_slices = n - 2  # Center grid size

    # Face header
    lines.append(f"═══ {face_name} ({face.color.name}) ═══")

    # Column headers
    col_header = "      " + "  ".join(f"c{c}" for c in range(n_slices))
    lines.append(col_header)

    # Top border
    lines.append("     ┌" + "───┬" * (n_slices - 1) + "───┐")

    # Rows with colors
    for row in range(n_slices):
        row_colors = []
        for col in range(n_slices):
            cs = center.get_center_slice((row, col))
            row_colors.append(f" {cs.color.name[0]} ")

        row_str = "│".join(row_colors)
        lines.append(f"  r{row} │{row_str}│")

        # Row separator (except last)
        if row < n_slices - 1:
            lines.append("     ├" + "───┼" * (n_slices - 1) + "───┤")

    # Bottom border
    lines.append("     └" + "───┴" * (n_slices - 1) + "───┘")

    return lines


def dump_face_edges(face) -> list[str]:
    """Dump edge info for a face."""
    lines = []
    face_name = face.name.name

    lines.append(f"  Edges of {face_name}:")

    for edge_name in ['top', 'right', 'bottom', 'left']:
        edge = getattr(face, f'edge_{edge_name}')
        is_horiz = edge_name in ('top', 'bottom')
        axis = "COL" if is_horiz else "ROW"
        is_f1 = (edge._f1 == face)
        same = "same" if edge.same_direction else "inv"

        lines.append(f"    {edge_name:6} → ltr selects {axis}, f1={is_f1}, {same}")

    return lines


def dump_cube(cube) -> str:
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


def main():
    """Generate cube state dumps."""
    from cube.domain.model.Cube import Cube
    from tests.test_utils import _test_sp

    cube = Cube(3, sp=_test_sp)

    print("INITIAL STATE (SOLVED)")
    print("=" * 40)
    print(dump_cube(cube))

    print("\n" + "█" * 40)
    print("AFTER M ROTATION")
    print("█" * 40)
    cube.m.rotate()
    print(dump_cube(cube))

    # Reset for S
    cube = Cube(3, sp=_test_sp)
    print("\n" + "█" * 40)
    print("AFTER S ROTATION")
    print("█" * 40)
    cube.s.rotate()
    print(dump_cube(cube))


if __name__ == "__main__":
    main()
