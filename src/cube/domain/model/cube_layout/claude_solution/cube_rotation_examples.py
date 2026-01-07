"""
Cube Rotation Walker - Usage Examples
=====================================

This script demonstrates how to use the CubeRotationWalker class
to calculate coordinates visited during slice rotations on a Rubik's cube.
"""

from cube_rotation_walker import (
    CubeRotationWalker,
    Face,
    Edge,
    EdgeConnection,
    Direction,
    create_standard_edge_map,
    print_results,
    print_face_grid,
)


# =============================================================================
# EXAMPLE 1: Basic usage with standard edge map
# =============================================================================

def example_basic():
    """Basic usage with default edge map"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 70)
    
    # Create edge map (standard Rubik's cube configuration)
    edge_map = create_standard_edge_map()
    
    # Create walker with N=4 grid
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    # Calculate rotation: Start on F, rotate with R, slice index 0
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R,
        si=0
    )
    
    # Print results
    print("\nInput:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = R")
    print("  SI = 0")
    
    print("\nOutput:")
    for result in results:
        print(f"  Face {result.face.value}: {result.visited_cells}")
    
    print()


# =============================================================================
# EXAMPLE 2: Different slice indices
# =============================================================================

def example_slice_indices():
    """Show how SI affects the starting position"""
    print("=" * 70)
    print("EXAMPLE 2: Different Slice Indices")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    print("\nRotating with R from Face F:")
    print("(SI=0 is closest to R, SI=3 is farthest)\n")
    
    for si in range(4):
        results = walker.calculate_rotation(
            starting_face=Face.F,
            rotate_with=Face.R,
            si=si
        )
        
        first_face = results[0]
        print(f"  SI={si}: Start at {first_face.enter_point}, "
              f"visits column {first_face.enter_point[1]}")
    
    print()


# =============================================================================
# EXAMPLE 3: Different rotation axes
# =============================================================================

def example_rotation_axes():
    """Show rotations around different faces"""
    print("=" * 70)
    print("EXAMPLE 3: Different Rotation Axes")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    rotations = [
        (Face.F, Face.R, "Rotate with R (vertical slice)"),
        (Face.F, Face.L, "Rotate with L (vertical slice)"),
        (Face.F, Face.U, "Rotate with U (horizontal slice)"),
        (Face.F, Face.D, "Rotate with D (horizontal slice)"),
    ]
    
    for starting_face, rotate_with, description in rotations:
        results = walker.calculate_rotation(
            starting_face=starting_face,
            rotate_with=rotate_with,
            si=0
        )
        
        path = " → ".join(r.face.value for r in results)
        direction = results[0].direction.value
        
        print(f"\n{description}:")
        print(f"  Path: {path} → {results[0].face.value}")
        print(f"  Direction on first face: {direction}")
    
    print()


# =============================================================================
# EXAMPLE 4: Access detailed results
# =============================================================================

def example_detailed_results():
    """Show how to access all result data"""
    print("=" * 70)
    print("EXAMPLE 4: Detailed Results")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R,
        si=1
    )
    
    print("\nDetailed results for each face:\n")
    
    for i, result in enumerate(results, 1):
        print(f"Face {i}: {result.face.value}")
        print(f"  enter_point:    {result.enter_point}")
        print(f"  direction:      {result.direction.value}")
        print(f"  visited_cells:  {result.visited_cells}")
        print(f"  exit_edge:      {result.exit_edge.value}")
        print(f"  p_value:        {result.p_value}")
        print()


# =============================================================================
# EXAMPLE 5: Custom edge map
# =============================================================================

def example_custom_edge_map():
    """Show how to create a custom edge map"""
    print("=" * 70)
    print("EXAMPLE 5: Custom Edge Map")
    print("=" * 70)
    
    print("\nYou can define your own edge connections:")
    print("""
    custom_edge_map = {
        Face.F: {
            Edge.RIGHT: EdgeConnection(Face.R, Edge.LEFT),
            Edge.LEFT: EdgeConnection(Face.L, Edge.RIGHT),
            Edge.TOP: EdgeConnection(Face.U, Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection(Face.D, Edge.TOP),
        },
        Face.R: {
            Edge.RIGHT: EdgeConnection(Face.B, Edge.LEFT),
            Edge.LEFT: EdgeConnection(Face.F, Edge.RIGHT),
            Edge.TOP: EdgeConnection(Face.U, Edge.RIGHT),
            Edge.BOTTOM: EdgeConnection(Face.D, Edge.RIGHT),
        },
        # ... define for all 6 faces
    }
    
    walker = CubeRotationWalker(n=4, edge_map=custom_edge_map)
    """)
    
    print("Each face needs 4 edge connections (TOP, BOTTOM, LEFT, RIGHT)")
    print("Each connection specifies: adjacent face and which edge it touches")
    print()


# =============================================================================
# EXAMPLE 6: Visualize the grid
# =============================================================================

def example_visualize():
    """Show visual grid output"""
    print("=" * 70)
    print("EXAMPLE 6: Visual Grid Output")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.U,
        si=0
    )
    
    print("\nVisual representation of each face:")
    
    for result in results:
        print_face_grid(
            n=4,
            visited_cells=result.visited_cells,
            direction=result.direction,
            face_name=result.face.value
        )
    
    print()


# =============================================================================
# EXAMPLE 7: Collect all coordinates
# =============================================================================

def example_collect_coordinates():
    """Show how to collect all visited coordinates"""
    print("=" * 70)
    print("EXAMPLE 7: Collect All Coordinates")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R,
        si=0
    )
    
    # Collect all coordinates with face names
    all_coordinates = []
    for result in results:
        for row, col in result.visited_cells:
            all_coordinates.append({
                'face': result.face.value,
                'row': row,
                'col': col
            })
    
    print(f"\nTotal coordinates visited: {len(all_coordinates)}")
    print("\nFirst 8 coordinates:")
    for i, coord in enumerate(all_coordinates[:8]):
        print(f"  {i+1}. Face {coord['face']}: ({coord['row']}, {coord['col']})")
    
    print("  ...")
    print(f"\nLast coordinate:")
    last = all_coordinates[-1]
    print(f"  {len(all_coordinates)}. Face {last['face']}: ({last['row']}, {last['col']})")
    print()


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
        walker = CubeRotationWalker(n=n, edge_map=edge_map)
        
        results = walker.calculate_rotation(
            starting_face=Face.F,
            rotate_with=Face.R,
            si=0
        )
        
        total_cells = sum(len(r.visited_cells) for r in results)
        first_result = results[0]
        
        print(f"\nN={n} ({n}×{n} grid):")
        print(f"  Total cells visited: {total_cells} (4 faces × {n} cells)")
        print(f"  First face visits: {first_result.visited_cells}")
    
    print()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    example_basic()
    example_slice_indices()
    example_rotation_axes()
    example_detailed_results()
    example_custom_edge_map()
    example_visualize()
    example_collect_coordinates()
    example_grid_sizes()
    
    print("=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)
