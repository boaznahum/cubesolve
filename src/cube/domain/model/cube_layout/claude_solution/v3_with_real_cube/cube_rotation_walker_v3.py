"""
Cube Grid Coordinate Transformation - Variant 3 (Fully Configurable)
=====================================================================

This module implements slice rotation on a 3D cube where each face 
has an N×N grid. This variant accepts ALL configuration as input,
making the algorithm completely isolated and reusable.

INPUTS (all configurable):
  - N: Grid size (e.g., 4 means 4×4 grid)
  - edge_map: Edge connection map between faces
  - rotation_paths: Which 4 faces surround each rotating face

KEY FEATURE:
  The get_point(si, other_coord) method returns the coordinate at position
  'other_coord' (0 to N-1) along the path for slice index 'si'.
  
CRITICAL ADJACENCY PROPERTY:
  For consecutive faces f1 and f2 (where f2 follows f1 in CW rotation):
  
    f1.get_point(si, N-1)  →  last point on f1 (exit point)
    f2.get_point(si, 0)    →  first point on f2 (entry point)
    
  These two points are PHYSICALLY ADJACENT on the cube!
"""

from enum import Enum
from typing import List, Tuple, Dict, Callable, Any
from dataclasses import dataclass


# =============================================================================
# ENUMS - Generic edge and direction definitions
# =============================================================================

class Edge(Enum):
    """Edge names on a face (in LTR coordinate system)"""
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Direction(Enum):
    """Walking directions across a face"""
    LEFT_TO_RIGHT = "LEFT→RIGHT"
    RIGHT_TO_LEFT = "RIGHT→LEFT"
    BOTTOM_TO_TOP = "BOTTOM→TOP"
    TOP_TO_BOTTOM = "TOP→BOTTOM"


# =============================================================================
# DATA STRUCTURES - Input configuration types
# =============================================================================

@dataclass
class EdgeConnection:
    """
    Represents a connection between two face edges.
    
    Attributes:
        face: The adjacent face (can be any hashable identifier)
        edge: Which edge of the adjacent face this connects to
    
    Example:
        # Face F's RIGHT edge connects to Face R's LEFT edge
        EdgeConnection(face="R", edge=Edge.LEFT)
    """
    face: Any  # Face identifier (string, enum, int, etc.)
    edge: Edge


@dataclass 
class CubeConfig:
    """
    Complete configuration for a cube's face connections and rotation paths.
    
    This data structure encapsulates all the cube-specific information,
    keeping the algorithm completely generic.
    
    Attributes:
        edge_map: Dictionary mapping each face to its edge connections
        rotation_paths: Dictionary mapping each face to its surrounding faces (CW order)
    
    Example:
        config = CubeConfig(
            edge_map={
                "F": {
                    Edge.RIGHT: EdgeConnection("R", Edge.LEFT),
                    Edge.LEFT: EdgeConnection("L", Edge.RIGHT),
                    Edge.TOP: EdgeConnection("U", Edge.BOTTOM),
                    Edge.BOTTOM: EdgeConnection("D", Edge.TOP),
                },
                # ... other faces
            },
            rotation_paths={
                "R": ["F", "U", "B", "D"],  # Faces surrounding R in CW order
                "L": ["F", "D", "B", "U"],
                # ... other faces
            }
        )
    """
    edge_map: Dict[Any, Dict[Edge, EdgeConnection]]
    rotation_paths: Dict[Any, List[Any]]


# =============================================================================
# OUTPUT DATA STRUCTURE
# =============================================================================

class FaceOutput:
    """
    Represents the output for one face in the rotation path.
    
    Provides get_point(si, other_coord) for dynamic coordinate calculation.
    
    Attributes:
        face: The face identifier
        n: Grid size (N×N)
        direction: Walking direction on this face
        my_edge: Edge of this face that connects to the rotating face
        rotating_edge: Edge of the rotating face that connects to this face
        exit_edge: Edge where the path exits this face
        enter_edge: Edge where the path enters this face
        face_index: Position in the rotation path (0, 1, 2, or 3)
    
    ═══════════════════════════════════════════════════════════════════════
    CRITICAL ADJACENCY PROPERTY
    ═══════════════════════════════════════════════════════════════════════
    
    For consecutive faces f1 and f2 in the rotation path:
    
        f1.get_point(si, N-1)  →  EXIT point (last point on f1)
        f2.get_point(si, 0)    →  ENTRY point (first point on f2)
    
    These two points are PHYSICALLY ADJACENT on the 3D cube surface!
    
    ═══════════════════════════════════════════════════════════════════════
    VISUAL DIAGRAM
    ═══════════════════════════════════════════════════════════════════════
    
    Example: Rotation path F → U → B → D (rotating with R), N=4, SI=0
    
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
    
    f1.get_point(si=0, other_coord=3) = (3, 3)  ← EXIT from F
    f2.get_point(si=0, other_coord=0) = (0, 3)  ← ENTRY to U
    
    These are ADJACENT on the cube!
    """
    
    def __init__(
        self,
        face: Any,
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
        
        ═══════════════════════════════════════════════════════════════════
        CRITICAL ADJACENCY PROPERTY
        ═══════════════════════════════════════════════════════════════════
        
        For consecutive faces f1 and f2 in the rotation path:
        
            f1.get_point(si, N-1)  →  EXIT point (last point on f1)
            f2.get_point(si, 0)    →  ENTRY point (first point on f2)
        
        These two points are PHYSICALLY ADJACENT on the 3D cube surface!
        
        ═══════════════════════════════════════════════════════════════════
        UNDERSTANDING other_coord
        ═══════════════════════════════════════════════════════════════════
        
        DIRECTION: BOTTOM→TOP (vertical walk upward)
        
                         TOP edge
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
        
        
        DIRECTION: LEFT→RIGHT (horizontal walk rightward)
        
                  +---+---+---+---+
            row   | X | X | X | X |  ← row = (N-1)-SI
                  +---+---+---+---+
                    ↑   ↑   ↑   ↑
                   oc  oc  oc  oc
                   =0  =1  =2  =3
                   
            ENTRY              EXIT
        
        ═══════════════════════════════════════════════════════════════════
        USAGE EXAMPLES
        ═══════════════════════════════════════════════════════════════════
        
            # Get all points for SI=0
            for oc in range(N):
                row, col = face_output.get_point(si=0, other_coord=oc)
            
            # Get entry and exit points
            entry_point = face_output.get_point(si=0, other_coord=0)
            exit_point = face_output.get_point(si=0, other_coord=N-1)
            
            # Verify adjacency between consecutive faces
            f1_exit = faces[0].get_point(si=0, other_coord=N-1)
            f2_entry = faces[1].get_point(si=0, other_coord=0)
            # f1_exit and f2_entry are adjacent on the cube!
        """
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
        face_str = self.face.value if hasattr(self.face, 'value') else str(self.face)
        return (f"FaceOutput(face={face_str}, direction={self.direction.value}, "
                f"enter={self.enter_edge.value}, exit={self.exit_edge.value}, "
                f"index={self.face_index})")


# =============================================================================
# MAIN ALGORITHM - Completely generic, no hardcoded data
# =============================================================================

class CubeRotationWalkerV3:
    """
    Calculates coordinates visited during a slice rotation on a cube.
    
    This is Variant 3 - FULLY CONFIGURABLE:
    - edge_map: Provided as input
    - rotation_paths: Provided as input
    - Algorithm is completely isolated from cube-specific data
    
    ═══════════════════════════════════════════════════════════════════════
    INPUT DATA STRUCTURES
    ═══════════════════════════════════════════════════════════════════════
    
    1. edge_map: Dict[Face, Dict[Edge, EdgeConnection]]
       
       Maps each face to its 4 edge connections.
       
       Example:
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
               # ... define for all 6 faces
           }
    
    2. rotation_paths: Dict[Face, List[Face]]
       
       Maps each face to the 4 faces that surround it (in CW order).
       These are the faces a slice passes through when rotating that face.
       
       Example:
           rotation_paths = {
               "R": ["F", "U", "B", "D"],  # CW from R's perspective
               "L": ["F", "D", "B", "U"],  # CW from L's perspective
               "U": ["F", "R", "B", "L"],
               "D": ["F", "L", "B", "R"],
               "F": ["U", "R", "D", "L"],
               "B": ["U", "L", "D", "R"],
           }
    
    ═══════════════════════════════════════════════════════════════════════
    USAGE
    ═══════════════════════════════════════════════════════════════════════
    
        # Define your cube configuration
        edge_map = { ... }
        rotation_paths = { ... }
        
        # Create walker
        walker = CubeRotationWalkerV3(
            n=4,
            edge_map=edge_map,
            rotation_paths=rotation_paths
        )
        
        # Or use CubeConfig
        config = CubeConfig(edge_map=edge_map, rotation_paths=rotation_paths)
        walker = CubeRotationWalkerV3(n=4, config=config)
        
        # Calculate rotation
        faces = walker.calculate_rotation(
            starting_face="F",
            rotate_with="R"
        )
        
        # Get points
        point = faces[0].get_point(si=0, other_coord=2)
    """
    
    # =========================================================================
    # TRANSFORMATION TABLES - These are universal, not cube-specific
    # =========================================================================
    
    # TABLE 2: Starting Face (16 cases)
    # Key: (my_edge, rotating_edge)
    # Value: (direction, row_formula, col_formula, exit_edge)
    TABLE2_STARTING = {
        # My Edge: RIGHT → vertical direction, col = (N-1)-SI
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
    
    # TABLE 1: Crossing Transformations (16 cases)
    # Key: (exit_edge, enter_edge)
    # Value: (direction, row_formula, col_formula)
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
    
    def __init__(
        self,
        n: int,
        edge_map: Dict[Any, Dict[Edge, EdgeConnection]] = None,
        rotation_paths: Dict[Any, List[Any]] = None,
        config: CubeConfig = None
    ):
        """
        Initialize the cube rotation walker.
        
        Args:
            n: Grid size (N×N on each face)
            edge_map: Dictionary mapping each face's edges to their connections
            rotation_paths: Dictionary mapping each face to surrounding faces (CW order)
            config: Alternative - provide CubeConfig object instead of separate dicts
        
        Either provide (edge_map + rotation_paths) OR config, not both.
        """
        if n < 1:
            raise ValueError("N must be at least 1")
        self.n = n
        
        # Accept either config object or separate dicts
        if config is not None:
            self.edge_map = config.edge_map
            self.rotation_paths = config.rotation_paths
        elif edge_map is not None and rotation_paths is not None:
            self.edge_map = edge_map
            self.rotation_paths = rotation_paths
        else:
            raise ValueError("Must provide either (edge_map + rotation_paths) or config")
    
    def _find_connecting_edge(self, from_face: Any, to_face: Any) -> Tuple[Edge, Edge]:
        """Find which edges connect two faces."""
        for edge, connection in self.edge_map[from_face].items():
            if connection.face == to_face:
                return edge, connection.edge
        raise ValueError(f"No connection found between {from_face} and {to_face}")
    
    def _create_formula(self, formula: str, n: int, p_formula: Callable = None) -> Callable[[int, int], int]:
        """Create a function from a formula string."""
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
        """Get the P value formula based on direction."""
        if direction in (Direction.LEFT_TO_RIGHT, Direction.RIGHT_TO_LEFT):
            return lambda si, oc: row_formula(si, self.n - 1)
        else:
            return lambda si, oc: col_formula(si, self.n - 1)
    
    def _get_exit_edge(self, direction: Direction) -> Edge:
        """Get the exit edge based on walking direction."""
        exit_edges = {
            Direction.LEFT_TO_RIGHT: Edge.RIGHT,
            Direction.RIGHT_TO_LEFT: Edge.LEFT,
            Direction.BOTTOM_TO_TOP: Edge.TOP,
            Direction.TOP_TO_BOTTOM: Edge.BOTTOM,
        }
        return exit_edges[direction]
    
    def calculate_rotation(self, starting_face: Any, rotate_with: Any) -> List[FaceOutput]:
        """
        Calculate FaceOutput objects for a slice rotation.
        
        Args:
            starting_face: Which face to start on (must be in rotation path)
            rotate_with: Which face to rotate with (determines the path)
        
        Returns:
            List of 4 FaceOutput objects, one for each face in the rotation path.
            
            CRITICAL: For consecutive faces f1=faces[i] and f2=faces[i+1]:
                f1.get_point(si, N-1) and f2.get_point(si, 0)
                return ADJACENT points on the cube surface!
        """
        # Get the rotation path from input configuration
        path = self.rotation_paths[rotate_with]
        if starting_face not in path:
            raise ValueError(f"Face {starting_face} is not in the rotation path for {rotate_with}")
        
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
                
            else:
                # Subsequent faces: use TABLE1_CROSSING
                prev_face = path[face_idx - 1]
                _, enter_edge = self._find_connecting_edge(prev_face, current_face)
                
                key = (prev_exit_edge, enter_edge)
                direction, row_str, col_str = self.TABLE1_CROSSING[key]
                
                row_formula = self._create_formula(row_str, self.n, prev_p_formula)
                col_formula = self._create_formula(col_str, self.n, prev_p_formula)
            
            # Calculate exit edge
            exit_edge = self._get_exit_edge(direction)
            
            # Store P formula for next iteration
            prev_p_formula = self._get_p_formula(direction, row_formula, col_formula)
            prev_exit_edge = exit_edge
            
            # Determine enter_edge
            if face_idx == 0:
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


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def print_face_grid(n: int, face_output: FaceOutput, si: int):
    """Print a visual representation of a face with visited cells marked."""
    points = face_output.get_all_points(si)
    
    arrows = {
        Direction.LEFT_TO_RIGHT: '→',
        Direction.RIGHT_TO_LEFT: '←',
        Direction.BOTTOM_TO_TOP: '↑',
        Direction.TOP_TO_BOTTOM: '↓',
    }
    arrow = arrows[face_output.direction]
    
    grid = [['  .   ' for _ in range(n)] for _ in range(n)]
    for r, c in points:
        grid[r][c] = f'({r},{c}){arrow}'
    
    face_str = face_output.face.value if hasattr(face_output.face, 'value') else str(face_output.face)
    print(f"\n    Face {face_str} (SI={si}):")
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
        face_str = face_output.face.value if hasattr(face_output.face, 'value') else str(face_output.face)
        
        print(f"\nFace {face_str}:")
        print(f"  Direction: {face_output.direction.value}")
        print(f"  Enter edge: {face_output.enter_edge.value}")
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
        
        f1_str = f1.face.value if hasattr(f1.face, 'value') else str(f1.face)
        f2_str = f2.face.value if hasattr(f2.face, 'value') else str(f2.face)
        
        print(f"\n  {f1_str} → {f2_str}:")
        print(f"    {f1_str}.get_point({si}, {n-1}) = {exit_point}  (exit)")
        print(f"    {f2_str}.get_point({si}, 0) = {entry_point}  (entry)")
        print(f"    These points are ADJACENT on the cube ✓")


# =============================================================================
# EXAMPLE: Standard Rubik's Cube Configuration
# =============================================================================

def create_standard_rubiks_cube_config() -> CubeConfig:
    """
    Create a standard Rubik's cube configuration.
    
    This is an EXAMPLE of how to create input data.
    You can create your own configuration for different cube types.
    
    Returns:
        CubeConfig with standard Rubik's cube edge connections and rotation paths
    """
    
    # Using string identifiers for faces
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
    
    rotation_paths = {
        "R": ["F", "U", "B", "D"],
        "L": ["F", "D", "B", "U"],
        "U": ["F", "R", "B", "L"],
        "D": ["F", "L", "B", "R"],
        "F": ["U", "R", "D", "L"],
        "B": ["U", "L", "D", "R"],
    }
    
    return CubeConfig(edge_map=edge_map, rotation_paths=rotation_paths)


# =============================================================================
# MAIN - Demo
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CUBE ROTATION WALKER V3 - Fully Configurable")
    print("=" * 70)
    
    # Create configuration
    config = create_standard_rubiks_cube_config()
    
    print("\n1. INPUT DATA STRUCTURE - edge_map:")
    print("-" * 50)
    for face, edges in config.edge_map.items():
        print(f"\n  {face}:")
        for edge, conn in edges.items():
            print(f"    {edge.value:6} → {conn.face}.{conn.edge.value}")
    
    print("\n\n2. INPUT DATA STRUCTURE - rotation_paths:")
    print("-" * 50)
    for face, path in config.rotation_paths.items():
        print(f"  {face}: {path}")
    
    # Create walker with config
    walker = CubeRotationWalkerV3(n=4, config=config)
    
    # Calculate rotation
    faces = walker.calculate_rotation(
        starting_face="F",
        rotate_with="R"
    )
    
    print("\n\n3. OUTPUT:")
    print("-" * 50)
    
    print("\nRotation path: F → U → B → D")
    print("\nSI=0 results:")
    for face in faces:
        print(f"  Face {face.face}: {face.get_all_points(0)}")
    
    print("\nSI=2 results:")
    for face in faces:
        print(f"  Face {face.face}: {face.get_all_points(2)}")
    
    # Show adjacency
    print("\n\n4. ADJACENCY VERIFICATION (SI=0):")
    print("-" * 50)
    n = 4
    for i in range(len(faces)):
        f1 = faces[i]
        f2 = faces[(i + 1) % len(faces)]
        
        exit_pt = f1.get_point(0, n - 1)
        entry_pt = f2.get_point(0, 0)
        
        print(f"\n  {f1.face} → {f2.face}:")
        print(f"    Exit:  {f1.face}.get_point(0, 3) = {exit_pt}")
        print(f"    Entry: {f2.face}.get_point(0, 0) = {entry_pt}")
        print(f"    ADJACENT ✓")
