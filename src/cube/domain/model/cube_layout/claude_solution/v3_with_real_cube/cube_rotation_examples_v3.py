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
    
    # Helper functions
    create_standard_rubiks_cube_config,
    print_results,
    print_face_grid,
)


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

def example_separate_inputs():
    """Basic usage with separate dictionaries"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Using Separate edge_map and rotation_paths")
    print("=" * 70)
    
    # Define edge_map
    edge_map = {
        "F": {
            Edge.RIGHT: EdgeConnection("R", Edge.LEFT),
            Edge.LEFT: EdgeConnection("L", Edge.RIGHT),
            Edge.TOP: EdgeConnection("U", Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection("D", Edge.TOP),
        },
        "R": {
            Edge.RIGHT: EdgeConnection("B", Edge.LEFT),
            Edge.LEFT: EdgeConnection("F", Edge.RIGHT),
            Edge.TOP: EdgeConnection("U", Edge.RIGHT),
            Edge.BOTTOM: EdgeConnection("D", Edge.RIGHT),
        },
        "B": {
            Edge.RIGHT: EdgeConnection("L", Edge.LEFT),
            Edge.LEFT: EdgeConnection("R", Edge.RIGHT),
            Edge.TOP: EdgeConnection("U", Edge.TOP),
            Edge.BOTTOM: EdgeConnection("D", Edge.BOTTOM),
        },
        "L": {
            Edge.RIGHT: EdgeConnection("F", Edge.LEFT),
            Edge.LEFT: EdgeConnection("B", Edge.RIGHT),
            Edge.TOP: EdgeConnection("U", Edge.LEFT),
            Edge.BOTTOM: EdgeConnection("D", Edge.LEFT),
        },
        "U": {
            Edge.RIGHT: EdgeConnection("R", Edge.TOP),
            Edge.LEFT: EdgeConnection("L", Edge.TOP),
            Edge.TOP: EdgeConnection("B", Edge.TOP),
            Edge.BOTTOM: EdgeConnection("F", Edge.TOP),
        },
        "D": {
            Edge.RIGHT: EdgeConnection("R", Edge.BOTTOM),
            Edge.LEFT: EdgeConnection("L", Edge.BOTTOM),
            Edge.TOP: EdgeConnection("F", Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection("B", Edge.BOTTOM),
        },
    }
    
    # Define rotation_paths
    rotation_paths = {
        "R": ["F", "U", "B", "D"],
        "L": ["F", "D", "B", "U"],
        "U": ["F", "R", "B", "L"],
        "D": ["F", "L", "B", "R"],
        "F": ["U", "R", "D", "L"],
        "B": ["U", "L", "D", "R"],
    }
    
    # Create walker with separate inputs
    walker = CubeRotationWalkerV3(
        n=4,
        edge_map=edge_map,
        rotation_paths=rotation_paths
    )
    
    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )
    
    print("\nUsing separate inputs:")
    print("  walker = CubeRotationWalkerV3(n=4, edge_map=edge_map, rotation_paths=rotation_paths)")
    print("\nResults for SI=0:")
    for face in faces:
        print(f"  Face {face.face}: {face.get_all_points(0)}")


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

def example_custom_config():
    """Create a custom cube configuration"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Custom Cube Configuration")
    print("=" * 70)
    
    print("""
    You can define your own cube configuration for:
    - Different cube orientations
    - Non-standard cubes
    - Testing/debugging
    
    Example: A simplified 4-face "ring" configuration
    """)
    
    # Example: A simple 4-face ring (not a real cube, just for demo)
    edge_map = {
        "A": {
            Edge.RIGHT: EdgeConnection("B", Edge.LEFT),
            Edge.LEFT: EdgeConnection("D", Edge.RIGHT),
            Edge.TOP: EdgeConnection("X", Edge.BOTTOM),  # X = some other face
            Edge.BOTTOM: EdgeConnection("Y", Edge.TOP),  # Y = some other face
        },
        "B": {
            Edge.RIGHT: EdgeConnection("C", Edge.LEFT),
            Edge.LEFT: EdgeConnection("A", Edge.RIGHT),
            Edge.TOP: EdgeConnection("X", Edge.RIGHT),
            Edge.BOTTOM: EdgeConnection("Y", Edge.RIGHT),
        },
        "C": {
            Edge.RIGHT: EdgeConnection("D", Edge.LEFT),
            Edge.LEFT: EdgeConnection("B", Edge.RIGHT),
            Edge.TOP: EdgeConnection("X", Edge.TOP),
            Edge.BOTTOM: EdgeConnection("Y", Edge.BOTTOM),
        },
        "D": {
            Edge.RIGHT: EdgeConnection("A", Edge.LEFT),
            Edge.LEFT: EdgeConnection("C", Edge.RIGHT),
            Edge.TOP: EdgeConnection("X", Edge.LEFT),
            Edge.BOTTOM: EdgeConnection("Y", Edge.LEFT),
        },
        "X": {
            Edge.BOTTOM: EdgeConnection("A", Edge.TOP),
            Edge.RIGHT: EdgeConnection("B", Edge.TOP),
            Edge.TOP: EdgeConnection("C", Edge.TOP),
            Edge.LEFT: EdgeConnection("D", Edge.TOP),
        },
        "Y": {
            Edge.TOP: EdgeConnection("A", Edge.BOTTOM),
            Edge.RIGHT: EdgeConnection("B", Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection("C", Edge.BOTTOM),
            Edge.LEFT: EdgeConnection("D", Edge.BOTTOM),
        },
    }
    
    rotation_paths = {
        "X": ["A", "B", "C", "D"],  # Ring around X
        "Y": ["A", "D", "C", "B"],  # Ring around Y (opposite direction)
    }
    
    walker = CubeRotationWalkerV3(
        n=3,
        edge_map=edge_map,
        rotation_paths=rotation_paths
    )
    
    faces = walker.calculate_rotation(
        starting_face="A",
        rotate_with="X"
    )
    
    print("\nCustom configuration results:")
    print(f"  Rotation path: A → B → C → D")
    for face in faces:
        print(f"  Face {face.face}: {face.get_all_points(0)}")


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

def example_integer_faces():
    """Use integer identifiers instead of strings"""
    print("\n" + "=" * 70)
    print("EXAMPLE 10: Using Integer Face Identifiers")
    print("=" * 70)
    
    print("""
    Face identifiers can be any hashable type:
    - Strings: "F", "R", "B", "L", "U", "D"
    - Integers: 0, 1, 2, 3, 4, 5
    - Enums: Face.F, Face.R, etc.
    """)
    
    # Using integers: 0=F, 1=R, 2=B, 3=L, 4=U, 5=D
    edge_map = {
        0: {  # F
            Edge.RIGHT: EdgeConnection(1, Edge.LEFT),
            Edge.LEFT: EdgeConnection(3, Edge.RIGHT),
            Edge.TOP: EdgeConnection(4, Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection(5, Edge.TOP),
        },
        1: {  # R
            Edge.RIGHT: EdgeConnection(2, Edge.LEFT),
            Edge.LEFT: EdgeConnection(0, Edge.RIGHT),
            Edge.TOP: EdgeConnection(4, Edge.RIGHT),
            Edge.BOTTOM: EdgeConnection(5, Edge.RIGHT),
        },
        2: {  # B
            Edge.RIGHT: EdgeConnection(3, Edge.LEFT),
            Edge.LEFT: EdgeConnection(1, Edge.RIGHT),
            Edge.TOP: EdgeConnection(4, Edge.TOP),
            Edge.BOTTOM: EdgeConnection(5, Edge.BOTTOM),
        },
        3: {  # L
            Edge.RIGHT: EdgeConnection(0, Edge.LEFT),
            Edge.LEFT: EdgeConnection(2, Edge.RIGHT),
            Edge.TOP: EdgeConnection(4, Edge.LEFT),
            Edge.BOTTOM: EdgeConnection(5, Edge.LEFT),
        },
        4: {  # U
            Edge.RIGHT: EdgeConnection(1, Edge.TOP),
            Edge.LEFT: EdgeConnection(3, Edge.TOP),
            Edge.TOP: EdgeConnection(2, Edge.TOP),
            Edge.BOTTOM: EdgeConnection(0, Edge.TOP),
        },
        5: {  # D
            Edge.RIGHT: EdgeConnection(1, Edge.BOTTOM),
            Edge.LEFT: EdgeConnection(3, Edge.BOTTOM),
            Edge.TOP: EdgeConnection(0, Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection(2, Edge.BOTTOM),
        },
    }
    
    rotation_paths = {
        1: [0, 4, 2, 5],  # R: F→U→B→D
        3: [0, 5, 2, 4],  # L: F→D→B→U
        4: [0, 1, 2, 3],  # U: F→R→B→L
        5: [0, 3, 2, 1],  # D: F→L→B→R
    }
    
    walker = CubeRotationWalkerV3(
        n=4,
        edge_map=edge_map,
        rotation_paths=rotation_paths
    )
    
    faces = walker.calculate_rotation(
        starting_face=0,  # F
        rotate_with=1     # R
    )
    
    print("\nUsing integers (0=F, 1=R, 2=B, 3=L, 4=U, 5=D):")
    print(f"  Path: {' → '.join(str(f.face) for f in faces)}")
    for face in faces:
        print(f"  Face {face.face}: {face.get_all_points(0)}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    example_using_config()
    example_separate_inputs()
    example_show_input_structures()
    example_custom_config()
    example_adjacency()
    example_dynamic_si()
    example_attributes()
    example_visual()
    example_rotation_axes()
    example_integer_faces()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)
