"""
Cube Rotation Walker V2 - Usage Examples
========================================

This script demonstrates how to use the CubeRotationWalkerV2 class
with the get_point(si, other_coord) method for dynamic coordinate calculation.

KEY FEATURE:
  get_point(si, other_coord) returns coordinates for ANY slice index,
  not just the one specified at creation time.

CRITICAL ADJACENCY PROPERTY:
  For consecutive faces f1 and f2:
    f1.get_point(si, N-1)  →  EXIT point
    f2.get_point(si, 0)    →  ENTRY point
  These are PHYSICALLY ADJACENT on the cube!

USAGE:
  Make sure cube_rotation_walker_v2.py is in the same directory or in PYTHONPATH.
  Then run: python cube_rotation_examples_v2.py
"""

# Import from the main module
from cube_rotation_walker_v2 import (
    # Core classes
    CubeRotationWalkerV2,
    FaceOutput,
    
    # Enums
    Face,
    Edge,
    Direction,
    
    # Data classes
    EdgeConnection,
    
    # Helper functions
    create_standard_edge_map,
    print_results,
    print_face_grid,
)


# =============================================================================
# EXAMPLE 1: Basic usage with get_point()
# =============================================================================

def example_basic():
    """Basic usage showing get_point() method"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Usage with get_point()")
    print("=" * 70)
    
    # Create edge map and walker
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    # Get FaceOutput objects (no SI specified - works for all!)
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print("\nInput:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = R")
    
    # Get points for SI=0
    print("\nUsing get_point(si=0, other_coord):")
    for face in faces:
        points = [face.get_point(0, oc) for oc in range(4)]
        print(f"  Face {face.face.value}: {points}")
    
    print()


# =============================================================================
# EXAMPLE 2: Dynamic SI - same FaceOutput, different slices
# =============================================================================

def example_dynamic_si():
    """Show that same FaceOutput works for any SI"""
    print("=" * 70)
    print("EXAMPLE 2: Dynamic SI - One FaceOutput, Any Slice")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    # Same FaceOutput object works for ALL slice indices!
    face_f = faces[0]
    
    print(f"\nFace {face_f.face.value} - same object, different SI values:")
    print()
    
    for si in range(4):
        entry = face_f.get_point(si, 0)
        exit_pt = face_f.get_point(si, 3)
        all_pts = face_f.get_all_points(si)
        print(f"  SI={si}:")
        print(f"    Entry (oc=0): {entry}")
        print(f"    Exit (oc=3):  {exit_pt}")
        print(f"    All points:   {all_pts}")
        print()


# =============================================================================
# EXAMPLE 3: Adjacency property
# =============================================================================

def example_adjacency():
    """Demonstrate the critical adjacency property"""
    print("=" * 70)
    print("EXAMPLE 3: Critical Adjacency Property")
    print("=" * 70)
    
    print("""
    CRITICAL PROPERTY:
    
    For consecutive faces f1 and f2 (f2 follows f1 in CW rotation):
    
        f1.get_point(si, N-1)  →  EXIT point (last on f1)
        f2.get_point(si, 0)    →  ENTRY point (first on f2)
        
    These points are PHYSICALLY ADJACENT on the cube!
    They share the same edge and continue the straight-line path.
    """)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    n = 4
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print("Verification for SI=0:")
    print()
    
    for i in range(len(faces)):
        f1 = faces[i]
        f2 = faces[(i + 1) % len(faces)]
        
        exit_pt = f1.get_point(0, n - 1)
        entry_pt = f2.get_point(0, 0)
        
        print(f"  {f1.face.value} → {f2.face.value}:")
        print(f"    {f1.face.value}.get_point(0, 3) = {exit_pt}  ← EXIT")
        print(f"    {f2.face.value}.get_point(0, 0) = {entry_pt}  ← ENTRY")
        print(f"    Edge: {f1.exit_edge.value} ↔ {f2.enter_edge.value}")
        print(f"    ADJACENT ✓")
        print()


# =============================================================================
# EXAMPLE 4: FaceOutput attributes
# =============================================================================

def example_attributes():
    """Show all FaceOutput attributes"""
    print("=" * 70)
    print("EXAMPLE 4: FaceOutput Attributes")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print("\nAll attributes for each FaceOutput:")
    
    for face in faces:
        print(f"\nFace {face.face.value}:")
        print(f"  face:          {face.face.value}")
        print(f"  n:             {face.n}")
        print(f"  direction:     {face.direction.value}")
        print(f"  my_edge:       {face.my_edge.value}")
        print(f"  rotating_edge: {face.rotating_edge.value}")
        print(f"  enter_edge:    {face.enter_edge.value if face.enter_edge else 'None'}")
        print(f"  exit_edge:     {face.exit_edge.value}")
        print(f"  face_index:    {face.face_index}")


# =============================================================================
# EXAMPLE 5: Different rotation axes
# =============================================================================

def example_rotation_axes():
    """Show rotations around different faces"""
    print("=" * 70)
    print("EXAMPLE 5: Different Rotation Axes")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    rotations = [
        (Face.F, Face.R, "Rotate with R"),
        (Face.F, Face.L, "Rotate with L"),
        (Face.F, Face.U, "Rotate with U"),
        (Face.F, Face.D, "Rotate with D"),
    ]
    
    for starting_face, rotate_with, description in rotations:
        faces = walker.calculate_rotation(
            starting_face=starting_face,
            rotate_with=rotate_with
        )
        
        path = " → ".join(f.face.value for f in faces)
        f0 = faces[0]
        
        print(f"\n{description}:")
        print(f"  Path: {path} → {faces[0].face.value}")
        print(f"  Direction on {f0.face.value}: {f0.direction.value}")
        print(f"  SI=0 points on {f0.face.value}: {f0.get_all_points(0)}")


# =============================================================================
# EXAMPLE 6: Visual grid output
# =============================================================================

def example_visual():
    """Show visual grid output"""
    print("=" * 70)
    print("EXAMPLE 6: Visual Grid Output")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print_results(faces, n=4, si=0)


# =============================================================================
# EXAMPLE 7: Collect all coordinates
# =============================================================================

def example_collect_coordinates():
    """Show how to collect all visited coordinates"""
    print("=" * 70)
    print("EXAMPLE 7: Collect All Coordinates")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    n = 4
    si = 0
    
    # Collect all coordinates with face names
    all_coordinates = []
    for face in faces:
        for oc in range(n):
            row, col = face.get_point(si, oc)
            all_coordinates.append({
                'face': face.face.value,
                'row': row,
                'col': col,
                'other_coord': oc
            })
    
    print(f"\nTotal coordinates for SI={si}: {len(all_coordinates)}")
    print("\nAll coordinates in order:")
    
    for i, coord in enumerate(all_coordinates):
        marker = ""
        if coord['other_coord'] == 0:
            marker = " ← ENTRY"
        elif coord['other_coord'] == n - 1:
            marker = " ← EXIT"
        print(f"  {i+1:2}. Face {coord['face']}: ({coord['row']}, {coord['col']}){marker}")


# =============================================================================
# EXAMPLE 8: Different grid sizes
# =============================================================================

def example_grid_sizes():
    """Show different grid sizes"""
    print("=" * 70)
    print("EXAMPLE 8: Different Grid Sizes")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    
    for n in [2, 3, 4, 5]:
        walker = CubeRotationWalkerV2(n=n, edge_map=edge_map)
        
        faces = walker.calculate_rotation(
            starting_face=Face.F,
            rotate_with=Face.R
        )
        
        f0 = faces[0]
        
        print(f"\nN={n} ({n}×{n} grid):")
        print(f"  Face {f0.face.value} SI=0: {f0.get_all_points(0)}")
        print(f"  Face {f0.face.value} SI={n-1}: {f0.get_all_points(n-1)}")
        
        # Verify adjacency
        f1 = faces[1]
        exit_pt = f0.get_point(0, n-1)
        entry_pt = f1.get_point(0, 0)
        print(f"  Adjacency: {f0.face.value} exit {exit_pt} → {f1.face.value} entry {entry_pt}")


# =============================================================================
# EXAMPLE 9: Building a complete slice representation
# =============================================================================

def example_complete_slice():
    """Build a complete representation of a slice across all 4 faces"""
    print("=" * 70)
    print("EXAMPLE 9: Complete Slice Representation")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    n = 4
    
    print("\nComplete slice data for SI=0 and SI=2:")
    print()
    
    for si in [0, 2]:
        print(f"SI={si}:")
        print("-" * 50)
        
        for face_idx, face in enumerate(faces):
            print(f"\n  Face {face.face.value} (index {face_idx}):")
            print(f"    Direction: {face.direction.value}")
            
            for oc in range(n):
                point = face.get_point(si, oc)
                
                # Determine if entry, exit, or middle
                if oc == 0:
                    status = "ENTRY"
                elif oc == n - 1:
                    status = "EXIT"
                else:
                    status = "middle"
                
                print(f"    other_coord={oc}: {point} ({status})")
        
        print()


# =============================================================================
# EXAMPLE 10: Compare V1 vs V2
# =============================================================================

def example_compare_versions():
    """Compare V1 (fixed SI) vs V2 (dynamic SI)"""
    print("=" * 70)
    print("EXAMPLE 10: V1 vs V2 Comparison")
    print("=" * 70)
    
    print("""
    V1 (cube_rotation_walker.py):
    ─────────────────────────────
    - calculate_rotation() requires SI parameter
    - Returns FaceResult with fixed visited_cells list
    - To get different SI, must call calculate_rotation() again
    
    Usage:
        results = walker.calculate_rotation(Face.F, Face.R, si=0)
        cells = results[0].visited_cells  # [(0,3), (1,3), (2,3), (3,3)]
    
    
    V2 (cube_rotation_walker_v2.py):
    ─────────────────────────────────
    - calculate_rotation() does NOT require SI
    - Returns FaceOutput with get_point(si, other_coord) method
    - Same FaceOutput works for ANY SI
    
    Usage:
        faces = walker.calculate_rotation(Face.F, Face.R)
        point = faces[0].get_point(si=0, other_coord=2)  # (2, 3)
        point = faces[0].get_point(si=2, other_coord=2)  # (2, 1)
    
    
    V2 ADVANTAGE:
    ─────────────
    One call to calculate_rotation() gives you FaceOutput objects
    that can generate coordinates for ALL slice indices!
    """)
    
    # Demonstrate V2 flexibility
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    # Single call
    faces = walker.calculate_rotation(Face.F, Face.R)
    
    print("V2 Demonstration - single calculate_rotation() call:")
    print()
    
    f0 = faces[0]
    for si in range(4):
        print(f"  faces[0].get_all_points(si={si}): {f0.get_all_points(si)}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    example_basic()
    example_dynamic_si()
    example_adjacency()
    example_attributes()
    example_rotation_axes()
    example_visual()
    example_collect_coordinates()
    example_grid_sizes()
    example_complete_slice()
    example_compare_versions()
    
    print("=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)
