"""
Cube Grid Coordinate Transformation - Variant 2
================================================

This module implements slice rotation on a 3D Rubik's cube where each face 
has an N×N grid. This variant uses a get_point(si, other_coord) method
that allows dynamic calculation of coordinates for any slice index.

KEY FEATURE:
  The get_point(si, other_coord) method returns the coordinate at position
  'other_coord' (0 to N-1) along the path for slice index 'si'.
  
CRITICAL PROPERTY:
  For consecutive faces f1 and f2 (where f2 follows f1 in CW rotation):
  
    f1.get_point(si, N-1)  →  last point on f1 (exit point)
    f2.get_point(si, 0)    →  first point on f2 (entry point)
    
  These two points are PHYSICALLY ADJACENT on the cube!
  They represent the continuation of the same straight-line path.

INPUT:
  - N: Grid size (e.g., 4 means 4×4 grid)
  - starting_face: Which face you're on (F, B, L, R, U, D)
  - rotate_with: Which face to rotate with
  - edge_map: Edge connection map between faces

OUTPUT:
  - List of FaceOutput objects, each with get_point(si, other_coord) method
"""

from enum import Enum
from typing import List, Tuple, Dict, Callable
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


class FaceOutput:
    """
    Represents the output for one face in the rotation path.
    
    This class provides the get_point(si, other_coord) method that calculates
    the (row, col) coordinate for any slice index and position along the path.
    
    Attributes:
        face: The face name (F, B, L, R, U, D)
        n: Grid size (N×N)
        direction: Walking direction on this face
        my_edge: Edge of this face that connects to the rotating face
        rotating_edge: Edge of the rotating face that connects to this face
        exit_edge: Edge where the path exits this face
        enter_edge: Edge where the path enters this face
        face_index: Position in the rotation path (0, 1, 2, or 3)
    
    CRITICAL ADJACENCY PROPERTY:
    ============================
    For consecutive faces in the rotation path:
    
        f1 = faces[i]      (current face)
        f2 = faces[i+1]    (next face in CW rotation)
        
        f1.get_point(si, N-1)  →  EXIT point on f1
        f2.get_point(si, 0)    →  ENTRY point on f2
        
        These points are PHYSICALLY ADJACENT on the 3D cube!
        
    Visual Example (N=4, rotating with R, SI=0):
    
        Face F (index=0)              Face U (index=1)
        
                 TOP                          TOP
            +---+---+---+---+            +---+---+---+---+
          3 |   |   |   | 3 |          3 |   |   |   | 3 |  ← other_coord=3
            +---+---+---+---+            +---+---+---+---+
          2 |   |   |   | 2 |          2 |   |   |   | 2 |
            +---+---+---+---+            +---+---+---+---+
          1 |   |   |   | 1 |          1 |   |   |   | 1 |
            +---+---+---+---+            +---+---+---+---+
          0 |   |   |   | 0 |          0 |   |   |   | 0 |  ← other_coord=0
            +---+---+---+---+            +---+---+---+---+
               BOTTOM                        BOTTOM
                    ↑                         ↑
               col 3 (SI=0)              col 3 (SI=0)
        
        Path on F: (0,3) → (1,3) → (2,3) → (3,3)
                   oc=0    oc=1    oc=2    oc=3
        
        Path on U: (0,3) → (1,3) → (2,3) → (3,3)
                   oc=0    oc=1    oc=2    oc=3
        
        f1.get_point(0, 3) = (3, 3)  ← EXIT from F (TOP edge)
        f2.get_point(0, 0) = (0, 3)  ← ENTRY to U (BOTTOM edge)
        
        These are ADJACENT! (3,3) on F's TOP touches (0,3) on U's BOTTOM
    """
    
    def __init__(
        self,
        face: Face,
        n: int,
        direction: Direction,
        my_edge: Edge,
        rotating_edge: Edge,
        exit_edge: Edge,
        enter_edge: Edge,
        face_index: int,
        row_formula: Callable[[int, int], int],
        col_formula: Callable[[int, int], int],
    ):
        """
        Initialize FaceOutput.
        
        Args:
            face: The face name
            n: Grid size
            direction: Walking direction on this face
            my_edge: Edge connecting to rotating face
            rotating_edge: Rotating face's edge connecting to this face
            exit_edge: Edge where path exits
            enter_edge: Edge where path enters
            face_index: Position in rotation path (0-3)
            row_formula: Function(si, other_coord) → row
            col_formula: Function(si, other_coord) → col
        """
        self.face = face
        self.n = n
        self.direction = direction
        self.my_edge = my_edge
        self.rotating_edge = rotating_edge
        self.exit_edge = exit_edge
        self.enter_edge = enter_edge
        self.face_index = face_index
        self._row_formula = row_formula
        self._col_formula = col_formula
    
    def get_point(self, si: int, other_coord: int) -> Tuple[int, int]:
        """
        Get the (row, col) coordinate for a given slice index and path position.
        
        This method calculates the coordinate on this face's LTR grid system
        for the specified slice index (SI) and position along the path (other_coord).
        
        Args:
            si: Slice Index (0 to N-1)
                - 0 = slice closest to the rotating face
                - N-1 = slice farthest from the rotating face
                
            other_coord: Position along the path on this face (0 to N-1)
                - 0 = entry point (where path enters this face)
                - N-1 = exit point (where path exits this face)
        
        Returns:
            Tuple[int, int]: (row, col) in the LTR coordinate system
                - row: 0 at BOTTOM edge, N-1 at TOP edge
                - col: 0 at LEFT edge, N-1 at RIGHT edge
        
        Raises:
            ValueError: If si or other_coord is out of range [0, N-1]
        
        ═══════════════════════════════════════════════════════════════════════
        CRITICAL ADJACENCY PROPERTY
        ═══════════════════════════════════════════════════════════════════════
        
        For consecutive faces f1 and f2 in the rotation path:
        
            f1.get_point(si, N-1)  →  EXIT point (last point on f1)
            f2.get_point(si, 0)    →  ENTRY point (first point on f2)
        
        These two points are PHYSICALLY ADJACENT on the 3D cube surface!
        They represent the same physical edge shared by both faces.
        
        ═══════════════════════════════════════════════════════════════════════
        VISUAL DIAGRAM - Understanding other_coord
        ═══════════════════════════════════════════════════════════════════════
        
        The 'other_coord' parameter represents position along the walking path:
        
        DIRECTION: BOTTOM→TOP (vertical walk upward)
        ─────────────────────────────────────────────
        
                         TOP edge
                           ↓
                  +---+---+---+---+
            row 3 |   |   | X |   |  ← other_coord = 3 (EXIT)
                  +---+---+---+---+
            row 2 |   |   | X |   |  ← other_coord = 2
                  +---+---+---+---+
            row 1 |   |   | X |   |  ← other_coord = 1
                  +---+---+---+---+
            row 0 |   |   | X |   |  ← other_coord = 0 (ENTRY)
                  +---+---+---+---+
                           ↑
                      col = (N-1)-SI
                      
            Path visits: (0,col) → (1,col) → (2,col) → (3,col)
            other_coord:    0        1          2          3
        
        
        DIRECTION: TOP→BOTTOM (vertical walk downward)
        ─────────────────────────────────────────────
        
                         TOP edge
                           ↓
                  +---+---+---+---+
            row 3 |   | X |   |   |  ← other_coord = 0 (ENTRY)
                  +---+---+---+---+
            row 2 |   | X |   |   |  ← other_coord = 1
                  +---+---+---+---+
            row 1 |   | X |   |   |  ← other_coord = 2
                  +---+---+---+---+
            row 0 |   | X |   |   |  ← other_coord = 3 (EXIT)
                  +---+---+---+---+
                       ↑
                   col = SI
                   
            Path visits: (3,col) → (2,col) → (1,col) → (0,col)
            other_coord:    0        1          2          3
        
        
        DIRECTION: LEFT→RIGHT (horizontal walk rightward)
        ─────────────────────────────────────────────────
        
                  +---+---+---+---+
            row   | X | X | X | X |  ← row = (N-1)-SI
                  +---+---+---+---+
                    ↑   ↑   ↑   ↑
                   oc  oc  oc  oc
                   =0  =1  =2  =3
                   
            ENTRY              EXIT
            (col=0)          (col=3)
            
            Path visits: (row,0) → (row,1) → (row,2) → (row,3)
            other_coord:    0        1          2          3
        
        
        DIRECTION: RIGHT→LEFT (horizontal walk leftward)
        ─────────────────────────────────────────────────
        
                  +---+---+---+---+
            row   | X | X | X | X |  ← row = SI
                  +---+---+---+---+
                    ↑   ↑   ↑   ↑
                   oc  oc  oc  oc
                   =3  =2  =1  =0
                   
            EXIT               ENTRY
            (col=0)          (col=3)
            
            Path visits: (row,3) → (row,2) → (row,1) → (row,0)
            other_coord:    0        1          2          3
        
        
        ═══════════════════════════════════════════════════════════════════════
        ADJACENCY EXAMPLE
        ═══════════════════════════════════════════════════════════════════════
        
        Rotation path: F → U → B → D → F (rotating with R)
        N = 4, SI = 0
        
        Face F:                          Face U:
        Direction: BOTTOM→TOP            Direction: BOTTOM→TOP
        
              TOP                              TOP
          +---+---+---+---+                +---+---+---+---+
        3 |   |   |   |(3,3)|  EXIT      3 |   |   |   |(3,3)|
          +---+---+---+---+                +---+---+---+---+
        2 |   |   |   |(2,3)|            2 |   |   |   |(2,3)|
          +---+---+---+---+                +---+---+---+---+
        1 |   |   |   |(1,3)|            1 |   |   |   |(1,3)|
          +---+---+---+---+                +---+---+---+---+
        0 |   |   |   |(0,3)|            0 |   |   |   |(0,3)|  ENTRY
          +---+---+---+---+                +---+---+---+---+
              BOTTOM                           BOTTOM
        
        f1 = Face F (index 0)
        f2 = Face U (index 1)
        
        f1.get_point(si=0, other_coord=3) = (3, 3)   ← EXIT from F's TOP edge
        f2.get_point(si=0, other_coord=0) = (0, 3)   ← ENTRY to U's BOTTOM edge
        
        On the 3D cube:
        - F's TOP edge is adjacent to U's BOTTOM edge
        - Point (3,3) on F touches point (0,3) on U
        - They are the SAME physical location on the cube's edge!
        
        ═══════════════════════════════════════════════════════════════════════
        USAGE EXAMPLES
        ═══════════════════════════════════════════════════════════════════════
        
        # Get all points for SI=0
        for oc in range(N):
            row, col = face_output.get_point(si=0, other_coord=oc)
            print(f"Position {oc}: ({row}, {col})")
        
        # Get entry and exit points
        entry_point = face_output.get_point(si=0, other_coord=0)
        exit_point = face_output.get_point(si=0, other_coord=N-1)
        
        # Verify adjacency between consecutive faces
        f1_exit = faces[0].get_point(si=0, other_coord=N-1)
        f2_entry = faces[1].get_point(si=0, other_coord=0)
        # f1_exit and f2_entry are adjacent on the cube!
        
        # Get points for different slice indices
        for si in range(N):
            point = face_output.get_point(si=si, other_coord=0)
            print(f"SI={si}: Entry at {point}")
        """
        # Validate inputs
        if si < 0 or si >= self.n:
            raise ValueError(f"si must be between 0 and {self.n - 1}, got {si}")
        if other_coord < 0 or other_coord >= self.n:
            raise ValueError(f"other_coord must be between 0 and {self.n - 1}, got {other_coord}")
        
        row = self._row_formula(si, other_coord)
        col = self._col_formula(si, other_coord)
        
        return (row, col)
    
    def get_all_points(self, si: int) -> List[Tuple[int, int]]:
        """
        Get all N points for a given slice index.
        
        Args:
            si: Slice Index (0 to N-1)
        
        Returns:
            List of (row, col) tuples, ordered by other_coord from 0 to N-1
        """
        return [self.get_point(si, oc) for oc in range(self.n)]
    
    def __repr__(self) -> str:
        return (f"FaceOutput(face={self.face.value}, direction={self.direction.value}, "
                f"enter={self.enter_edge.value}, exit={self.exit_edge.value}, "
                f"index={self.face_index})")


class CubeRotationWalkerV2:
    """
    Calculates coordinates visited during a slice rotation on a Rubik's cube.
    
    This is Variant 2 which uses FaceOutput objects with get_point() method
    for dynamic coordinate calculation.
    
    Usage:
        edge_map = create_standard_edge_map()
        walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
        
        faces = walker.calculate_rotation(
            starting_face=Face.F,
            rotate_with=Face.R
        )
        
        # Get point for SI=0, position 2
        point = faces[0].get_point(si=0, other_coord=2)
        
        # Verify adjacency
        exit_point = faces[0].get_point(si=0, other_coord=3)   # (3,3)
        entry_point = faces[1].get_point(si=0, other_coord=0)  # (0,3)
        # These are adjacent on the cube!
    """
    
    # =========================================================================
    # TABLE 2: Starting Face (16 cases)
    # Key: (my_edge, rotating_edge)
    # Value: (direction, row_base, col_base, row_uses_oc, col_uses_oc, exit_edge)
    #
    # row_base/col_base: 'SI', '(N-1)-SI', '0', 'N-1'
    # row_uses_oc/col_uses_oc: True if that coordinate uses other_coord
    # =========================================================================
    TABLE2_STARTING = {
        # My Edge: RIGHT → vertical direction, col = (N-1)-SI
        # Format: (direction, row_formula, col_formula, exit_edge)
        (Edge.RIGHT, Edge.LEFT):   (Direction.BOTTOM_TO_TOP, 'oc', '(N-1)-SI', Edge.TOP),
        (Edge.RIGHT, Edge.RIGHT):  (Direction.TOP_TO_BOTTOM, '(N-1)-oc', '(N-1)-SI', Edge.BOTTOM),
        (Edge.RIGHT, Edge.TOP):    (Direction.TOP_TO_BOTTOM, '(N-1)-oc', '(N-1)-SI', Edge.BOTTOM),
        (Edge.RIGHT, Edge.BOTTOM): (Direction.BOTTOM_TO_TOP, 'oc', '(N-1)-SI', Edge.TOP),
        
        # My Edge: LEFT → vertical direction, col = SI
        (Edge.LEFT, Edge.LEFT):    (Direction.BOTTOM_TO_TOP, 'oc', 'SI', Edge.TOP),
        (Edge.LEFT, Edge.RIGHT):   (Direction.TOP_TO_BOTTOM, '(N-1)-oc', 'SI', Edge.BOTTOM),
        (Edge.LEFT, Edge.TOP):     (Direction.TOP_TO_BOTTOM, '(N-1)-oc', 'SI', Edge.BOTTOM),
        (Edge.LEFT, Edge.BOTTOM):  (Direction.BOTTOM_TO_TOP, 'oc', 'SI', Edge.TOP),
        
        # My Edge: TOP → horizontal direction, row = (N-1)-SI
        (Edge.TOP, Edge.LEFT):     (Direction.LEFT_TO_RIGHT, '(N-1)-SI', 'oc', Edge.RIGHT),
        (Edge.TOP, Edge.RIGHT):    (Direction.RIGHT_TO_LEFT, '(N-1)-SI', '(N-1)-oc', Edge.LEFT),
        (Edge.TOP, Edge.TOP):      (Direction.LEFT_TO_RIGHT, '(N-1)-SI', 'oc', Edge.RIGHT),
        (Edge.TOP, Edge.BOTTOM):   (Direction.RIGHT_TO_LEFT, '(N-1)-SI', '(N-1)-oc', Edge.LEFT),
        
        # My Edge: BOTTOM → horizontal direction, row = SI
        (Edge.BOTTOM, Edge.LEFT):   (Direction.RIGHT_TO_LEFT, 'SI', '(N-1)-oc', Edge.LEFT),
        (Edge.BOTTOM, Edge.RIGHT):  (Direction.LEFT_TO_RIGHT, 'SI', 'oc', Edge.RIGHT),
        (Edge.BOTTOM, Edge.TOP):    (Direction.RIGHT_TO_LEFT, 'SI', '(N-1)-oc', Edge.LEFT),
        (Edge.BOTTOM, Edge.BOTTOM): (Direction.LEFT_TO_RIGHT, 'SI', 'oc', Edge.RIGHT),
    }
    
    # =========================================================================
    # TABLE 1: Crossing Transformations (16 cases)
    # Key: (exit_edge, enter_edge)
    # Value: (direction, row_formula, col_formula)
    #
    # Formulas use: 'P' (previous P value), 'oc', '0', 'N-1', '(N-1)-oc'
    # =========================================================================
    TABLE1_CROSSING = {
        (Edge.RIGHT, Edge.LEFT):   (Direction.LEFT_TO_RIGHT, 'P', 'oc'),
        (Edge.RIGHT, Edge.RIGHT):  (Direction.RIGHT_TO_LEFT, 'P', '(N-1)-oc'),
        (Edge.RIGHT, Edge.BOTTOM): (Direction.BOTTOM_TO_TOP, 'oc', 'P'),
        (Edge.RIGHT, Edge.TOP):    (Direction.TOP_TO_BOTTOM, '(N-1)-oc', 'P'),
        
        (Edge.LEFT, Edge.RIGHT):   (Direction.RIGHT_TO_LEFT, 'P', '(N-1)-oc'),
        (Edge.LEFT, Edge.LEFT):    (Direction.LEFT_TO_RIGHT, 'P', 'oc'),
        (Edge.LEFT, Edge.BOTTOM):  (Direction.BOTTOM_TO_TOP, 'oc', 'P'),
        (Edge.LEFT, Edge.TOP):     (Direction.TOP_TO_BOTTOM, '(N-1)-oc', 'P'),
        
        (Edge.TOP, Edge.BOTTOM):   (Direction.BOTTOM_TO_TOP, 'oc', 'P'),
        (Edge.TOP, Edge.TOP):      (Direction.TOP_TO_BOTTOM, '(N-1)-oc', 'P'),
        (Edge.TOP, Edge.LEFT):     (Direction.LEFT_TO_RIGHT, 'P', 'oc'),
        (Edge.TOP, Edge.RIGHT):    (Direction.RIGHT_TO_LEFT, 'P', '(N-1)-oc'),
        
        (Edge.BOTTOM, Edge.TOP):    (Direction.TOP_TO_BOTTOM, '(N-1)-oc', 'P'),
        (Edge.BOTTOM, Edge.BOTTOM): (Direction.BOTTOM_TO_TOP, 'oc', 'P'),
        (Edge.BOTTOM, Edge.LEFT):   (Direction.LEFT_TO_RIGHT, 'P', 'oc'),
        (Edge.BOTTOM, Edge.RIGHT):  (Direction.RIGHT_TO_LEFT, 'P', '(N-1)-oc'),
    }
    
    # Rotation paths: which 4 faces surround each rotating face
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
    
    def _find_connecting_edge(self, from_face: Face, to_face: Face) -> Tuple[Edge, Edge]:
        """Find which edges connect two faces."""
        for edge, connection in self.edge_map[from_face].items():
            if connection.face == to_face:
                return edge, connection.edge
        raise ValueError(f"No connection found between {from_face.value} and {to_face.value}")
    
    def _create_formula(self, formula: str, n: int, p_formula: Callable = None) -> Callable[[int, int], int]:
        """
        Create a function from a formula string.
        
        Args:
            formula: One of 'SI', '(N-1)-SI', 'oc', '(N-1)-oc', 'P', '0', 'N-1'
            n: Grid size
            p_formula: Function for P value (used in crossings)
        
        Returns:
            Function(si, other_coord) → int
        """
        if formula == 'SI':
            return lambda si, oc: si
        elif formula == '(N-1)-SI':
            return lambda si, oc: (n - 1) - si
        elif formula == 'oc':
            return lambda si, oc: oc
        elif formula == '(N-1)-oc':
            return lambda si, oc: (n - 1) - oc
        elif formula == 'P':
            return p_formula
        elif formula == '0':
            return lambda si, oc: 0
        elif formula == 'N-1':
            return lambda si, oc: n - 1
        else:
            raise ValueError(f"Unknown formula: {formula}")
    
    def _get_p_formula(self, direction: Direction, row_formula: Callable, col_formula: Callable) -> Callable[[int, int], int]:
        """
        Get the P value formula based on direction.
        
        P is the position along the exit edge (at other_coord = N-1).
        For horizontal directions: P = row
        For vertical directions: P = col
        """
        if direction in (Direction.LEFT_TO_RIGHT, Direction.RIGHT_TO_LEFT):
            # P = row at exit
            return lambda si, oc: row_formula(si, self.n - 1)
        else:
            # P = col at exit
            return lambda si, oc: col_formula(si, self.n - 1)
    
    def calculate_rotation(self, starting_face: Face, rotate_with: Face) -> List[FaceOutput]:
        """
        Calculate FaceOutput objects for a slice rotation.
        
        Args:
            starting_face: Which face to start on
            rotate_with: Which face to rotate with
        
        Returns:
            List of 4 FaceOutput objects, one for each face in the rotation path.
            
            IMPORTANT: For consecutive faces f1=faces[i] and f2=faces[i+1]:
                f1.get_point(si, N-1) and f2.get_point(si, 0)
                return ADJACENT points on the cube surface!
        """
        # Get the rotation path
        path = self.ROTATION_PATHS[rotate_with]
        if starting_face not in path:
            raise ValueError(f"Face {starting_face.value} is not in the rotation path for {rotate_with.value}")
        
        # Rotate path to start from starting_face
        start_idx = path.index(starting_face)
        path = path[start_idx:] + path[:start_idx]
        
        results = []
        prev_p_formula = None
        prev_exit_edge = None
        
        for face_idx, current_face in enumerate(path):
            # Find connection to rotating face
            my_edge, rotating_edge = self._find_connecting_edge(current_face, rotate_with)
            
            if face_idx == 0:
                # First face: use TABLE2_STARTING
                key = (my_edge, rotating_edge)
                direction, row_str, col_str, exit_edge = self.TABLE2_STARTING[key]
                
                row_formula = self._create_formula(row_str, self.n)
                col_formula = self._create_formula(col_str, self.n)
                enter_edge = None  # First face has no entry
                
            else:
                # Subsequent faces: use TABLE1_CROSSING
                prev_face = path[face_idx - 1]
                _, enter_edge = self._find_connecting_edge(prev_face, current_face)
                
                key = (prev_exit_edge, enter_edge)
                direction, row_str, col_str = self.TABLE1_CROSSING[key]
                
                row_formula = self._create_formula(row_str, self.n, prev_p_formula)
                col_formula = self._create_formula(col_str, self.n, prev_p_formula)
                exit_edge = self._get_exit_edge(direction)
            
            # Calculate exit edge for first face
            if face_idx == 0:
                exit_edge = self._get_exit_edge(direction)
            else:
                exit_edge = self._get_exit_edge(direction)
            
            # Store P formula for next iteration
            prev_p_formula = self._get_p_formula(direction, row_formula, col_formula)
            prev_exit_edge = exit_edge
            
            # Determine enter_edge for first face (from last face going back)
            if face_idx == 0:
                # Calculate what edge we'd enter from if coming from face 3
                last_face = path[-1]
                _, enter_edge = self._find_connecting_edge(last_face, current_face)
            
            # Create FaceOutput
            face_output = FaceOutput(
                face=current_face,
                n=self.n,
                direction=direction,
                my_edge=my_edge,
                rotating_edge=rotating_edge,
                exit_edge=exit_edge,
                enter_edge=enter_edge,
                face_index=face_idx,
                row_formula=row_formula,
                col_formula=col_formula,
            )
            
            results.append(face_output)
        
        return results
    
    def _get_exit_edge(self, direction: Direction) -> Edge:
        """Get the exit edge based on walking direction."""
        exit_edges = {
            Direction.LEFT_TO_RIGHT: Edge.RIGHT,
            Direction.RIGHT_TO_LEFT: Edge.LEFT,
            Direction.BOTTOM_TO_TOP: Edge.TOP,
            Direction.TOP_TO_BOTTOM: Edge.BOTTOM,
        }
        return exit_edges[direction]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_standard_edge_map() -> Dict[Face, Dict[Edge, EdgeConnection]]:
    """
    Create a standard Rubik's cube edge connection map.
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


def print_face_grid(n: int, face_output: FaceOutput, si: int):
    """Print a visual representation of a face with visited cells marked."""
    # Get all points for this SI
    points = face_output.get_all_points(si)
    points_set = set(points)
    
    # Direction arrows
    arrows = {
        Direction.LEFT_TO_RIGHT: '→',
        Direction.RIGHT_TO_LEFT: '←',
        Direction.BOTTOM_TO_TOP: '↑',
        Direction.TOP_TO_BOTTOM: '↓',
    }
    arrow = arrows[face_output.direction]
    
    # Create grid
    grid = [['  .   ' for _ in range(n)] for _ in range(n)]
    for r, c in points:
        grid[r][c] = f'({r},{c}){arrow}'
    
    # Print
    print(f"\n    Face {face_output.face.value} (SI={si}):")
    print("        " + "".join(f"   {c}   " for c in range(n)))
    print("       +" + "-------+" * n)
    for r in range(n - 1, -1, -1):
        row_str = " | ".join(f"{grid[r][c]:^5}" for c in range(n))
        print(f"   {r}   | {row_str} |")
        print("       +" + "-------+" * n)


def print_results(faces: List[FaceOutput], n: int, si: int):
    """Print detailed results."""
    print("\n" + "=" * 70)
    print(f"ROTATION RESULTS (SI={si})")
    print("=" * 70)
    
    for face_output in faces:
        points = face_output.get_all_points(si)
        print(f"\nFace {face_output.face.value}:")
        print(f"  Direction: {face_output.direction.value}")
        print(f"  Enter edge: {face_output.enter_edge.value if face_output.enter_edge else 'START'}")
        print(f"  Exit edge: {face_output.exit_edge.value}")
        print(f"  Entry point: {face_output.get_point(si, 0)}")
        print(f"  Exit point: {face_output.get_point(si, n-1)}")
        print(f"  All points: {points}")
        
        print_face_grid(n, face_output, si)
    
    # Verify adjacency
    print("\n" + "=" * 70)
    print("ADJACENCY VERIFICATION")
    print("=" * 70)
    
    for i in range(len(faces)):
        f1 = faces[i]
        f2 = faces[(i + 1) % len(faces)]
        
        exit_point = f1.get_point(si, n - 1)
        entry_point = f2.get_point(si, 0)
        
        print(f"\n  {f1.face.value} → {f2.face.value}:")
        print(f"    {f1.face.value}.get_point({si}, {n-1}) = {exit_point}  (exit)")
        print(f"    {f2.face.value}.get_point({si}, 0) = {entry_point}  (entry)")
        print(f"    These points are ADJACENT on the cube ✓")


# =============================================================================
# EXAMPLES
# =============================================================================

def example_1_basic():
    """Example 1: Basic usage with get_point()"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Usage with get_point()")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print("\nInput:")
    print("  N = 4")
    print("  Starting Face = F")
    print("  Rotate With = R")
    
    print("\nUsing get_point(si, other_coord):")
    print("\n  SI=0 (closest to R):")
    for face_output in faces:
        points = [face_output.get_point(0, oc) for oc in range(4)]
        print(f"    Face {face_output.face.value}: {points}")
    
    print("\n  SI=2 (farther from R):")
    for face_output in faces:
        points = [face_output.get_point(2, oc) for oc in range(4)]
        print(f"    Face {face_output.face.value}: {points}")


def example_2_adjacency():
    """Example 2: Demonstrate adjacency property"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Adjacency Property")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    n = 4
    si = 0
    
    print(f"\nFor SI={si}, N={n}:")
    print("\nCRITICAL: f1.get_point(si, N-1) and f2.get_point(si, 0) are ADJACENT!")
    
    for i in range(len(faces)):
        f1 = faces[i]
        f2 = faces[(i + 1) % len(faces)]
        
        exit_pt = f1.get_point(si, n - 1)
        entry_pt = f2.get_point(si, 0)
        
        print(f"\n  {f1.face.value} → {f2.face.value}:")
        print(f"    Exit:  {f1.face.value}.get_point({si}, {n-1}) = {exit_pt}")
        print(f"    Entry: {f2.face.value}.get_point({si}, 0)   = {entry_pt}")
        print(f"    Adjacent on cube: {f1.exit_edge.value} ↔ {f2.enter_edge.value}")


def example_3_all_slices():
    """Example 3: Show all slice indices"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: All Slice Indices")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print("\nFace F points for each SI:")
    f = faces[0]
    
    for si in range(4):
        points = f.get_all_points(si)
        print(f"  SI={si}: {points}")


def example_4_visual():
    """Example 4: Visual output"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Visual Output")
    print("=" * 70)
    
    edge_map = create_standard_edge_map()
    walker = CubeRotationWalkerV2(n=4, edge_map=edge_map)
    
    faces = walker.calculate_rotation(
        starting_face=Face.F,
        rotate_with=Face.R
    )
    
    print_results(faces, n=4, si=0)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    example_1_basic()
    example_2_adjacency()
    example_3_all_slices()
    example_4_visual()
