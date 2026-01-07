"""
Cube Grid Coordinate Transformation - Complete Implementation
==============================================================

This module implements slice rotation on a 3D Rubik's cube where each face 
has an N×N grid. Given a starting face, rotating face, and slice index,
it calculates all coordinates visited on each face during the rotation.

INPUT:
  - N: Grid size (e.g., 4 means 4×4 grid)
  - starting_face: Which face you're on (F, B, L, R, U, D)
  - rotate_with: Which face to rotate with
  - SI: Slice Index (0 = closest to rotating face, N-1 = farthest)
  - edge_map: Edge connection map between faces

OUTPUT:
  - For each of 4 faces in the rotation path:
    - Face name
    - Enter point (row, col)
    - Direction
    - Visited cells (N coordinates)
    - Exit edge
    - P value
"""

from enum import Enum
from typing import List, Tuple, Dict
from dataclasses import dataclass


class Edge(Enum):
    """Edge names on a face"""
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Direction(Enum):
    """Walking directions"""
    LEFT_TO_RIGHT = "LEFT→RIGHT"
    RIGHT_TO_LEFT = "RIGHT→LEFT"
    BOTTOM_TO_TOP = "BOTTOM→TOP"
    TOP_TO_BOTTOM = "TOP→BOTTOM"


class Face(Enum):
    """Rubik's cube face names"""
    F = "F"  # Front
    B = "B"  # Back
    L = "L"  # Left
    R = "R"  # Right
    U = "U"  # Up
    D = "D"  # Down


@dataclass
class EdgeConnection:
    """Represents a connection between two face edges"""
    face: Face
    edge: Edge


@dataclass
class FaceResult:
    """Result of walking on one face"""
    face: Face
    enter_point: Tuple[int, int]
    direction: Direction
    visited_cells: List[Tuple[int, int]]
    exit_edge: Edge
    p_value: int


class CubeRotationWalker:
    """
    Calculates coordinates visited during a slice rotation on a Rubik's cube.
    
    Usage:
        # Define edge connections
        edge_map = {
            Face.F: {
                Edge.RIGHT: EdgeConnection(Face.R, Edge.LEFT),
                Edge.LEFT: EdgeConnection(Face.L, Edge.RIGHT),
                Edge.TOP: EdgeConnection(Face.U, Edge.BOTTOM),
                Edge.BOTTOM: EdgeConnection(Face.D, Edge.TOP),
            },
            # ... define for all faces
        }
        
        walker = CubeRotationWalker(n=4, edge_map=edge_map)
        results = walker.calculate_rotation(
            starting_face=Face.F,
            rotate_with=Face.R,
            si=0
        )
    """
    
    # =========================================================================
    # TABLE 1: Crossing Transformations (16 cases)
    # When crossing from one face to another
    # Key: (exit_edge, enter_edge)
    # Value: (new_row_formula, new_col_formula, new_direction)
    # =========================================================================
    TABLE1_CROSSING = {
        (Edge.RIGHT, Edge.LEFT):   ('P', '0', Direction.LEFT_TO_RIGHT),
        (Edge.RIGHT, Edge.RIGHT):  ('P', 'N-1', Direction.RIGHT_TO_LEFT),
        (Edge.RIGHT, Edge.BOTTOM): ('0', 'P', Direction.BOTTOM_TO_TOP),
        (Edge.RIGHT, Edge.TOP):    ('N-1', 'P', Direction.TOP_TO_BOTTOM),
        
        (Edge.LEFT, Edge.RIGHT):   ('P', 'N-1', Direction.RIGHT_TO_LEFT),
        (Edge.LEFT, Edge.LEFT):    ('P', '0', Direction.LEFT_TO_RIGHT),
        (Edge.LEFT, Edge.BOTTOM):  ('0', 'P', Direction.BOTTOM_TO_TOP),
        (Edge.LEFT, Edge.TOP):     ('N-1', 'P', Direction.TOP_TO_BOTTOM),
        
        (Edge.TOP, Edge.BOTTOM):   ('0', 'P', Direction.BOTTOM_TO_TOP),
        (Edge.TOP, Edge.TOP):      ('N-1', 'P', Direction.TOP_TO_BOTTOM),
        (Edge.TOP, Edge.LEFT):     ('P', '0', Direction.LEFT_TO_RIGHT),
        (Edge.TOP, Edge.RIGHT):    ('P', 'N-1', Direction.RIGHT_TO_LEFT),
        
        (Edge.BOTTOM, Edge.TOP):    ('N-1', 'P', Direction.TOP_TO_BOTTOM),
        (Edge.BOTTOM, Edge.BOTTOM): ('0', 'P', Direction.BOTTOM_TO_TOP),
        (Edge.BOTTOM, Edge.LEFT):   ('P', '0', Direction.LEFT_TO_RIGHT),
        (Edge.BOTTOM, Edge.RIGHT):  ('P', 'N-1', Direction.RIGHT_TO_LEFT),
    }
    
    # =========================================================================
    # TABLE 2: Starting Face (16 cases)
    # When determining starting direction based on rotation
    # Key: (my_edge, rotating_edge)
    # Value: (direction, start_row_formula, start_col_formula, exit_edge)
    # =========================================================================
    TABLE2_STARTING = {
        (Edge.RIGHT, Edge.LEFT):   (Direction.BOTTOM_TO_TOP, '0', '(N-1)-SI', Edge.TOP),
        (Edge.RIGHT, Edge.RIGHT):  (Direction.TOP_TO_BOTTOM, 'N-1', '(N-1)-SI', Edge.BOTTOM),
        (Edge.RIGHT, Edge.TOP):    (Direction.TOP_TO_BOTTOM, 'N-1', '(N-1)-SI', Edge.BOTTOM),
        (Edge.RIGHT, Edge.BOTTOM): (Direction.BOTTOM_TO_TOP, '0', '(N-1)-SI', Edge.TOP),
        
        (Edge.LEFT, Edge.LEFT):    (Direction.BOTTOM_TO_TOP, '0', 'SI', Edge.TOP),
        (Edge.LEFT, Edge.RIGHT):   (Direction.TOP_TO_BOTTOM, 'N-1', 'SI', Edge.BOTTOM),
        (Edge.LEFT, Edge.TOP):     (Direction.TOP_TO_BOTTOM, 'N-1', 'SI', Edge.BOTTOM),
        (Edge.LEFT, Edge.BOTTOM):  (Direction.BOTTOM_TO_TOP, '0', 'SI', Edge.TOP),
        
        (Edge.TOP, Edge.LEFT):     (Direction.LEFT_TO_RIGHT, '(N-1)-SI', '0', Edge.RIGHT),
        (Edge.TOP, Edge.RIGHT):    (Direction.RIGHT_TO_LEFT, '(N-1)-SI', 'N-1', Edge.LEFT),
        (Edge.TOP, Edge.TOP):      (Direction.LEFT_TO_RIGHT, '(N-1)-SI', '0', Edge.RIGHT),
        (Edge.TOP, Edge.BOTTOM):   (Direction.RIGHT_TO_LEFT, '(N-1)-SI', 'N-1', Edge.LEFT),
        
        (Edge.BOTTOM, Edge.LEFT):   (Direction.RIGHT_TO_LEFT, 'SI', 'N-1', Edge.LEFT),
        (Edge.BOTTOM, Edge.RIGHT):  (Direction.LEFT_TO_RIGHT, 'SI', '0', Edge.RIGHT),
        (Edge.BOTTOM, Edge.TOP):    (Direction.RIGHT_TO_LEFT, 'SI', 'N-1', Edge.LEFT),
        (Edge.BOTTOM, Edge.BOTTOM): (Direction.LEFT_TO_RIGHT, 'SI', '0', Edge.RIGHT),
    }
    
    # =========================================================================
    # Rotation paths: which 4 faces surround each rotating face
    # =========================================================================
    ROTATION_PATHS = {
        Face.R: [Face.F, Face.U, Face.B, Face.D],
        Face.L: [Face.F, Face.D, Face.B, Face.U],
        Face.U: [Face.F, Face.R, Face.B, Face.L],
        Face.D: [Face.F, Face.L, Face.B, Face.R],
        Face.F: [Face.U, Face.R, Face.D, Face.L],
        Face.B: [Face.U, Face.L, Face.D, Face.R],
    }
    
    def __init__(self, n: int, edge_map: Dict[Face, Dict[Edge, EdgeConnection]]):
        """
        Initialize the cube rotation walker.
        
        Args:
            n: Grid size (N×N on each face)
            edge_map: Dictionary mapping each face's edges to their connections
        """
        if n < 1:
            raise ValueError("N must be at least 1")
        self.n = n
        self.edge_map = edge_map
    
    def _apply_formula(self, formula: str, p: int, si: int) -> int:
        """Apply a formula to get a coordinate value."""
        if formula == 'P':
            return p
        elif formula == '0':
            return 0
        elif formula == 'N-1':
            return self.n - 1
        elif formula == 'SI':
            return si
        elif formula == '(N-1)-SI':
            return (self.n - 1) - si
        else:
            raise ValueError(f"Unknown formula: {formula}")
    
    def _get_visit_sequence(self, row: int, col: int, direction: Direction) -> List[Tuple[int, int]]:
        """Get the sequence of cells visited when walking across a face."""
        cells = []
        
        if direction == Direction.LEFT_TO_RIGHT:
            for c in range(self.n):
                cells.append((row, c))
        elif direction == Direction.RIGHT_TO_LEFT:
            for c in range(self.n - 1, -1, -1):
                cells.append((row, c))
        elif direction == Direction.BOTTOM_TO_TOP:
            for r in range(self.n):
                cells.append((r, col))
        elif direction == Direction.TOP_TO_BOTTOM:
            for r in range(self.n - 1, -1, -1):
                cells.append((r, col))
        
        return cells
    
    def _get_p_value(self, row: int, col: int, direction: Direction) -> int:
        """Get the P value (position along exit edge)."""
        if direction in (Direction.LEFT_TO_RIGHT, Direction.RIGHT_TO_LEFT):
            return row
        else:
            return col
    
    def _get_exit_edge(self, direction: Direction) -> Edge:
        """Get the exit edge based on walking direction."""
        exit_edges = {
            Direction.LEFT_TO_RIGHT: Edge.RIGHT,
            Direction.RIGHT_TO_LEFT: Edge.LEFT,
            Direction.BOTTOM_TO_TOP: Edge.TOP,
            Direction.TOP_TO_BOTTOM: Edge.BOTTOM,
        }
        return exit_edges[direction]
    
    def _find_connecting_edge(self, from_face: Face, to_face: Face) -> Tuple[Edge, Edge]:
        """Find which edges connect two faces."""
        for edge, connection in self.edge_map[from_face].items():
            if connection.face == to_face:
                return edge, connection.edge
        raise ValueError(f"No connection found between {from_face.value} and {to_face.value}")
    
    def _get_starting_info(self, my_edge: Edge, rotating_edge: Edge, si: int) -> Tuple[Direction, int, int, Edge]:
        """
        Get starting direction, point, and exit edge using Table 2.
        
        Returns:
            Tuple of (direction, start_row, start_col, exit_edge)
        """
        key = (my_edge, rotating_edge)
        if key not in self.TABLE2_STARTING:
            raise ValueError(f"Invalid edge combination: {my_edge.value} → {rotating_edge.value}")
        
        direction, row_formula, col_formula, exit_edge = self.TABLE2_STARTING[key]
        
        start_row = self._apply_formula(row_formula, 0, si)
        start_col = self._apply_formula(col_formula, 0, si)
        
        return direction, start_row, start_col, exit_edge
    
    def _cross_to_next_face(self, exit_edge: Edge, enter_edge: Edge, p: int) -> Tuple[int, int, Direction]:
        """
        Calculate new position and direction when crossing to next face using Table 1.
        
        Returns:
            Tuple of (new_row, new_col, new_direction)
        """
        key = (exit_edge, enter_edge)
        if key not in self.TABLE1_CROSSING:
            raise ValueError(f"Invalid crossing: {exit_edge.value} → {enter_edge.value}")
        
        row_formula, col_formula, new_direction = self.TABLE1_CROSSING[key]
        
        new_row = self._apply_formula(row_formula, p, 0)
        new_col = self._apply_formula(col_formula, p, 0)
        
        return new_row, new_col, new_direction
    
    def calculate_rotation(self, starting_face: Face, rotate_with: Face, si: int) -> List[FaceResult]:
        """
        Calculate all coordinates visited during a slice rotation.
        
        Args:
            starting_face: Which face to start on
            rotate_with: Which face to rotate with
            si: Slice index (0 = closest to rotating face)
        
        Returns:
            List of FaceResult objects for each face in the rotation path
        """
        # Validate inputs
        if si < 0 or si >= self.n:
            raise ValueError(f"SI must be between 0 and {self.n - 1}")
        
        # Get the rotation path
        path = self.ROTATION_PATHS[rotate_with]
        if starting_face not in path:
            raise ValueError(f"Face {starting_face.value} is not in the rotation path for {rotate_with.value}")
        
        # Rotate path to start from starting_face
        start_idx = path.index(starting_face)
        path = path[start_idx:] + path[:start_idx]
        
        results = []
        
        # Step 1: Get starting info from Table 2
        my_edge, rotating_edge = self._find_connecting_edge(starting_face, rotate_with)
        direction, row, col, _ = self._get_starting_info(my_edge, rotating_edge, si)
        
        # Process each face in the path
        for i, current_face in enumerate(path):
            # Determine enter point based on direction
            if direction == Direction.LEFT_TO_RIGHT:
                enter_point = (row, 0)
            elif direction == Direction.RIGHT_TO_LEFT:
                enter_point = (row, self.n - 1)
            elif direction == Direction.BOTTOM_TO_TOP:
                enter_point = (0, col)
            elif direction == Direction.TOP_TO_BOTTOM:
                enter_point = (self.n - 1, col)
            
            # Get visited cells
            visited = self._get_visit_sequence(row, col, direction)
            
            # Get exit edge and P value
            exit_edge = self._get_exit_edge(direction)
            p = self._get_p_value(row, col, direction)
            
            # Store result
            results.append(FaceResult(
                face=current_face,
                enter_point=enter_point,
                direction=direction,
                visited_cells=visited,
                exit_edge=exit_edge,
                p_value=p
            ))
            
            # Cross to next face (if not the last face)
            if i < len(path) - 1:
                next_face = path[i + 1]
                _, enter_edge = self._find_connecting_edge(current_face, next_face)
                row, col, direction = self._cross_to_next_face(exit_edge, enter_edge, p)
        
        return results


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_standard_edge_map() -> Dict[Face, Dict[Edge, EdgeConnection]]:
    """
    Create a standard Rubik's cube edge connection map.
    
    This is one possible configuration. Adjust as needed for your cube orientation.
    """
    return {
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
        Face.B: {
            Edge.RIGHT: EdgeConnection(Face.L, Edge.LEFT),
            Edge.LEFT: EdgeConnection(Face.R, Edge.RIGHT),
            Edge.TOP: EdgeConnection(Face.U, Edge.TOP),
            Edge.BOTTOM: EdgeConnection(Face.D, Edge.BOTTOM),
        },
        Face.L: {
            Edge.RIGHT: EdgeConnection(Face.F, Edge.LEFT),
            Edge.LEFT: EdgeConnection(Face.B, Edge.RIGHT),
            Edge.TOP: EdgeConnection(Face.U, Edge.LEFT),
            Edge.BOTTOM: EdgeConnection(Face.D, Edge.LEFT),
        },
        Face.U: {
            Edge.RIGHT: EdgeConnection(Face.R, Edge.TOP),
            Edge.LEFT: EdgeConnection(Face.L, Edge.TOP),
            Edge.TOP: EdgeConnection(Face.B, Edge.TOP),
            Edge.BOTTOM: EdgeConnection(Face.F, Edge.TOP),
        },
        Face.D: {
            Edge.RIGHT: EdgeConnection(Face.R, Edge.BOTTOM),
            Edge.LEFT: EdgeConnection(Face.L, Edge.BOTTOM),
            Edge.TOP: EdgeConnection(Face.F, Edge.BOTTOM),
            Edge.BOTTOM: EdgeConnection(Face.B, Edge.BOTTOM),
        },
    }


def print_face_grid(n: int, visited_cells: List[Tuple[int, int]], direction: Direction, face_name: str):
    """Print a visual representation of a face with visited cells marked."""
    # Create empty grid
    grid = [['  .   ' for _ in range(n)] for _ in range(n)]
    
    # Direction arrows
    arrows = {
        Direction.LEFT_TO_RIGHT: '→',
        Direction.RIGHT_TO_LEFT: '←',
        Direction.BOTTOM_TO_TOP: '↑',
        Direction.TOP_TO_BOTTOM: '↓',
    }
    arrow = arrows[direction]
    
    # Mark visited cells
    for r, c in visited_cells:
        grid[r][c] = f'({r},{c}){arrow}'
    
    # Print
    print(f"\n    Face {face_name}:")
    print("        " + "".join(f"   {c}   " for c in range(n)))
    print("       +" + "-------+" * n)
    for r in range(n - 1, -1, -1):
        row_str = " | ".join(f"{grid[r][c]:^5}" for c in range(n))
        print(f"   {r}   | {row_str} |")
        print("       +" + "-------+" * n)


def print_results(results: List[FaceResult], n: int):
    """Print detailed results of a cube rotation."""
    print("\n" + "=" * 70)
    print("ROTATION RESULTS")
    print("=" * 70)
    
    for result in results:
        print(f"\nFace {result.face.value}:")
        print(f"  Enter point: {result.enter_point}")
        print(f"  Direction: {result.direction.value}")
        print(f"  Visited: {result.visited_cells}")
        print(f"  Exit edge: {result.exit_edge.value}")
        print(f"  P value: {result.p_value}")
        
        print_face_grid(n, result.visited_cells, result.direction, result.face.value)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nPath: {' → '.join(r.face.value for r in results)} → {results[0].face.value}")
    print(f"\nAll visited cells:")
    for result in results:
        print(f"  Face {result.face.value}: {result.visited_cells}")
    
    total_cells = sum(len(r.visited_cells) for r in results)
    print(f"\nTotal cells visited: {total_cells}")


# =============================================================================
# EXAMPLES
# =============================================================================

def example_1_basic():
    """Example 1: Basic rotation with R, SI=0"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Rotate with R, SI=0")
    print("=" * 70)
    
    print("\nINPUT:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = R")
    print("  SI = 0 (closest to R)")
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R,
        si=0
    )
    
    print_results(results, n=4)


def example_2_different_si():
    """Example 2: Rotation with R, SI=2"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Rotate with R, SI=2")
    print("=" * 70)
    
    print("\nINPUT:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = R")
    print("  SI = 2 (farther from R)")
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R,
        si=2
    )
    
    print_results(results, n=4)


def example_3_rotate_with_u():
    """Example 3: Rotation with U, SI=0"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Rotate with U, SI=0")
    print("=" * 70)
    
    print("\nINPUT:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = U")
    print("  SI = 0 (closest to U)")
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.U,
        si=0
    )
    
    print_results(results, n=4)


def example_4_rotate_with_l():
    """Example 4: Rotation with L, SI=1"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Rotate with L, SI=1")
    print("=" * 70)
    
    print("\nINPUT:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = L")
    print("  SI = 1")
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.L,
        si=1
    )
    
    print_results(results, n=4)


def example_5_custom():
    """Example 5: Interactive custom rotation"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Custom Rotation")
    print("=" * 70)
    
    print("\nYou can use the CubeRotationWalker like this:")
    print("""
    from cube_rotation_walker import (
        CubeRotationWalker, Face, create_standard_edge_map
    )
    
    # Create edge map (or use standard one)
    edge_map = create_standard_edge_map()
    
    # Create walker
    walker = CubeRotationWalker(n=4, edge_map=edge_map)
    
    # Calculate rotation
    results = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R,
        si=0
    )
    
    # Print results
    for result in results:
        print(f"Face {result.face.value}: {result.visited_cells}")
    """)


def print_tables():
    """Print both transformation tables"""
    print("\n" + "=" * 70)
    print("TABLE 1: CROSSING TRANSFORMATIONS")
    print("=" * 70)
    print(f"\n{'#':<3} {'Exit Edge':<10} {'Enter Edge':<11} {'new_row':<8} {'new_col':<8} {'New Direction':<15}")
    print("-" * 60)
    
    for i, ((exit_e, enter_e), (row_f, col_f, direction)) in enumerate(CubeRotationWalker.TABLE1_CROSSING.items(), 1):
        print(f"{i:<3} {exit_e.value:<10} {enter_e.value:<11} {row_f:<8} {col_f:<8} {direction.value:<15}")
    
    print("\n" + "=" * 70)
    print("TABLE 2: STARTING FACE")
    print("=" * 70)
    print(f"\n{'#':<3} {'My Edge':<10} {'Rot Edge':<10} {'Direction':<14} {'Start Row':<12} {'Start Col':<12} {'Exit Edge':<10}")
    print("-" * 80)
    
    for i, ((my_e, rot_e), (direction, row_f, col_f, exit_e)) in enumerate(CubeRotationWalker.TABLE2_STARTING.items(), 1):
        print(f"{i:<3} {my_e.value:<10} {rot_e.value:<10} {direction.value:<14} {row_f:<12} {col_f:<12} {exit_e.value:<10}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Print tables
    print_tables()
    
    # Run examples
    example_1_basic()
    example_2_different_si()
    example_3_rotate_with_u()
    example_4_rotate_with_l()
    example_5_custom()
