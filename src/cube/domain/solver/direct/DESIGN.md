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

### 2. Algorithm Overview

```
solve():
    solve_centers()    # For N > 3
    solve_edges()
    solve_corners()

solve_X():
    while unsolved_X_pieces exist:
        piece = find_unsolved_X_piece()
        target = get_target_position(piece)
        (setup, A, B) = find_commutator(piece, target)
        execute([setup: [A, B]])
```

### 3. Architecture

```
CommutatorNxNSolver
├── CommutatorLibrary          # Database of known commutators
│   ├── CenterCommutators      # For center 3-cycles
│   ├── EdgeCommutators        # For edge 3-cycles
│   └── CornerCommutators      # For corner 3-cycles
├── PieceFinder                # Locates pieces on cube
│   ├── find_center_piece()
│   ├── find_edge_piece()
│   └── find_corner_piece()
├── SetupCalculator            # Computes setup moves
│   └── calculate_setup(piece, commutator) -> moves
└── CommutatorExecutor         # Executes [setup: [A, B]]
    └── execute(setup, A, B)
```

### 4. Solving Phases

#### Phase 1: Centers (for N > 3)

For a 4x4 cube, each face has 4 center pieces (2x2 block).
For a 5x5 cube, each face has 9 center pieces (3x3 block).

**Strategy:**
1. Choose a reference face (e.g., D/White)
2. Find center pieces that belong to this face
3. Use center commutators to cycle them into position
4. Repeat for opposite face, then remaining 4 faces

**Center Commutator Example (4x4):**
```
[Rw U Rw', D2]

Effect: 3-cycles centers on U and D faces
- Piece at Urf-center → Dlf-center → Ubr-center → Urf-center
```

#### Phase 2: Edges

For 3x3: 12 edges
For 4x4: 24 edge "wings" (2 per edge position)
For 5x5: 24 edge wings + 12 center edges

**Strategy:**
1. Identify all unsolved edge pieces
2. For each unsolved edge:
   - Find its target position
   - Calculate setup moves to align with known commutator
   - Execute commutator
   - Verify piece is solved

**Edge Commutator Example:**
```
[R U R', D]

Effect: 3-cycles edges
- UF → DF → UB → UF
```

#### Phase 3: Corners

All NxN cubes have exactly 8 corners (same as 3x3).

**Strategy:**
1. Position corners using corner 3-cycles
2. Orient corners using orientation commutators

**Corner Commutator (Niklas):**
```
[R U' L' U, R' U' L U]  -- simplified: R U' L' U R' U' L U

Effect: 3-cycles corners
- UFR → UBL → UFL → UFR
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

### 6. Implementation Plan

#### Step 1: Infrastructure
- [ ] Create `Commutator` dataclass
- [ ] Implement `inverse()` function for move sequences
- [ ] Create `CommutatorExecutor` class

#### Step 2: Piece Finding
- [ ] Implement `PieceFinder` for centers
- [ ] Implement `PieceFinder` for edges
- [ ] Implement `PieceFinder` for corners
- [ ] Add `get_target_position()` for each piece type

#### Step 3: Commutator Library
- [ ] Define basic center commutators (for 4x4, 5x5)
- [ ] Define basic edge commutators
- [ ] Define corner commutators (Niklas, A-perm style)
- [ ] Implement setup move calculation

#### Step 4: Solver Integration
- [ ] Implement `solve_centers()`
- [ ] Implement `solve_edges()`
- [ ] Implement `solve_corners()`
- [ ] Wire up main `solve()` method

#### Step 5: Testing
- [ ] Unit tests for commutator execution
- [ ] Unit tests for piece finding
- [ ] Integration tests: solve scrambled 4x4
- [ ] Integration tests: solve scrambled 5x5

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
