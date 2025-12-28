#!/usr/bin/env python3
"""
Find all valid f1/f2 arrangements for cube edge coordinate system.

This script exhaustively searches all possible configurations to find
arrangements where all 6 faces have consistent ltr coordinates.

The constraint: for each face, opposite edges must agree on ltr mapping.
- left and right edges must agree
- top and bottom edges must agree
"""

from itertools import product
from dataclasses import dataclass
from typing import Iterator


@dataclass
class EdgeConfig:
    """Configuration for a single edge."""
    name: str
    face1: str  # First face in edge name
    face2: str  # Second face in edge name
    same_direction: bool  # True = both faces see slices same way
    f1_is_face1: bool = True  # When same_direction=False, is face1 the f1?


# The 12 edges of the cube with their geometric True/False values
# (These are determined by cube geometry - R/T direction alignment)
EDGES = [
    # True edges (8) - faces see slices same direction
    ("F-U", "F", "U", True),
    ("F-L", "F", "L", True),
    ("F-R", "F", "R", True),
    ("F-D", "F", "D", True),
    ("L-D", "L", "D", True),
    ("R-B", "R", "B", True),
    ("L-B", "L", "B", True),
    ("U-R", "U", "R", True),
    # False edges (4) - faces see slices in opposite directions
    ("L-U", "L", "U", False),
    ("D-R", "D", "R", False),
    ("D-B", "D", "B", False),
    ("U-B", "U", "B", False),
]

# Which edge is used for each face's edge_top/bottom/left/right
FACE_EDGE_POSITIONS = {
    "F": {"top": "F-U", "bottom": "F-D", "left": "F-L", "right": "F-R"},
    "L": {"top": "L-U", "bottom": "L-D", "left": "L-B", "right": "F-L"},
    "R": {"top": "U-R", "bottom": "D-R", "left": "F-R", "right": "R-B"},
    "U": {"top": "U-B", "bottom": "F-U", "left": "L-U", "right": "U-R"},
    "D": {"top": "F-D", "bottom": "D-B", "left": "L-D", "right": "D-R"},
    "B": {"top": "U-B", "bottom": "D-B", "left": "R-B", "right": "L-B"},
}


def get_edge_info(edge_name: str) -> tuple[str, str, bool]:
    """Get (face1, face2, same_direction) for an edge."""
    for name, f1, f2, same_dir in EDGES:
        if name == edge_name:
            return f1, f2, same_dir
    raise ValueError(f"Unknown edge: {edge_name}")


def does_face_invert(face: str, edge_name: str, f1_assignments: dict[str, str]) -> bool:
    """
    Check if a face inverts when accessing an edge.

    Args:
        face: The face accessing the edge
        edge_name: The edge being accessed
        f1_assignments: Maps edge_name -> which face is f1 (for False edges)

    Returns:
        True if the face sees inverted indices
    """
    face1, face2, same_direction = get_edge_info(edge_name)

    if same_direction:
        return False  # True edges never invert

    # For False edges, f2 inverts
    f1 = f1_assignments.get(edge_name)
    if f1 is None:
        raise ValueError(f"No f1 assignment for False edge {edge_name}")

    return face != f1  # Face inverts if it's f2


def check_face_consistency(face: str, f1_assignments: dict[str, str]) -> tuple[bool, str]:
    """
    Check if a face's opposite edges agree on ltr.

    Returns:
        (is_consistent, failure_reason)
    """
    positions = FACE_EDGE_POSITIONS[face]

    # Check top/bottom (horizontal edges)
    top_edge = positions["top"]
    bottom_edge = positions["bottom"]
    top_inverts = does_face_invert(face, top_edge, f1_assignments)
    bottom_inverts = does_face_invert(face, bottom_edge, f1_assignments)

    if top_inverts != bottom_inverts:
        return False, f"top({top_edge})={top_inverts} != bottom({bottom_edge})={bottom_inverts}"

    # Check left/right (vertical edges)
    left_edge = positions["left"]
    right_edge = positions["right"]
    left_inverts = does_face_invert(face, left_edge, f1_assignments)
    right_inverts = does_face_invert(face, right_edge, f1_assignments)

    if left_inverts != right_inverts:
        return False, f"left({left_edge})={left_inverts} != right({right_edge})={right_inverts}"

    return True, "OK"


def get_false_edges() -> list[tuple[str, str, str]]:
    """Get list of (edge_name, face1, face2) for False edges."""
    return [(name, f1, f2) for name, f1, f2, same_dir in EDGES if not same_dir]


def generate_all_f1_assignments() -> Iterator[dict[str, str]]:
    """Generate all possible f1 assignments for False edges."""
    false_edges = get_false_edges()

    # Each False edge can have either face as f1
    for choices in product([0, 1], repeat=len(false_edges)):
        assignment = {}
        for (edge_name, face1, face2), choice in zip(false_edges, choices):
            assignment[edge_name] = face1 if choice == 0 else face2
        yield assignment


def check_all_faces(f1_assignments: dict[str, str]) -> list[tuple[str, str]]:
    """Check all faces and return list of (face, failure_reason) for failures."""
    failures = []
    for face in ["F", "L", "R", "U", "D", "B"]:
        ok, reason = check_face_consistency(face, f1_assignments)
        if not ok:
            failures.append((face, reason))
    return failures


def main():
    print("=" * 70)
    print("EXHAUSTIVE SEARCH: Finding valid f1/f2 arrangements")
    print("=" * 70)

    false_edges = get_false_edges()
    print(f"\nFalse edges ({len(false_edges)}):")
    for edge_name, f1, f2 in false_edges:
        print(f"  {edge_name}: {f1} or {f2} can be f1")

    print(f"\nTotal combinations to check: 2^{len(false_edges)} = {2**len(false_edges)}")
    print("-" * 70)

    solutions = []
    best_result = None

    for assignment in generate_all_f1_assignments():
        failures = check_all_faces(assignment)

        if not failures:
            solutions.append(assignment)

        if best_result is None or len(failures) < len(best_result[1]):
            best_result = (assignment, failures)

    # Report results
    print(f"\n{'=' * 70}")
    print("RESULTS")
    print("=" * 70)

    if solutions:
        print(f"\n✓ FOUND {len(solutions)} VALID SOLUTION(S):\n")
        for i, sol in enumerate(solutions, 1):
            print(f"Solution {i}:")
            for edge_name, f1 in sol.items():
                _, face1, face2 = next((e for e in false_edges if e[0] == edge_name))
                f2 = face2 if f1 == face1 else face1
                print(f"  {edge_name}: f1={f1}, f2={f2}")
            print()
    else:
        print("\n✗ NO VALID SOLUTION EXISTS\n")
        print(f"Best result has {len(best_result[1])} failing face(s):\n")

        assignment, failures = best_result
        print("Assignment:")
        for edge_name, f1 in assignment.items():
            print(f"  {edge_name}: f1={f1}")

        print("\nFailing faces:")
        for face, reason in failures:
            print(f"  Face {face}: {reason}")

    # Show why it's unsatisfiable (constraint analysis)
    print("\n" + "=" * 70)
    print("CONSTRAINT ANALYSIS")
    print("=" * 70)

    print("\nFor each face, derive what f1 assignment it needs:\n")

    for face in ["F", "L", "R", "U", "D", "B"]:
        positions = FACE_EDGE_POSITIONS[face]
        constraints = []

        # Check top/bottom
        top_edge = positions["top"]
        bottom_edge = positions["bottom"]
        top_f1, top_f2, top_same = get_edge_info(top_edge)
        bot_f1, bot_f2, bot_same = get_edge_info(bottom_edge)

        if not top_same and bot_same:
            # Top is False, bottom is True (doesn't invert)
            # Top must not invert -> face must be f1 in top
            constraints.append(f"{top_edge}: {face}=f1 (to match True {bottom_edge})")
        elif top_same and not bot_same:
            constraints.append(f"{bottom_edge}: {face}=f1 (to match True {top_edge})")
        elif not top_same and not bot_same:
            constraints.append(f"{top_edge} and {bottom_edge}: must agree (both {face}=f1 or both {face}=f2)")

        # Check left/right
        left_edge = positions["left"]
        right_edge = positions["right"]
        left_f1, left_f2, left_same = get_edge_info(left_edge)
        right_f1, right_f2, right_same = get_edge_info(right_edge)

        if not left_same and right_same:
            constraints.append(f"{left_edge}: {face}=f1 (to match True {right_edge})")
        elif left_same and not right_same:
            constraints.append(f"{right_edge}: {face}=f1 (to match True {left_edge})")
        elif not left_same and not right_same:
            constraints.append(f"{left_edge} and {right_edge}: must agree")

        if constraints:
            print(f"Face {face}:")
            for c in constraints:
                print(f"  → {c}")
        else:
            print(f"Face {face}: All True edges, no constraints")

    # Show conflicts
    print("\n" + "-" * 70)
    print("CONFLICTS (edges where both faces need f1):")
    print("-" * 70)

    # Manually identify conflicts based on constraints
    conflicts = []

    # L-U: L needs f1 (Face L constraint), U needs f1 (Face U constraint)
    # D-R: R needs f1 (Face R constraint), D needs f1 (Face D constraint)

    for edge_name, face1, face2 in false_edges:
        face1_needs_f1 = False
        face2_needs_f1 = False

        # Check if face1 needs to be f1 in this edge
        for pos_name, pos_edge in FACE_EDGE_POSITIONS[face1].items():
            if pos_edge == edge_name:
                # Find the opposite edge
                if pos_name == "top":
                    opp_edge = FACE_EDGE_POSITIONS[face1]["bottom"]
                elif pos_name == "bottom":
                    opp_edge = FACE_EDGE_POSITIONS[face1]["top"]
                elif pos_name == "left":
                    opp_edge = FACE_EDGE_POSITIONS[face1]["right"]
                else:
                    opp_edge = FACE_EDGE_POSITIONS[face1]["left"]

                _, _, opp_same = get_edge_info(opp_edge)
                if opp_same:  # Opposite is True (doesn't invert)
                    face1_needs_f1 = True

        # Check if face2 needs to be f1 in this edge
        for pos_name, pos_edge in FACE_EDGE_POSITIONS[face2].items():
            if pos_edge == edge_name:
                if pos_name == "top":
                    opp_edge = FACE_EDGE_POSITIONS[face2]["bottom"]
                elif pos_name == "bottom":
                    opp_edge = FACE_EDGE_POSITIONS[face2]["top"]
                elif pos_name == "left":
                    opp_edge = FACE_EDGE_POSITIONS[face2]["right"]
                else:
                    opp_edge = FACE_EDGE_POSITIONS[face2]["left"]

                _, _, opp_same = get_edge_info(opp_edge)
                if opp_same:
                    face2_needs_f1 = True

        if face1_needs_f1 and face2_needs_f1:
            conflicts.append((edge_name, face1, face2))

    if conflicts:
        for edge_name, f1, f2 in conflicts:
            print(f"\n  {edge_name}: Both {f1} and {f2} need to be f1!")
            print(f"    - {f1} needs f1 because its opposite edge is True")
            print(f"    - {f2} needs f1 because its opposite edge is True")
    else:
        print("\n  No conflicts found!")


if __name__ == "__main__":
    main()
