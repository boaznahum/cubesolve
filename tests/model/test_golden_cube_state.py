"""
Golden file tests - capture current behavior as source of truth.

WORKFLOW:
1. Run with --generate to create golden files from current (working) code
2. After refactoring, run normally to compare against golden files
3. If output matches, refactoring is correct

Run: PYTHONPATH=src pytest tests/model/test_golden_cube_state.py -v -s
Generate golden files: PYTHONPATH=src python tests/model/test_golden_cube_state.py --generate
"""

import sys
import os
from pathlib import Path

import pytest
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


GOLDEN_DIR = Path(__file__).parent / "golden_files"


def cube_state_to_text(cube: Cube) -> str:
    """
    Convert cube state to text representation.

    Format: Each face's center colors in reading order (row by row).
    This captures the complete cube state.
    """
    lines = []
    faces = [
        ('F', cube.front),
        ('U', cube.up),
        ('R', cube.right),
        ('B', cube.back),
        ('D', cube.down),
        ('L', cube.left),
    ]

    n = cube.size

    for face_name, face in faces:
        lines.append(f"=== {face_name} ({face.color.name}) ===")

        # Center colors (for n >= 3)
        if n >= 3:
            center = face.center
            n_slices = n - 2  # Center grid size
            for row in range(n_slices):
                row_colors = []
                for col in range(n_slices):
                    cs = center.get_center_slice((row, col))
                    row_colors.append(cs.color.name[0])  # First letter
                lines.append("  " + " ".join(row_colors))

        # Edge colors (simplified - just the face's own edge colors)
        edges = ['top', 'right', 'bottom', 'left']
        for edge_name in edges:
            edge = getattr(face, f'edge_{edge_name}')
            edge_color = edge.get_face_edge(face).color.name
            lines.append(f"  edge_{edge_name}: {edge_color[0]}")

        lines.append("")

    return "\n".join(lines)


def run_test_sequence(cube: Cube, sequence_name: str) -> str:
    """
    Run a specific test sequence and return the final state.
    """
    output_lines = [f"# Sequence: {sequence_name}", f"# Cube size: {cube.size}", ""]

    # Initial state
    output_lines.append("## Initial State (Solved)")
    output_lines.append(cube_state_to_text(cube))

    if sequence_name == "m_rotation":
        # M slice rotation
        output_lines.append("## After M rotation")
        cube.m.rotate()
        output_lines.append(cube_state_to_text(cube))

        output_lines.append("## After M M (2 rotations)")
        cube.m.rotate()
        output_lines.append(cube_state_to_text(cube))

    elif sequence_name == "s_rotation":
        # S slice rotation (has axis exchange)
        output_lines.append("## After S rotation")
        cube.s.rotate()
        output_lines.append(cube_state_to_text(cube))

    elif sequence_name == "e_rotation":
        # E slice rotation
        output_lines.append("## After E rotation")
        cube.e.rotate()
        output_lines.append(cube_state_to_text(cube))

    elif sequence_name == "face_f_rotation":
        # Front face rotation
        output_lines.append("## After F rotation")
        cube.front.rotate()
        output_lines.append(cube_state_to_text(cube))

    elif sequence_name == "complex_sequence":
        # A complex sequence that exercises multiple code paths
        output_lines.append("## After M S E sequence")
        cube.m.rotate()
        cube.s.rotate()
        cube.e.rotate()
        output_lines.append(cube_state_to_text(cube))

        output_lines.append("## After F R U sequence")
        cube.front.rotate()
        cube.right.rotate()
        cube.up.rotate()
        output_lines.append(cube_state_to_text(cube))

    return "\n".join(output_lines)


# Test sequences to generate/verify
TEST_SEQUENCES = [
    ("3x3", 3, "m_rotation"),
    ("3x3", 3, "s_rotation"),
    ("3x3", 3, "e_rotation"),
    ("3x3", 3, "face_f_rotation"),
    ("3x3", 3, "complex_sequence"),
    ("4x4", 4, "m_rotation"),
    ("4x4", 4, "s_rotation"),
    ("5x5", 5, "m_rotation"),
    ("5x5", 5, "complex_sequence"),
]


def generate_golden_files():
    """Generate golden files from current (working) code."""
    GOLDEN_DIR.mkdir(exist_ok=True)

    print(f"Generating golden files in {GOLDEN_DIR}")
    print("=" * 60)

    for size_name, size, sequence in TEST_SEQUENCES:
        filename = f"golden_{size_name}_{sequence}.txt"
        filepath = GOLDEN_DIR / filename

        cube = Cube(size, sp=_test_sp)
        output = run_test_sequence(cube, sequence)

        filepath.write_text(output)
        print(f"Generated: {filename}")

    print("=" * 60)
    print(f"Generated {len(TEST_SEQUENCES)} golden files")
    print("\nThese files capture the current (correct) behavior.")
    print("After refactoring, run pytest to verify behavior matches.")


class TestGoldenFiles:
    """Compare current behavior against golden files."""

    @pytest.fixture(autouse=True)
    def check_golden_files_exist(self):
        """Ensure golden files exist before running tests."""
        if not GOLDEN_DIR.exists():
            pytest.skip(
                f"Golden files not found at {GOLDEN_DIR}. "
                f"Run with --generate first to create them."
            )

    @pytest.mark.parametrize("size_name,size,sequence", TEST_SEQUENCES)
    def test_against_golden(self, size_name, size, sequence):
        """Verify current behavior matches golden file."""
        filename = f"golden_{size_name}_{sequence}.txt"
        filepath = GOLDEN_DIR / filename

        if not filepath.exists():
            pytest.skip(f"Golden file {filename} not found")

        # Run the same sequence
        cube = Cube(size, sp=_test_sp)
        actual_output = run_test_sequence(cube, sequence)

        # Load golden file
        expected_output = filepath.read_text()

        # Compare
        if actual_output != expected_output:
            # Show diff for debugging
            actual_lines = actual_output.split("\n")
            expected_lines = expected_output.split("\n")

            diff_lines = []
            for i, (actual, expected) in enumerate(zip(actual_lines, expected_lines)):
                if actual != expected:
                    diff_lines.append(f"Line {i+1}:")
                    diff_lines.append(f"  Expected: {expected}")
                    diff_lines.append(f"  Actual:   {actual}")

            if len(actual_lines) != len(expected_lines):
                diff_lines.append(f"Line count: expected {len(expected_lines)}, got {len(actual_lines)}")

            pytest.fail(
                f"Output differs from golden file {filename}:\n" +
                "\n".join(diff_lines[:20])  # First 20 differences
            )


if __name__ == "__main__":
    if "--generate" in sys.argv:
        generate_golden_files()
    else:
        print("Usage:")
        print("  Generate golden files: python test_golden_cube_state.py --generate")
        print("  Run tests:            pytest test_golden_cube_state.py -v")
