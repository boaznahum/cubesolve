# Direct NxN Solvers - Design Document

## Overview

This package contains **non-reduction** solvers for NxN cubes. Unlike the reduction
method (which reduces big cubes to 3x3 state first), these solvers work directly
on the NxN cube structure.

## Available Methods

| Method | Class | Complexity | Status |
|--------|-------|------------|--------|
| Commutator-based | `CommutatorNxNSolver` | Simple | **Selected for implementation** |
| Layer-by-Layer | `LayerByLayerNxNSolver` | Moderate | Stub only |
| Cage Method | - | Complex | Not implemented |

---

## Commutator-Based Solver Design

### 1. Core Concept

A **commutator** `[A, B] = A B A' B'` is a move sequence that:
- Cycles exactly 3 pieces
- Leaves all other pieces unchanged
- Is always an even permutation (no parity issues)

### 2. Algorithm Overview - Detailed Pseudo Code

#### 2.1 Main Solving Flow

```
solve():
    if cube.size > 3:
        solve_centers()
        solve_edges()
    solve_corners()
```

#### 2.2 Center Solving Algorithm

The challenge: A commutator is a 3-cycle. We need to cycle pieces without
destroying already-solved pieces.

**Key concept: Buffer Position**
- Choose a "buffer" position (e.g., Front face, position (0,0))
- The buffer participates in every 3-cycle
- We cycle: buffer → target → source → buffer

```
solve_centers():
    # Solve faces in order: first face, opposite, then pairs
    for target_face in [D, U, F, B, L, R]:
        target_color = get_color_for_face(target_face)

        # Bring target face to FRONT for easier manipulation
        bring_face_to_front(target_face)

        for each position (r, c) on front face center:
            if front.center[r,c].color == target_color:
                continue  # Already correct

            # This position needs fixing
            # Find a piece of target_color somewhere else
            source = find_piece_of_color(target_color, exclude=front)

            if source is None:
                # All pieces of this color are on front face
                # but in wrong positions - need internal swap
                handle_internal_swap(front, r, c, target_color)
            else:
                # Standard case: bring source piece to target position
                # using 3-cycle through buffer

                # Step 1: Setup - rotate source face so piece aligns with buffer column
                setup_moves = calculate_setup(source)
                do(setup_moves)

                # Step 2: Execute commutator
                # Cycles: front[r,c] → buffer → source_piece → front[r,c]
                execute_center_commutator(target_col=c, source_face, source_col)

                # Step 3: Undo setup
                do(setup_moves.inverse)

find_piece_of_color(color, exclude_face):
    # Search order matters for efficiency
    # Check UP first (easiest to commutate with FRONT)
    # Then BACK
    # Then sides (L, R) - require different setup

    for face in [UP, BACK, LEFT, RIGHT, DOWN]:
        if face == exclude_face or face == exclude_face.opposite:
            continue
        for (r, c) in face.center_positions:
            if face.center[r,c].color == color:
                return (face, r, c)
    return None

handle_internal_swap(face, r, c, color):
    # All pieces of 'color' are on this face but wrong positions
    # Need to:
    #   1. Move wrong piece OUT to buffer face (UP)
    #   2. Move correct piece IN
    #   3. Move buffer piece to where correct piece was

    correct_piece_pos = find_on_face(face, color)  # Find one with correct color

    # Use commutator to cycle:
    # face[r,c] (wrong) → UP[buffer] → face[correct_pos] (correct) → face[r,c]
    ...
```

#### 2.3 The Center Commutator in Detail

```
execute_center_commutator(target_col, source_face, source_col):
    """
    Cycles 3 center pieces:
      FRONT[target_col] ↔ SOURCE[source_col] ↔ BUFFER

    The commutator pattern [A, B] = A B A' B':
      A = slice move (M slice) - moves column up/down
      B = face move (F) - rotates front face

    For source on UP face:
      rotate_mul = 1
    For source on BACK face:
      rotate_mul = 2 (need to go "through" to back)
    """

    # Which M slice to use?
    # M[1] affects column 0, M[2] affects column 1, etc. (1-indexed)
    target_slice = M[target_col + 1]
    source_slice = M[source_col + 1]

    # The commutator sequence:
    # This cycles: front[target_col] → source[source_col] → front[rotated_col]

    if source_face == UP:
        mul = 1
    else:  # BACK
        mul = 2

    sequence = [
        target_slice' * mul,    # Bring target column up to source face
        F,                       # Rotate front - target piece now in different column
        source_slice' * mul,    # Bring source column down
        F',                      # Undo front rotation
        target_slice * mul,     # Return target column
        F,                       # Rotate again
        source_slice * mul,     # Return source column
        F'                       # Undo rotation
    ]

    execute(sequence)
```

#### 2.4 Edge Solving Algorithm

Edges are more complex because:
1. Each edge has 2 colors (orientation matters)
2. On 4x4+, edges have multiple "wings"
3. The last edge cannot be solved with a 3-cycle alone (parity)

```
solve_edges():
    # For each edge position (12 edges total)
    while not all_edges_solved():

        # Find an unsolved edge
        target_edge = find_unsolved_edge()

        # Bring it to a working position (e.g., Front-Left)
        bring_edge_to_front_left(target_edge)
        target_edge = cube.front.edge_left

        # Determine what colors this edge should have
        required_colors = get_required_colors_for_position(front_left)

        # For each wing on this edge
        for wing_index in range(edge.n_slices):
            wing = target_edge.get_slice(wing_index)

            if wing.colors == required_colors and wing.is_correctly_oriented:
                continue  # This wing is solved

            # Find a wing with the required colors
            source_wing = find_wing_with_colors(required_colors, exclude=target_edge)

            if source_wing is None:
                # Wing is on same edge but wrong position/orientation
                handle_same_edge_flip(target_edge, wing_index)
            else:
                # Bring source wing to target position
                bring_source_edge_to_front_right(source_wing.parent)

                # Execute edge commutator
                execute_edge_commutator(wing_index)

    # Handle last edge parity if needed
    if not all_edges_solved():
        fix_edge_parity()

execute_edge_commutator(wing_index):
    """
    Cycles wings between front-left and front-right edges.

    Uses E slice (horizontal slice) to move wings.
    """

    slice_alg = E[wing_index + 1]  # Which E slice

    # Insert-Extract pattern:
    # R F' U R' F  -- this is an "inserter" that swaps edges
    inserter = R + F' + U + R' + F

    sequence = [
        slice_alg,        # Move target wing to E slice
        inserter,         # Swap with right edge
        slice_alg'        # Return wing
    ]

    execute(sequence)
```

#### 2.5 Corner Solving Algorithm

Corners are simpler - always 8 corners, same on any size cube.
Two phases: Position, then Orient.

```
solve_corners():
    position_corners()
    orient_corners()

position_corners():
    """
    Place all corners in correct positions (ignore orientation).
    Use Niklas commutator for 3-cycles.
    """

    while not all_corners_positioned():
        # Find a corner in wrong position
        wrong_corner = find_mispositioned_corner()

        # Find where it should go
        target_position = get_target_position(wrong_corner)

        # Find what corner is currently at target position
        displaced_corner = corner_at(target_position)

        # Setup: bring both corners to positions affected by Niklas
        # Niklas affects: UFR, UBL, UFL
        setup = calculate_corner_setup(wrong_corner, target_position)
        do(setup)

        # Execute Niklas: R U' L' U R' U' L U
        # Cycles: UFR → UBL → UFL → UFR
        do(NIKLAS)

        do(setup.inverse)

orient_corners():
    """
    Twist corners to correct orientation.
    All corners are in correct positions now.
    """

    while not all_corners_oriented():
        # Find a corner that needs clockwise twist
        corner_cw = find_corner_needing_cw_twist()

        # Find a corner that needs counter-clockwise twist
        # (corners twist in pairs to preserve cube state)
        corner_ccw = find_corner_needing_ccw_twist()

        # Setup both corners to UFR position and twist
        # Using: (R' D' R D) x 2 for CW twist

        setup1 = bring_corner_to_UFR(corner_cw)
        do(setup1)
        do(R' D' R D, R' D' R D)  # Twist CW
        do(setup1.inverse)

        setup2 = bring_corner_to_UFR(corner_ccw)
        do(setup2)
        do(D' R' D R, D' R' D R, D' R' D R)  # Twist CCW (3 times = CCW)
        do(setup2.inverse)
```

#### 2.6 Parity Handling

In commutator method, parity manifests differently than in reduction:

```
Parity situations:

1. LAST CENTER PIECE:
   - Cannot 3-cycle last piece if only 2 positions wrong
   - Solution: Use 2-swap algorithm instead of commutator

2. LAST EDGE:
   - If only 1 edge unsolved with 2 wings flipped
   - This is "edge parity" - need special algorithm
   - Use: M' U M' U M' U2 M U M U M U2 (or similar)

3. LAST CORNER:
   - If 2 corners need swapping (odd permutation)
   - This means edges have compensating swap
   - Rare in commutator method if done carefully
```

### 3. Architecture - Reusing Existing Infrastructure

**KEY INSIGHT:** The existing `NxNCenters._block_communicator()` already implements
a commutator pattern! We can learn from and reuse this.

#### 3.1 Class Hierarchy

```
SolverElementsProvider (Protocol)      # Minimal interface for solver components
├── BaseSolver                         # Common solver functionality
│   └── CommutatorNxNSolver            # Our new solver
│       ├── CommutatorCenters          # SolverElement for centers
│       ├── CommutatorEdges            # SolverElement for edges
│       └── CommutatorCorners          # SolverElement for corners
│
└── AbstractReducer                    # Base class for reducers
    └── BeginnerReducer                # Uses NxNCenters, NxNEdges

SolverElement(provider: SolverElementsProvider)  # Base for solver components
├── Provides: cube, op, ann, cmn, cqr
├── CommutatorCenters(SolverElement)
├── CommutatorEdges(SolverElement)
└── CommutatorCorners(SolverElement)
```

**Note:** `SolverElement` accepts any `SolverElementsProvider` (not just `BaseSolver`),
allowing both solvers and reducers to use the same component infrastructure.
See: `SOLVER_ARCHITECTURE.md` for details.

#### 3.2 Reusable Components from Existing Code

| Component | Location | What it provides |
|-----------|----------|------------------|
| `SolverElementsProvider` | `protocols/SolverElementsProvider.py` | Minimal interface for solver components |
| `SolverElement` | `common/SolverElement.py` | Base class with cube, op, annotations |
| `BaseSolver` | `common/BaseSolver.py` | Solver base with debug, solve interface |
| `CommonOp` | `common/CommonOp.py` | `bring_face_front()`, `bring_edge_to_front_left_by_whole_rotate()` |
| `CubeQueries2` | `model/CubeQueries2.py` | `find_edge()`, `rotate_and_check()`, `count_color_on_face()` |
| `FaceTracker` | `common/FaceTracker.py` | Track faces/pieces during solving |
| `Algs` | `algs/Algs.py` | All algorithms including slices |

#### 3.3 Key Algorithm APIs

```python
from cube.domain.algs import Algs

# Face moves
Algs.R, Algs.U, Algs.F, Algs.L, Algs.D, Algs.B
Algs.R.prime  # R'
Algs.R * 2    # R2

# Slice moves (1-indexed, for NxN cubes)
Algs.M[2]           # Second M slice
Algs.M[1:3]         # M slices 1 and 2
Algs.M[[1, 3]]      # M slices 1 and 3 (non-contiguous)
Algs.E[2].prime     # E slice 2, inverted

# Wide moves
Algs.R[1:3]         # Rw (R + slice)

# Whole cube rotations
Algs.X, Algs.Y, Algs.Z

# Sequence
Algs.seq_alg(None, Algs.R, Algs.U, Algs.R.prime)
```

### 3.4 The Commutator Pattern from NxNCenters

The existing `_block_communicator()` in `NxNCenters.py` implements:

```python
# This is [A, B] where:
#   A = rotate_on_cell (M slice move)
#   B = on_front_rotate (F face move)

cum = [
    rotate_on_cell.prime * rotate_mul,    # A'
    on_front_rotate,                       # B
    rotate_on_second.prime * rotate_mul,  # (setup for second position)
    on_front_rotate.prime,                 # B'
    rotate_on_cell * rotate_mul,          # A
    on_front_rotate,                       # B
    rotate_on_second * rotate_mul,        # (restore second position)
    on_front_rotate.prime                  # B'
]
```

This is actually a **double commutator** that cycles 3 center blocks!

### 4. Solving Phases - Detailed Implementation

#### Phase 1: Centers (for N > 3)

For a 4x4 cube, each face has 4 center pieces (2x2 block).
For a 5x5 cube, each face has 9 center pieces (3x3 block).

**Piece Access API:**
```python
# Access center pieces
face = cube.front
center = face.center                          # Center object
center_slice = center.get_center_slice((r, c))  # CenterSlice at row r, col c
color = center_slice.color                    # Color of this center piece

# Iterate all center slices
for cs in face.center.all_slices:
    print(cs.color)

# Check if center is solved (all same color)
is_solved = face.center.is3x3
```

**Finding Pieces:**
```python
def find_center_piece_by_color(cube: Cube, target_color: Color) -> list[tuple[Face, int, int]]:
    """Find all center pieces of a given color."""
    results = []
    for face in cube.faces:
        n = cube.n_slices
        for r in range(n):
            for c in range(n):
                cs = face.center.get_center_slice((r, c))
                if cs.color == target_color:
                    results.append((face, r, c))
    return results
```

**Strategy:**
1. Choose a reference face (e.g., D/White)
2. For each center position on that face:
   - If wrong color, find a piece of correct color elsewhere
   - Use commutator to 3-cycle: wrong_piece → buffer → correct_piece → target
3. Repeat for opposite face, then remaining 4 faces

**Center Commutator - Using M Slices:**
```python
def center_commutator(self, target_col: int, source_col: int, is_back: bool):
    """
    3-cycle centers between Front and Up/Back faces.

    Based on NxNCenters._block_communicator() pattern.
    """
    rotate_mul = 2 if is_back else 1

    # Get slice algorithms
    slice_target = Algs.M[target_col + 1].prime  # +1 because slices are 1-indexed
    slice_source = Algs.M[source_col + 1].prime

    # The commutator: [slice, F] pattern
    alg = Algs.seq_alg(None,
        slice_target.prime * rotate_mul,
        Algs.F,
        slice_source.prime * rotate_mul,
        Algs.F.prime,
        slice_target * rotate_mul,
        Algs.F,
        slice_source * rotate_mul,
        Algs.F.prime
    )

    self.op.play(alg)
```

#### Phase 2: Edges

For 3x3: 12 edges
For 4x4: 24 edge "wings" (2 per edge position)
For 5x5: 24 edge wings + 12 center edges

**Edge Access API:**
```python
# Access edges
edge = cube.front.edge_left          # Edge object
edge = cube.fl                       # Shortcut: front-left edge

# Edge slices (wings)
n_slices = edge.n_slices             # Number of wing pairs
wing = edge.get_slice(i)             # EdgeWing at index i
colors = wing.colors_id              # frozenset of 2 colors

# Check if edge is solved (all wings paired correctly)
is_solved = edge.is3x3

# Find edges
edge = cqr.find_edge(cube.edges, lambda e: not e.is3x3)
```

**Finding Wing Pieces:**
```python
def find_wing_by_colors(cube: Cube, color1: Color, color2: Color) -> list[EdgeWing]:
    """Find all wings with given colors."""
    target_id = frozenset([color1, color2])
    results = []
    for edge in cube.edges:
        for i in range(edge.n_slices):
            wing = edge.get_slice(i)
            if wing.colors_id == target_id:
                results.append(wing)
    return results
```

**Edge Commutator - Basic:**
```python
# Classic edge 3-cycle: UF → DF → UB
# [R U R', D] = R U R' D R U' R' D'
edge_cycle = Algs.R + Algs.U + Algs.R.prime + Algs.D + \
             Algs.R + Algs.U.prime + Algs.R.prime + Algs.D.prime
```

**Edge Commutator - For Wings (4x4+):**
```python
def wing_commutator(self, slice_index: int):
    """
    3-cycle wing edges using E slice.

    Based on NxNEdges pattern.
    """
    # E slice for wing manipulation
    slice_alg = Algs.E[slice_index + 1]  # +1 for 1-indexing

    # Insert/extract pattern
    rf = Algs.R + Algs.F.prime + Algs.U + Algs.R.prime + Algs.F  # from NxNEdges

    alg = slice_alg + rf + slice_alg.prime
    self.op.play(alg)
```

#### Phase 3: Corners

All NxN cubes have exactly 8 corners (same as 3x3).

**Corner Access API:**
```python
# Access corners
corner = cube.front.corner_top_right   # Corner object
corner = cube.ufr                       # Shortcut: up-front-right corner

# Corner properties
colors = corner.colors_id              # frozenset of 3 colors
faces = corner.faces                   # 3 faces this corner touches

# Find corners
def find_corner_by_colors(cube: Cube, c1: Color, c2: Color, c3: Color) -> Corner:
    target = frozenset([c1, c2, c3])
    for corner in cube.corners:
        if corner.colors_id == target:
            return corner
    return None
```

**Corner Commutator (Niklas):**
```python
# Niklas: 3-cycles UFR → UBL → UFL
# R U' L' U R' U' L U
niklas = Algs.R + Algs.U.prime + Algs.L.prime + Algs.U + \
         Algs.R.prime + Algs.U.prime + Algs.L + Algs.U
```

**Corner Orientation (Sune-based):**
```python
# Twist corner in place (UFR clockwise)
# R U R' U R U2 R'
sune = Algs.R + Algs.U + Algs.R.prime + Algs.U + \
       Algs.R + Algs.U * 2 + Algs.R.prime
```

### 5. Data Structures

#### 5.1 Piece Identification

```python
@dataclass
class PieceLocation:
    """Identifies a piece's current position on the cube."""
    piece_type: Literal["center", "edge", "corner"]
    face: Face           # Primary face
    position: tuple      # (row, col) for centers, edge/corner index

@dataclass
class PieceIdentity:
    """Identifies which piece this is (by its colors)."""
    colors: tuple[Color, ...]  # 1 for center, 2 for edge, 3 for corner
```

#### 5.2 Commutator Representation

```python
@dataclass
class Commutator:
    """Represents a commutator [A, B] with optional setup."""
    a: str              # First sequence
    b: str              # Interchange sequence
    setup: str = ""     # Optional setup moves

    def execute(self, op: OperatorProtocol) -> None:
        """Execute [setup: [A, B]] = setup A B A' B' setup'"""
        if self.setup:
            op.play(self.setup)
        op.play(self.a)
        op.play(self.b)
        op.play(inverse(self.a))
        op.play(inverse(self.b))
        if self.setup:
            op.play(inverse(self.setup))
```

#### 5.3 Commutator Library

```python
class CommutatorLibrary:
    """Database of commutators indexed by effect."""

    # Maps (source, target, third) -> Commutator
    center_commutators: dict[tuple, Commutator]
    edge_commutators: dict[tuple, Commutator]
    corner_commutators: dict[tuple, Commutator]

    def find_commutator(
        self,
        piece_type: str,
        source: PieceLocation,
        target: PieceLocation
    ) -> Commutator:
        """Find a commutator that moves piece from source to target."""
        ...
```

### 6. Implementation Plan - Detailed Steps

#### Step 1: Create Main Solver Class

**File:** `CommutatorNxNSolver.py` (update existing stub)

```python
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.solver import Solver, SolveStep, SolverResults
from cube.domain.solver.SolverName import SolverName

class CommutatorNxNSolver(BaseSolver):
    """Solves NxN cubes using commutators."""

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__(op)
        self._centers = CommutatorCenters(self)
        self._edges = CommutatorEdges(self)
        self._corners = CommutatorCorners(self)

    @property
    def get_code(self) -> SolverName:
        return SolverName.COMMUTATOR  # Add to enum

    @property
    def status(self) -> str:
        if self.is_solved:
            return "Solved"
        if not self._centers.is_solved:
            return f"Centers: {self._centers.status}"
        if not self._edges.is_solved:
            return f"Edges: {self._edges.status}"
        return f"Corners: {self._corners.status}"

    def solve(self, debug=None, animation=True, what=SolveStep.ALL) -> SolverResults:
        with self.op.with_animation(animation=animation):
            if not self.cube.is3x3:  # N > 3
                self._centers.solve()
                self._edges.solve()
            self._corners.solve()
        return SolverResults()
```

**Tasks:**
- [ ] Update `CommutatorNxNSolver` class to inherit from `BaseSolver`
- [ ] Add `SolverName.COMMUTATOR` to `SolverName` enum
- [ ] Wire up to `Solvers` factory

#### Step 2: Create Center Solver Component

**File:** `CommutatorCenters.py` (new file)

```python
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.protocols import SolverElementsProvider

class CommutatorCenters(SolverElement):
    """Solves center pieces using commutators."""

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver)
        self._set_debug_prefix("CommCenters")

    @property
    def is_solved(self) -> bool:
        return all(f.center.is3x3 for f in self.cube.faces)

    @property
    def status(self) -> str:
        solved = sum(1 for f in self.cube.faces if f.center.is3x3)
        return f"{solved}/6 faces"

    def solve(self) -> None:
        if self.is_solved:
            return

        with self.ann.annotate(h1="Commutator: Centers"):
            # Solve each face in order: D, U, F, B, L, R
            for face in self._face_order():
                self._solve_face(face)

    def _face_order(self) -> list[Face]:
        """Order faces for solving (opposite pairs)."""
        cube = self.cube
        return [cube.down, cube.up, cube.front, cube.back, cube.left, cube.right]

    def _solve_face(self, target_face: Face) -> None:
        """Solve all centers on target_face."""
        target_color = self._get_target_color(target_face)

        with self.ann.annotate(h2=f"Face {target_face.name.value}"):
            # Bring target face to front
            self.cmn.bring_face_front(target_face)
            target_face = self.cube.front

            # For each center position
            for r in range(self.cube.n_slices):
                for c in range(self.cube.n_slices):
                    self._solve_center_at(target_face, r, c, target_color)

    def _solve_center_at(self, face: Face, r: int, c: int, target_color: Color) -> None:
        """Solve a single center position using commutator."""
        cs = face.center.get_center_slice((r, c))
        if cs.color == target_color:
            return  # Already solved

        # Find a piece of target_color on Up or Back face
        source = self._find_source_piece(target_color, exclude_face=face)
        if source is None:
            raise InternalSWError(f"No source found for {target_color}")

        # Execute commutator to cycle pieces
        self._center_commutator(face, r, c, source)

    def _center_commutator(self, target_face: Face, tr: int, tc: int,
                           source: tuple[Face, int, int]) -> None:
        """Execute center commutator."""
        # Implementation based on NxNCenters._block_communicator()
        ...
```

**Tasks:**
- [ ] Create `CommutatorCenters.py`
- [ ] Implement `_solve_face()` for each face
- [ ] Implement `_find_source_piece()` to locate pieces
- [ ] Implement `_center_commutator()` based on `NxNCenters._block_communicator()`

#### Step 3: Create Edge Solver Component

**File:** `CommutatorEdges.py` (new file)

```python
class CommutatorEdges(SolverElement):
    """Solves edge pieces using commutators."""

    @property
    def is_solved(self) -> bool:
        return all(e.is3x3 for e in self.cube.edges)

    def solve(self) -> None:
        with self.ann.annotate(h1="Commutator: Edges"):
            while not self.is_solved:
                edge = self.cqr.find_edge(self.cube.edges, lambda e: not e.is3x3)
                self._solve_edge(edge)

    def _solve_edge(self, edge: Edge) -> None:
        """Solve all wings on an edge."""
        # Bring edge to front-left
        self.cmn.bring_edge_to_front_left_by_whole_rotate(edge)
        edge = self.cube.front.edge_left

        # For each wing
        for i in range(edge.n_slices):
            self._solve_wing(edge, i)

    def _edge_commutator(self, target_edge: Edge, wing_index: int) -> None:
        """Execute edge commutator."""
        # Based on NxNEdges patterns
        ...
```

**Tasks:**
- [ ] Create `CommutatorEdges.py`
- [ ] Implement wing finding and solving
- [ ] Implement `_edge_commutator()` based on `NxNEdges` patterns

#### Step 4: Create Corner Solver Component

**File:** `CommutatorCorners.py` (new file)

```python
class CommutatorCorners(SolverElement):
    """Solves corner pieces using commutators."""

    # Classic corner commutators
    NIKLAS = "R U' L' U R' U' L U"  # 3-cycle: UFR → UBL → UFL
    A_PERM = "R' F R' B2 R F' R' B2 R2"  # Another 3-cycle

    def solve(self) -> None:
        with self.ann.annotate(h1="Commutator: Corners"):
            self._position_corners()
            self._orient_corners()

    def _position_corners(self) -> None:
        """Place all corners in correct positions."""
        while not self._all_positioned():
            self._niklas_cycle()

    def _orient_corners(self) -> None:
        """Twist corners to correct orientation."""
        while not self._all_oriented():
            self._twist_corner()
```

**Tasks:**
- [ ] Create `CommutatorCorners.py`
- [ ] Implement Niklas corner 3-cycle
- [ ] Implement corner orientation algorithms

#### Step 5: Register Solver

**File:** Update `Solvers.py` and `SolverName.py`

```python
# SolverName.py - add new enum value
class SolverName(Enum):
    LBL = "LBL"
    CFOP = "CFOP"
    KOCIEMBA = "Kociemba"
    COMMUTATOR = "Commutator"  # NEW

# Solvers.py - add factory method
@staticmethod
def commutator(op: OperatorProtocol) -> Solver:
    """Get commutator-based solver for NxN cubes."""
    from .direct import CommutatorNxNSolver
    return CommutatorNxNSolver(op)
```

**Tasks:**
- [ ] Add `COMMUTATOR` to `SolverName` enum
- [ ] Add `commutator()` factory method to `Solvers`
- [ ] Update `by_name()` and `next_solver()` in `Solvers`

#### Step 6: Testing

**File:** `tests/solvers/test_commutator_solver.py`

```python
import pytest
from cube.domain.model.Cube import Cube
from cube.domain.solver.Solvers import Solvers

@pytest.fixture
def scrambled_4x4():
    cube = Cube(4)
    cube.scramble()
    return cube

def test_commutator_solver_4x4(scrambled_4x4):
    op = Operator(scrambled_4x4)
    solver = Solvers.commutator(op)
    solver.solve()
    assert scrambled_4x4.solved

def test_commutator_solver_5x5():
    cube = Cube(5)
    cube.scramble()
    op = Operator(cube)
    solver = Solvers.commutator(op)
    solver.solve()
    assert cube.solved
```

**Tasks:**
- [ ] Create test file for commutator solver
- [ ] Test on 3x3, 4x4, 5x5 cubes
- [ ] Test individual phases (centers, edges, corners)
- [ ] Compare move count with reduction method

### 7. Key Commutators Reference

#### Centers (4x4+)

| Name | Moves | Effect |
|------|-------|--------|
| U-D Center | `[Rw U Rw', D2]` | Cycles 3 centers between U and D |
| U-F Center | `[Rw U Rw', F2]` | Cycles 3 centers between U and F |
| Slice Center | `[M' U M, U2]` | Cycles centers in M slice |

#### Edges

| Name | Moves | Effect |
|------|-------|--------|
| Basic | `[R U R', D]` | UF → DF → UB |
| M-slice | `[M' U M, U2]` | Cycles M-slice edges |
| Wide | `[Rw U Rw', D]` | For wing edges on 4x4+ |

#### Corners

| Name | Moves | Effect |
|------|-------|--------|
| Niklas | `R U' L' U R' U' L U` | UFR → UBL → UFL |
| A-perm | `R' F R' B2 R F' R' B2 R2` | Corner 3-cycle |
| Twist CW | `R' D' R D` x2-3 | Twists corner in place |

### 8. Complexity Analysis

| Phase | Pieces | Commutators | Worst Case Moves |
|-------|--------|-------------|------------------|
| Centers (4x4) | 24 | ~24 | ~24 × 16 = 384 |
| Centers (5x5) | 54 | ~54 | ~54 × 16 = 864 |
| Edges (4x4) | 24 | ~24 | ~24 × 12 = 288 |
| Corners | 8 | ~8 | ~8 × 10 = 80 |

Total for 4x4: ~750 moves (vs ~200 for reduction method)
Total for 5x5: ~1200 moves (vs ~300 for reduction method)

**Trade-off:** More moves, but no parity issues and simpler logic.

### 9. Future Optimizations

1. **Commutator caching** - Pre-compute optimal commutator for each case
2. **Setup minimization** - Choose commutators that minimize setup moves
3. **Batch solving** - Solve multiple pieces with one commutator when possible
4. **Floating pieces** - Delay solving some pieces to reduce setup moves

---

## Comparison with Reduction Method

| Aspect | Reduction | Commutator |
|--------|-----------|------------|
| Move count | Lower (~200-300) | Higher (~750-1200) |
| Parity handling | Required | Not needed |
| Logic complexity | Higher | Lower |
| Implementation | Moderate | Simple |
| Debugging | Harder | Easier |
| Extensibility | Limited | High |

---

## References

- [Speedsolving Wiki - Commutators](https://www.speedsolving.com/wiki/index.php/Commutator)
- [Ryan Heise - Commutator Tutorial](https://www.ryanheise.com/cube/commutators.html)
- [Big Cube Commutators](https://www.speedsolving.com/wiki/index.php/Big_Cube_Commutators)
