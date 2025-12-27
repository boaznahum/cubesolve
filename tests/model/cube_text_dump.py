"""
Cube state text dump with full coordinate system visualization.

Shows for each face:
- (row, col) indexes in the grid
- LTR numbering (0→1→2) on each edge
- R/T direction arrows
- Colors at each position

This is the SOURCE OF TRUTH for verifying coordinate translations.

Usage:
    PYTHONPATH=src python tests/model/cube_text_dump.py
"""

from dataclasses import dataclass


def dump_face_detailed(face, n: int) -> list[str]:
    """
    Generate detailed text representation of a face.

    Shows:
    - Face name and color
    - Grid with (row, col) and color at each position
    - LTR numbering on all 4 edges
    - R (right) and T (top) direction indicators
    """
    lines = []
    face_name = face.name.name  # e.g., "F", "U", etc.
    face_color = face.color.name[0]  # First letter of color

    # Get center colors for the grid
    center = face.center
    n_slices = n - 2  # Center grid size (for n=3, this is 1)

    # Build color grid
    color_grid = []
    for row in range(n_slices):
        row_colors = []
        for col in range(n_slices):
            cs = center.get_center_slice((row, col))
            row_colors.append(cs.color.name[0])
        color_grid.append(row_colors)

    # Top edge ltr
    top_ltr = "  ltr: " + " → ".join(str(i) for i in range(n_slices))

    # Header
    lines.append(f"╔{'═' * 50}╗")
    lines.append(f"║  FACE {face_name} ({face.color.name}){' ' * (50 - 12 - len(face.color.name))}║")
    lines.append(f"╠{'═' * 50}╣")

    # Top edge with ltr
    lines.append(f"║{' ' * 15}TOP edge{' ' * 27}║")
    lines.append(f"║{' ' * 12}{top_ltr}{' ' * (38 - len(top_ltr))}║")
    lines.append(f"║{' ' * 10}┌{'─' * 28}┐{' ' * 10}║")

    # Grid rows with LEFT and RIGHT ltr
    for row in range(n_slices):
        left_ltr = n_slices - 1 - row  # Vertical: bottom=0, top=n-1
        right_ltr = n_slices - 1 - row

        # Build row content: (row,col)=COLOR
        row_content = ""
        for col in range(n_slices):
            color = color_grid[row][col]
            row_content += f"({row},{col})={color} "
        row_content = row_content.strip()

        # Pad to fixed width
        content_width = 26
        row_content = row_content.center(content_width)

        left_label = f"ltr={left_ltr}"
        right_label = f"ltr={right_ltr}"

        lines.append(f"║  {left_label} │{row_content}│ {right_label}  ║")

    # Bottom edge
    lines.append(f"║{' ' * 10}└{'─' * 28}┘{' ' * 10}║")
    bottom_ltr = "  ltr: " + " → ".join(str(i) for i in range(n_slices))
    lines.append(f"║{' ' * 12}{bottom_ltr}{' ' * (38 - len(bottom_ltr))}║")
    lines.append(f"║{' ' * 15}BOTTOM edge{' ' * 24}║")

    # Direction indicators
    lines.append(f"╠{'═' * 50}╣")
    lines.append(f"║  R direction: →  (columns increase left to right)  ║")
    lines.append(f"║  T direction: ↑  (rows increase bottom to top)     ║")
    lines.append(f"║  Horizontal edge (top/bottom): ltr selects COLUMN  ║")
    lines.append(f"║  Vertical edge (left/right): ltr selects ROW       ║")
    lines.append(f"╚{'═' * 50}╝")

    return lines


def dump_face_simple(face, n: int) -> list[str]:
    """
    Simple grid view showing coordinates and colors.
    """
    lines = []
    face_name = face.name.name

    center = face.center
    n_slices = n - 2

    lines.append(f"=== {face_name} ({face.color.name}) ===")
    lines.append(f"    {'  '.join(f'c{c}' for c in range(n_slices))}")
    lines.append(f"    {'  '.join('──' for _ in range(n_slices))}")

    for row in range(n_slices):
        row_data = []
        for col in range(n_slices):
            cs = center.get_center_slice((row, col))
            row_data.append(f" {cs.color.name[0]} ")
        lines.append(f"r{row} │{'│'.join(row_data)}│")

    lines.append("")
    return lines


def dump_edges_info(face) -> list[str]:
    """
    Dump edge information for a face.
    """
    lines = []
    face_name = face.name.name

    lines.append(f"--- {face_name} Edges ---")

    edge_names = ['top', 'right', 'bottom', 'left']
    for edge_name in edge_names:
        edge = getattr(face, f'edge_{edge_name}')
        edge_color = edge.get_face_edge(face).color.name

        # Determine edge type
        is_horizontal = edge_name in ('top', 'bottom')
        edge_type = "horizontal" if is_horizontal else "vertical"
        axis = "COLUMN" if is_horizontal else "ROW"

        # Get same_direction info
        is_f1 = (edge._f1 == face)
        same_dir = edge.same_direction

        lines.append(f"  {edge_name:6}: {edge_color:6} | {edge_type:10} | ltr→{axis:6} | f1={is_f1} same_dir={same_dir}")

    lines.append("")
    return lines


def dump_cube_state(cube) -> str:
    """
    Complete cube state dump with all coordinate information.
    """
    lines = []
    n = cube.size

    lines.append("╔" + "═" * 60 + "╗")
    lines.append("║" + f"  CUBE STATE DUMP (size={n})".center(60) + "║")
    lines.append("║" + f"  Source of truth for coordinate verification".center(60) + "║")
    lines.append("╚" + "═" * 60 + "╝")
    lines.append("")

    faces = [
        cube.front, cube.up, cube.right,
        cube.back, cube.down, cube.left
    ]

    # Simple grid view for each face
    lines.append("=" * 60)
    lines.append("FACE GRIDS (row, col → color)")
    lines.append("=" * 60)

    for face in faces:
        lines.extend(dump_face_simple(face, n))

    # Edge information
    lines.append("=" * 60)
    lines.append("EDGE INFORMATION")
    lines.append("=" * 60)

    for face in faces:
        lines.extend(dump_edges_info(face))

    # LTR coordinate system reminder
    lines.append("=" * 60)
    lines.append("LTR COORDINATE SYSTEM")
    lines.append("=" * 60)
    lines.append("")
    lines.append("  Each face's LTR system:")
    lines.append("  - Horizontal edges (top/bottom): ltr 0→1→2 left to right")
    lines.append("  - Vertical edges (left/right): ltr 0→1→2 bottom to top")
    lines.append("")
    lines.append("  The Axis Rule:")
    lines.append("  - Horizontal edge → ltr selects COLUMN")
    lines.append("  - Vertical edge → ltr selects ROW")
    lines.append("")

    return "\n".join(lines)


def dump_after_rotation(cube, rotation_name: str, rotation_func) -> str:
    """
    Dump cube state before and after a rotation.
    """
    lines = []

    lines.append("\n" + "█" * 60)
    lines.append(f"  ROTATION: {rotation_name}")
    lines.append("█" * 60 + "\n")

    lines.append("BEFORE:")
    lines.append("-" * 40)
    lines.append(dump_cube_state(cube))

    # Apply rotation
    rotation_func()

    lines.append("\nAFTER:")
    lines.append("-" * 40)
    lines.append(dump_cube_state(cube))

    return "\n".join(lines)


def main():
    """Generate cube state dumps for verification."""
    # Import here to avoid module-level dependency issues
    import sys
    import os

    # Add both src and project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.join(project_root, 'src'))
    sys.path.insert(0, project_root)

    from cube.domain.model.Cube import Cube
    from tests.test_utils import _test_sp

    # Create cube
    cube = Cube(3, sp=_test_sp)

    print("=" * 60)
    print("INITIAL STATE (SOLVED)")
    print("=" * 60)
    print(dump_cube_state(cube))

    # M rotation
    print("\n" + "█" * 60)
    print("  AFTER M ROTATION")
    print("█" * 60)
    cube.m.rotate()
    print(dump_cube_state(cube))

    # Reset and do S rotation
    cube = Cube(3, sp=_test_sp)
    print("\n" + "█" * 60)
    print("  AFTER S ROTATION (axis exchange test)")
    print("█" * 60)
    cube.s.rotate()
    print(dump_cube_state(cube))


if __name__ == "__main__":
    main()
