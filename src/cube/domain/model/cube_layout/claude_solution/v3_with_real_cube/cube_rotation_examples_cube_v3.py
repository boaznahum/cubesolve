"""
Cube Rotation Walker V3 - Usage Examples
========================================

This script demonstrates how to use the CubeRotationWalkerV3 class
with fully configurable inputs (edge_map and rotation_paths).

KEY FEATURE:
  - edge_map: Provided as input (not hardcoded)
  - rotation_paths: Provided as input (not hardcoded)
  - Algorithm is completely isolated from cube-specific data

USAGE:
  Make sure cube_rotation_walker_v3.py is in the same directory or in PYTHONPATH.
  Then run: python cube_rotation_examples_v3.py
"""

# Import from the main module
from cube_rotation_walker_v3 import (
    # Core class
    CubeRotationWalkerV3,

    # Output class
    FaceOutput,

    # Data structures for input
    CubeConfig,
    EdgeConnection,
    Edge,
    Direction,

    print_results,
    print_face_grid,
)


def create_standard_rubiks_cube_config() -> CubeConfig:
    """
    Create a standard Rubik's cube configuration.

    This is an EXAMPLE of how to create input data.
    You can create your own configuration for different cube types.

    Returns:
        CubeConfig with standard Rubik's cube edge connections and rotation paths
    """

    from cube.utils import service_provider_for_tests
    cube_size = 4  # it doesnt matter
    from cube.domain.model import Cube
    cube: Cube = Cube(cube_size, service_provider_for_tests.test_sp)

    from cube.domain import model
    from cube.domain.model import FaceName
    m2c = {
        FaceName.F: "F",
        FaceName.R: "R",
        FaceName.L: "L",
        FaceName.U: "U",
        FaceName.D: "D",
        FaceName.B: "B",

    }

    edge_map: dict[str, dict[Edge, EdgeConnection]] = {}

    for f in cube.faces:
        cn: str = m2c[f.name]

        face_connection = {}
        e: model.Edge
        face_connection[Edge.RIGHT] = EdgeConnection(m2c[f.edge_right.get_other_face(f).name], Edge.LEFT)
        face_connection[Edge.LEFT] = EdgeConnection(m2c[f.edge_left.get_other_face(f).name], Edge.RIGHT)
        face_connection[Edge.TOP] = EdgeConnection(m2c[f.edge_top.get_other_face(f).name], Edge.BOTTOM)
        face_connection[Edge.BOTTOM] = EdgeConnection(m2c[f.edge_bottom.get_other_face(f).name], Edge.TOP)

        edge_map[cn] = face_connection

    # - rotation_paths: Which 4 faces surround each rotating face
    rotation_paths = {m2c[f.name]: [m2c[e.get_other_face(f).name] for e in cube.layout.get_face_edge_rotation_cw(f)] for f in cube.faces}


    return CubeConfig(edge_map=edge_map, rotation_paths=rotation_paths)


# =============================================================================
# EXAMPLE 1: Using CubeConfig
# =============================================================================

def example_using_config():
    """Basic usage with CubeConfig object"""
    print("=" * 70)
    print("EXAMPLE 1: Using CubeConfig Object")
    print("=" * 70)

    # Create configuration (contains both edge_map and rotation_paths)
    config = create_standard_rubiks_cube_config()

    # Create walker with config
    walker = CubeRotationWalkerV3(n=4, config=config)

    # Calculate rotation
    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )

    print("\nUsing CubeConfig:")
    print("  walker = CubeRotationWalkerV3(n=4, config=config)")
    print("\nResults for SI=0:")
    for face in faces:
        print(f"  Face {face.face}: {face.get_all_points(0)}")


# =============================================================================
# EXAMPLE 2: Using separate edge_map and rotation_paths
# =============================================================================


# =============================================================================
# EXAMPLE 3: Show input data structures
# =============================================================================

def example_show_input_structures():
    """Display the input data structures"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Input Data Structures")
    print("=" * 70)

    config = create_standard_rubiks_cube_config()

    print("\n1. edge_map - Maps each face to its 4 edge connections:")
    print("-" * 50)
    print("""
    edge_map = {
        "F": {
            Edge.RIGHT:  EdgeConnection("R", Edge.LEFT),   # F's RIGHT connects to R's LEFT
            Edge.LEFT:   EdgeConnection("L", Edge.RIGHT),  # F's LEFT connects to L's RIGHT
            Edge.TOP:    EdgeConnection("U", Edge.BOTTOM), # F's TOP connects to U's BOTTOM
            Edge.BOTTOM: EdgeConnection("D", Edge.TOP),    # F's BOTTOM connects to D's TOP
        },
        "R": { ... },
        "B": { ... },
        "L": { ... },
        "U": { ... },
        "D": { ... },
    }
    """)

    print("\n2. rotation_paths - Maps each face to its 4 surrounding faces (CW order):")
    print("-" * 50)
    print("""
    rotation_paths = {
        "R": ["F", "U", "B", "D"],  # Faces surrounding R, in CW order from R's view
        "L": ["F", "D", "B", "U"],  # Faces surrounding L, in CW order from L's view
        "U": ["F", "R", "B", "L"],  # Faces surrounding U
        "D": ["F", "L", "B", "R"],  # Faces surrounding D
        "F": ["U", "R", "D", "L"],  # Faces surrounding F
        "B": ["U", "L", "D", "R"],  # Faces surrounding B
    }
    """)

    print("\n3. CubeConfig - Combines both into one object:")
    print("-" * 50)
    print("""
    config = CubeConfig(
        edge_map=edge_map,
        rotation_paths=rotation_paths
    )
    
    walker = CubeRotationWalkerV3(n=4, config=config)
    """)


# =============================================================================
# EXAMPLE 4: Custom cube configuration (e.g., different orientation)
# =============================================================================


# =============================================================================
# EXAMPLE 5: Adjacency property
# =============================================================================

def example_adjacency():
    """Demonstrate the adjacency property"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Critical Adjacency Property")
    print("=" * 70)

    print("""
    CRITICAL PROPERTY:
    
    For consecutive faces f1 and f2 (f2 follows f1 in CW rotation):
    
        f1.get_point(si, N-1)  →  EXIT point (last on f1)
        f2.get_point(si, 0)    →  ENTRY point (first on f2)
        
    These points are PHYSICALLY ADJACENT on the cube!
    """)

    config = create_standard_rubiks_cube_config()
    walker = CubeRotationWalkerV3(n=4, config=config)
    n = 4

    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )

    print("Verification for SI=0:")

    for i in range(len(faces)):
        f1 = faces[i]
        f2 = faces[(i + 1) % len(faces)]

        exit_pt = f1.get_point(0, n - 1)
        entry_pt = f2.get_point(0, 0)

        print(f"\n  {f1.face} → {f2.face}:")
        print(f"    {f1.face}.get_point(0, 3) = {exit_pt}  ← EXIT")
        print(f"    {f2.face}.get_point(0, 0) = {entry_pt}  ← ENTRY")
        print(f"    Edge: {f1.exit_edge.value} ↔ {f2.enter_edge.value}")
        print(f"    ADJACENT ✓")


# =============================================================================
# EXAMPLE 6: Dynamic SI with get_point
# =============================================================================

def example_dynamic_si():
    """Show dynamic SI calculation"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Dynamic SI - One FaceOutput, Any Slice")
    print("=" * 70)

    config = create_standard_rubiks_cube_config()
    walker = CubeRotationWalkerV3(n=4, config=config)

    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )

    f0 = faces[0]

    print(f"\nFace {f0.face} - same object, different SI values:")

    for si in range(4):
        all_pts = f0.get_all_points(si)
        print(f"  SI={si}: {all_pts}")


# =============================================================================
# EXAMPLE 7: FaceOutput attributes
# =============================================================================

def example_attributes():
    """Show FaceOutput attributes"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: FaceOutput Attributes")
    print("=" * 70)

    config = create_standard_rubiks_cube_config()
    walker = CubeRotationWalkerV3(n=4, config=config)

    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )

    print("\nAll attributes for each FaceOutput:")

    for face in faces:
        print(f"\nFace {face.face}:")
        print(f"  face:          {face.face}")
        print(f"  n:             {face.n}")
        print(f"  direction:     {face.direction.value}")
        print(f"  my_edge:       {face.my_edge.value}")
        print(f"  rotating_edge: {face.rotating_edge.value}")
        print(f"  enter_edge:    {face.enter_edge.value}")
        print(f"  exit_edge:     {face.exit_edge.value}")
        print(f"  face_index:    {face.face_index}")


# =============================================================================
# EXAMPLE 8: Visual output
# =============================================================================

def example_visual():
    """Show visual grid output"""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Visual Grid Output")
    print("=" * 70)

    config = create_standard_rubiks_cube_config()
    walker = CubeRotationWalkerV3(n=4, config=config)

    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )

    print_results(faces, n=4, si=0)


# =============================================================================
# EXAMPLE 9: Different rotation axes
# =============================================================================

def example_rotation_axes():
    """Show rotations around different faces"""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Different Rotation Axes")
    print("=" * 70)

    config = create_standard_rubiks_cube_config()
    walker = CubeRotationWalkerV3(n=4, config=config)

    rotations = [
        ("F", "R", "Rotate with R"),
        ("F", "L", "Rotate with L"),
        ("F", "U", "Rotate with U"),
        ("F", "D", "Rotate with D"),
    ]

    for starting_face, rotate_with, description in rotations:
        faces = walker.calculate_rotation(
            starting_face=starting_face,
            rotate_with=rotate_with
        )

        path = " → ".join(str(f.face) for f in faces)
        f0 = faces[0]

        print(f"\n{description}:")
        print(f"  Path: {path} → {faces[0].face}")
        print(f"  Direction on {f0.face}: {f0.direction.value}")
        print(f"  SI=0 points on {f0.face}: {f0.get_all_points(0)}")


# =============================================================================
# EXAMPLE 10: Using integer face identifiers
# =============================================================================


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    example_using_config()
    example_show_input_structures()
    example_adjacency()
    example_dynamic_si()
    example_attributes()
    example_visual()
    example_rotation_axes()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)
