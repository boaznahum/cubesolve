# Issue: Consistent Framework for Face-to-Face Navigation

## Background: Insights from Issue #53

This issue builds on the learnings from Issue #53 "Two edges may not agree in face coordinate system".

### Key Insight: Approach 2

The breakthrough understanding was:

> **Each face's ltr is consistent BY DEFINITION. Edges provide a translation layer.**

- Face ltr coordinates are face-owned, not edge-owned
- The edge's internal storage arbitrarily matches f1's perspective
- f2 translates through the edge (inverts if `same_direction=False`)
- No "agreement check" is needed - consistency is guaranteed by the translation layer

### Critical Discovery: M vs S Slice Behavior

**M Slice: NO Axis Exchange**
- Uses only horizontal edges: `edge_bottom` → `edge_top` on each face
- Stays as **COLUMN** on all 4 faces (F → U → B → D)
- Path: F(edge_bottom) → U(edge_bottom) → B(edge_top) → D(edge_bottom)

**S Slice: HAS Axis Exchange**
- Alternates between vertical and horizontal edges
- Switches between **ROW** and **COLUMN**:
  - U: ROW (vertical edge L-U)
  - R: COLUMN (horizontal edge U-R)
  - D: ROW (vertical edge D-R)
  - L: COLUMN (horizontal edge L-D)

### The Axis Rule

```
Horizontal edge (top/bottom) → ltr selects COLUMN
Vertical edge (left/right)   → ltr selects ROW
```

---

## Problem Statement

Currently, navigating between faces during slice rotations involves multiple concepts that are handled separately:
- Edge translation (ltr ↔ slice index)
- Axis exchange (ROW ↔ COLUMN)
- Physical alignment preservation
- `same_direction` flag handling

These are spread across `Edge.py`, `Face.py`, and `Slice.py` without a unified conceptual framework.

## Current Implementation

### Slice.py (lines 63-134)
Each slice type (M, E, S) has hardcoded starting face and edge:
```python
case SliceName.M:
    current_face = self.cube.front
    current_edge = current_face.edge_bottom

case SliceName.E:
    current_face = self.cube.right
    current_edge = current_face.edge_left

case SliceName.S:
    current_face = self.cube.up
    current_edge = current_face.edge_left
```

### Navigation Logic (Slice.py lines 126-134)
```python
next_edge = current_edge.opposite(current_face)
next_face = next_edge.get_other_face(current_face)

# Translate coordinates through edge
next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)
```

### Axis Detection (Slice.py lines 98-108)
```python
if current_face.is_bottom_or_top(current_edge):
    # Horizontal edge → ltr selects COLUMN
    _c = [center.get_center_slice((i, current_index)) for i in range(n_slices)]
else:
    # Vertical edge → ltr selects ROW
    _c = [center.get_center_slice((current_index, i)) for i in range(n_slices)]
```

## Proposed Framework

### 0. Central Coordinate Translation API

**Goal:** A single entry point for ALL face-to-face coordinate operations.

```python
class FaceCoordinateTranslator:
    """
    Central API for translating coordinates between faces.

    This is the ONE place that handles:
    - Adjacent face navigation (share an edge)
    - Non-adjacent face navigation (opposite faces)
    - Coordinate transformation with axis exchange
    - Rotation direction to reach destination
    """

    def translate_coordinate(
        self,
        source_face: Face,
        dest_face: Face,
        source_coord: tuple[int, int],  # (row, col) on source face
        cube_size: int
    ) -> FaceTranslationResult:
        """
        Translate a coordinate from source_face to dest_face.

        Args:
            source_face: The face where the piece currently is
            dest_face: The face where we want to find the piece
            source_coord: (row, col) position on source_face
            cube_size: Size of cube (3 for 3x3, 5 for 5x5, etc.)

        Returns:
            FaceTranslationResult containing:
            - dest_coord: (row, col) on destination face
            - shared_edge: Edge connecting the faces (if adjacent)
            - rotation_face: Which face to rotate to move piece
            - rotation_direction: CW or CCW to reach destination
            - reverse_direction: Direction to go back
            - is_adjacent: True if faces share an edge
            - axis_exchange: True if ROW↔COLUMN swap occurred
        """
        pass

    def get_slice_path(
        self,
        source_face: Face,
        dest_face: Face,
        source_coord: tuple[int, int],
        direction: RotationDirection  # CW or CCW
    ) -> list[FaceCoordinate]:
        """
        Get the complete path a slice takes from source to destination.

        Returns list of (face, row, col) for each face the slice passes through.
        Useful for visualizing or validating slice movements.
        """
        pass


@dataclass
class FaceTranslationResult:
    """Result of translating a coordinate between faces."""

    # The destination coordinate
    dest_coord: tuple[int, int]  # (row, col) on dest_face

    # Navigation information
    shared_edge: Edge | None      # None if non-adjacent (opposite faces)
    is_adjacent: bool             # True if faces share an edge

    # Rotation to reach destination
    rotation_face: Face           # Which face's rotation moves the piece
    rotation_direction: RotationDirection  # CW or CCW
    rotation_count: int           # Number of 90° turns (1, 2, or 3)

    # Reverse path
    reverse_direction: RotationDirection   # Direction to go back
    reverse_rotation_face: Face            # Face to rotate to go back

    # Axis information
    axis_exchange: bool           # True if ROW↔COLUMN swap occurred
    source_axis: Axis             # ROW or COLUMN on source
    dest_axis: Axis               # ROW or COLUMN on destination

    # LTR translation details
    source_ltr: int               # LTR index on source edge
    dest_ltr: int                 # LTR index on dest edge
```

### Navigation Cases

```
┌─────────────────────────────────────────────────────────────────┐
│                    FACE RELATIONSHIP MATRIX                      │
├─────────┬───────┬───────┬───────┬───────┬───────┬───────────────┤
│ From\To │   F   │   U   │   R   │   B   │   D   │       L       │
├─────────┼───────┼───────┼───────┼───────┼───────┼───────────────┤
│    F    │   -   │  adj  │  adj  │  opp  │  adj  │      adj      │
│    U    │  adj  │   -   │  adj  │  adj  │  opp  │      adj      │
│    R    │  adj  │  adj  │   -   │  adj  │  adj  │      opp      │
│    B    │  opp  │  adj  │  adj  │   -   │  adj  │      adj      │
│    D    │  adj  │  opp  │  adj  │  adj  │   -   │      adj      │
│    L    │  adj  │  adj  │  opp  │  adj  │  adj  │       -       │
└─────────┴───────┴───────┴───────┴───────┴───────┴───────────────┘

adj = adjacent (share edge, 1 rotation)
opp = opposite (no shared edge, need 2 rotations)
```

### Algorithm for Adjacent Faces

```python
def _translate_adjacent(self, source: Face, dest: Face, coord: tuple[int, int]) -> FaceTranslationResult:
    """
    For adjacent faces (share an edge):

    1. Find shared edge between source and dest
    2. Determine edge type on each face:
       - source_edge_type: TOP/BOTTOM/LEFT/RIGHT on source
       - dest_edge_type: TOP/BOTTOM/LEFT/RIGHT on dest
    3. Calculate rotation face (the face whose rotation moves the edge)
    4. Apply axis rule:
       - Horizontal edge → COLUMN (ltr selects column)
       - Vertical edge → ROW (ltr selects row)
    5. Translate coordinate through edge:
       - source coord → source ltr → edge internal → dest ltr → dest coord
    """
    shared_edge = self._find_shared_edge(source, dest)

    # Determine which edge this is on each face
    source_edge_pos = source.get_edge_position(shared_edge)  # TOP/BOTTOM/LEFT/RIGHT
    dest_edge_pos = dest.get_edge_position(shared_edge)

    # Apply axis rule
    source_axis = COLUMN if source_edge_pos in (TOP, BOTTOM) else ROW
    dest_axis = COLUMN if dest_edge_pos in (TOP, BOTTOM) else ROW

    # Extract coordinate along the edge
    if source_axis == ROW:
        source_ltr = coord[1]  # column index for row selection
    else:
        source_ltr = coord[0]  # row index for column selection

    # Translate through edge
    edge_index = shared_edge.get_slice_index_from_ltr_index(source, source_ltr)
    dest_ltr = shared_edge.get_ltr_index_from_slice_index(dest, edge_index)

    # Build destination coordinate
    # ... (depends on dest_edge_pos and dest_axis)
```

### Algorithm for Opposite Faces

```python
def _translate_opposite(self, source: Face, dest: Face, coord: tuple[int, int]) -> FaceTranslationResult:
    """
    For opposite faces (F↔B, U↔D, L↔R):

    1. Find intermediate face (any adjacent to both)
    2. Translate source → intermediate
    3. Translate intermediate → dest
    4. Combine transformations

    Note: Requires 2 rotations (180° total through intermediate)
    """
    # Find a face adjacent to both source and dest
    intermediate = self._find_intermediate_face(source, dest)

    # Two-step translation
    step1 = self._translate_adjacent(source, intermediate, coord)
    step2 = self._translate_adjacent(intermediate, dest, step1.dest_coord)

    # Combine results
    return FaceTranslationResult(
        dest_coord=step2.dest_coord,
        is_adjacent=False,
        rotation_count=2,
        # ...
    )
```

### 1. Navigation Context Object

Create a `FaceNavigationContext` that encapsulates:
```python
@dataclass
class FaceNavigationContext:
    face: Face
    entry_edge: Edge          # Edge we entered through
    exit_edge: Edge           # Edge we'll exit through (opposite)
    axis: Axis                # ROW or COLUMN on this face
    ltr_index: int            # Current position in ltr coordinates

    def navigate_to_next(self) -> 'FaceNavigationContext':
        """Create context for next face in rotation."""
        ...
```

### 2. Axis Determination Rule

Formalize the rule:
- **Horizontal edge** (top/bottom) → slice is a **COLUMN** (ltr selects which column)
- **Vertical edge** (left/right) → slice is a **ROW** (ltr selects which row)

### 3. Slice Path Definition

Define each slice's path declaratively:
```python
SLICE_PATHS = {
    SliceName.M: SlicePath(
        start_face='F',
        start_edge='bottom',
        direction='clockwise',  # F→U→B→D
        edge_type='horizontal'  # Always horizontal → always COLUMN
    ),
    SliceName.S: SlicePath(
        start_face='U',
        start_edge='left',
        direction='clockwise',  # U→R→D→L
        edge_type='alternating'  # vertical→horizontal→vertical→horizontal
    ),
    ...
}
```

### 4. Unified Translation Interface

```python
class FaceToFaceTranslator:
    """Handles all face-to-face coordinate translation."""

    def translate(self,
                  from_face: Face,
                  to_face: Face,
                  through_edge: Edge,
                  ltr_index: int) -> tuple[int, Axis]:
        """
        Returns (new_ltr_index, new_axis) for the destination face.
        """
        ...
```

## Benefits

1. **Single source of truth** for navigation rules
2. **Easier debugging** - can trace navigation step by step
3. **Extensible** - easy to add new slice types or custom rotations
4. **Testable** - can unit test navigation logic independently
5. **Documentation** - framework serves as executable documentation

## Related Files

### Source Code
- `src/cube/domain/model/Slice.py` - Main slice rotation logic (lines 63-134)
- `src/cube/domain/model/Edge.py` - Edge translation methods (`get_ltr_index_from_slice_index`, `get_slice_index_from_ltr_index`)
- `src/cube/domain/model/Face.py` - Face edge relationships and rotation

### Documentation Created in Issue #53
- `docs/design2/edge-face-coordinate-system-approach2.md` - **Main documentation** for Approach 2
  - Face rotation with ltr coordinates
  - Slice rotation physical alignment
  - Axis exchange explanation (S slice)
  - `same_direction` flag determination

### Diagrams
All diagrams in `docs/design2/images/`:

| Diagram | Description |
|---------|-------------|
| `edge-coordinate-system.png` | Unfolded cube with R/T arrows and **ltr numbering (0→1→2)** on each edge |
| `face-rotation-ltr.png` | Face rotation showing ltr coordinate flow |
| `slice-rotation-axis-exchange.png` | **S slice** ROW↔COLUMN axis exchange (U→R) |
| `slice-physical-alignment.png` | Physical alignment across 4 faces |

### Diagram Generation Scripts
- `scripts/generate_edge_diagram.py` - Generates edge-coordinate-system.png
- `scripts/generate_ltr_diagrams.py` - Generates face-rotation and slice-rotation diagrams

### Hand-drawn Reference
- `images/right-top-left-coordinates.jpg` - Original hand-drawn R/T coordinate system

## Related Issues

- Issue #53: Two edges may not agree in face coordinate system (**CLOSED**)
  - Proved original approach geometrically impossible
  - Established Approach 2 as correct understanding
  - Removed obsolete `_validate_edge_coordinate_consistency` method
  - Deleted obsolete test `tests/model/test_edge_coordinate_consistency.py`

## Tasks

- [ ] Design `FaceNavigationContext` class
- [ ] Design `SlicePath` declarative definition
- [ ] Implement `FaceCoordinateTranslator` (central API)
- [ ] Implement `FaceTranslationResult` dataclass
- [ ] Refactor `Slice._get_slices_by_index()` to use new framework
- [ ] Add comprehensive unit tests for navigation
- [ ] Update documentation with framework description

---

## Comprehensive Test Design

### Test Strategy: Prove ALL Combinations Work

```python
class TestFaceCoordinateTranslator:
    """
    Comprehensive tests proving all face-to-face translations work correctly.

    Test Matrix:
    - 6 faces × 6 faces = 36 combinations (30 non-self)
    - Each combination tested with multiple coordinates
    - Both directions tested (forward and reverse)
    - All cube sizes (3×3, 4×4, 5×5)
    """

    # All 30 face pairs (excluding self-to-self)
    ALL_FACE_PAIRS = [
        (F, U), (F, R), (F, D), (F, L), (F, B),  # From F
        (U, F), (U, R), (U, B), (U, L), (U, D),  # From U
        (R, F), (R, U), (R, B), (R, D), (R, L),  # From R
        (B, U), (B, R), (B, D), (B, L), (B, F),  # From B
        (D, F), (D, R), (D, B), (D, L), (D, U),  # From D
        (L, F), (L, U), (L, B), (L, D), (L, R),  # From L
    ]

    # Adjacent pairs (24 total - each face has 4 neighbors)
    ADJACENT_PAIRS = [
        (F, U), (F, R), (F, D), (F, L),
        (U, F), (U, R), (U, B), (U, L),
        (R, F), (R, U), (R, B), (R, D),
        (B, U), (B, R), (B, D), (B, L),
        (D, F), (D, R), (D, B), (D, L),
        (L, F), (L, U), (L, B), (L, D),
    ]

    # Opposite pairs (6 total)
    OPPOSITE_PAIRS = [
        (F, B), (B, F),
        (U, D), (D, U),
        (L, R), (R, L),
    ]
```

### Test 1: All Adjacent Face Translations

```python
@pytest.mark.parametrize("source,dest", ADJACENT_PAIRS)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_adjacent_face_translation(self, source, dest, cube_size):
    """
    For each adjacent face pair:
    1. Translate corner coordinates (0,0), (0,n-1), (n-1,0), (n-1,n-1)
    2. Translate edge midpoints
    3. Translate center (for odd-sized cubes)
    4. Verify reverse translation returns to original
    """
    translator = FaceCoordinateTranslator()
    n = cube_size

    # Test coordinates: corners, edge midpoints, center
    test_coords = [
        (0, 0), (0, n-1), (n-1, 0), (n-1, n-1),  # corners
        (0, n//2), (n-1, n//2), (n//2, 0), (n//2, n-1),  # edge midpoints
        (n//2, n//2),  # center
    ]

    for coord in test_coords:
        # Forward translation
        result = translator.translate_coordinate(source, dest, coord, cube_size)

        # Verify result is valid
        assert 0 <= result.dest_coord[0] < n
        assert 0 <= result.dest_coord[1] < n
        assert result.is_adjacent == True
        assert result.shared_edge is not None

        # Reverse translation should return to original
        reverse = translator.translate_coordinate(dest, source, result.dest_coord, cube_size)
        assert reverse.dest_coord == coord, f"Round-trip failed: {coord} → {result.dest_coord} → {reverse.dest_coord}"
```

### Test 2: All Opposite Face Translations

```python
@pytest.mark.parametrize("source,dest", OPPOSITE_PAIRS)
@pytest.mark.parametrize("cube_size", [3, 4, 5])
def test_opposite_face_translation(self, source, dest, cube_size):
    """
    For each opposite face pair:
    1. Verify translation requires 2 rotations
    2. Verify is_adjacent == False
    3. Verify round-trip works
    """
    translator = FaceCoordinateTranslator()
    n = cube_size

    for row in range(n):
        for col in range(n):
            coord = (row, col)
            result = translator.translate_coordinate(source, dest, coord, cube_size)

            assert result.is_adjacent == False
            assert result.rotation_count == 2
            assert result.shared_edge is None

            # Round-trip
            reverse = translator.translate_coordinate(dest, source, result.dest_coord, cube_size)
            assert reverse.dest_coord == coord
```

### Test 3: Axis Exchange Verification

```python
@pytest.mark.parametrize("source,dest", ADJACENT_PAIRS)
def test_axis_exchange_correctness(self, source, dest):
    """
    Verify axis exchange follows the rule:
    - Horizontal edge (top/bottom) → COLUMN
    - Vertical edge (left/right) → ROW
    """
    translator = FaceCoordinateTranslator()

    result = translator.translate_coordinate(source, dest, (1, 1), cube_size=3)

    # Get edge positions
    shared_edge = result.shared_edge
    source_edge_pos = source.get_edge_position(shared_edge)
    dest_edge_pos = dest.get_edge_position(shared_edge)

    # Verify axis rule
    expected_source_axis = COLUMN if source_edge_pos in (TOP, BOTTOM) else ROW
    expected_dest_axis = COLUMN if dest_edge_pos in (TOP, BOTTOM) else ROW

    assert result.source_axis == expected_source_axis
    assert result.dest_axis == expected_dest_axis
    assert result.axis_exchange == (expected_source_axis != expected_dest_axis)
```

### Test 4: Rotation Direction Verification

```python
@pytest.mark.parametrize("source,dest", ADJACENT_PAIRS)
def test_rotation_direction(self, source, dest):
    """
    Verify that applying the rotation actually moves the piece.

    1. Get translation result with rotation direction
    2. Create actual cube
    3. Place marker at source coord
    4. Apply rotation
    5. Verify marker is at dest coord
    """
    cube = Cube(3)
    translator = FaceCoordinateTranslator()

    coord = (1, 1)  # center of 3x3
    result = translator.translate_coordinate(source, dest, coord, cube_size=3)

    # Mark the source position
    original_color = source.get_color(coord)

    # Apply the rotation
    result.rotation_face.rotate(
        direction=result.rotation_direction,
        count=result.rotation_count
    )

    # Verify piece moved to destination
    new_color = dest.get_color(result.dest_coord)
    assert new_color == original_color
```

### Test 5: Slice Path Completeness

```python
def test_slice_path_covers_all_four_faces(self):
    """
    For M, E, S slices, verify the path visits exactly 4 faces.
    """
    translator = FaceCoordinateTranslator()

    # M slice: F → U → B → D
    path = translator.get_slice_path(F, F, (1, 1), direction=CW)
    faces_visited = [p.face for p in path]
    assert len(faces_visited) == 4
    assert set(faces_visited) == {F, U, B, D}

    # S slice: U → R → D → L
    path = translator.get_slice_path(U, U, (1, 1), direction=CW)
    faces_visited = [p.face for p in path]
    assert len(faces_visited) == 4
    assert set(faces_visited) == {U, R, D, L}

    # E slice: F → R → B → L
    path = translator.get_slice_path(F, F, (1, 1), direction=CW)
    faces_visited = [p.face for p in path]
    assert len(faces_visited) == 4
```

### Test 6: Physical Alignment Preservation

```python
@pytest.mark.parametrize("cube_size", [3, 5, 7])
def test_physical_alignment(self, cube_size):
    """
    Verify that a visual line stays aligned across face transitions.

    1. Take a column on Face F
    2. Follow it through U, B, D
    3. All coordinates should form a continuous physical line
    """
    translator = FaceCoordinateTranslator()

    # Middle column on F
    column_idx = cube_size // 2
    f_coords = [(row, column_idx) for row in range(cube_size)]

    # Translate to U
    u_coords = [translator.translate_coordinate(F, U, c, cube_size).dest_coord for c in f_coords]

    # Verify U coords form a valid line (all same row or all same column)
    u_rows = set(c[0] for c in u_coords)
    u_cols = set(c[1] for c in u_coords)
    assert len(u_rows) == 1 or len(u_cols) == 1, "Translated coords don't form a line on U"
```

### Test 7: Exhaustive Combination Test

```python
def test_all_combinations_exhaustive(self):
    """
    THE ULTIMATE TEST: Verify every single coordinate on every face
    can be translated to every other face and back.

    Total tests: 6 faces × 5 destinations × 9 coords (3×3) = 270 translations
    """
    translator = FaceCoordinateTranslator()
    faces = [F, U, R, B, D, L]
    cube_size = 3
    failures = []

    for source in faces:
        for dest in faces:
            if source == dest:
                continue

            for row in range(cube_size):
                for col in range(cube_size):
                    coord = (row, col)
                    try:
                        # Forward
                        result = translator.translate_coordinate(source, dest, coord, cube_size)

                        # Validate result
                        assert 0 <= result.dest_coord[0] < cube_size
                        assert 0 <= result.dest_coord[1] < cube_size

                        # Reverse
                        reverse = translator.translate_coordinate(dest, source, result.dest_coord, cube_size)
                        assert reverse.dest_coord == coord

                    except AssertionError as e:
                        failures.append(f"{source}→{dest} coord={coord}: {e}")

    assert not failures, f"Failed translations:\n" + "\n".join(failures)
```

### Running the Tests

```bash
# Run all face-to-face navigation tests
pytest tests/model/test_face_coordinate_translator.py -v

# Run with coverage
pytest tests/model/test_face_coordinate_translator.py --cov=src/cube/domain/model

# Run specific test
pytest tests/model/test_face_coordinate_translator.py::TestFaceCoordinateTranslator::test_all_combinations_exhaustive -v
```

---

## Session Summary (Issue #53 Resolution)

### What Was Done
1. Analyzed original assumption that opposite edges must "agree" - proved **geometrically impossible**
2. Established **Approach 2**: Face ltr is consistent by definition, edges translate
3. Documented 7 usage cases of ltr methods - all match Approach 2
4. Created comprehensive documentation with ASCII and graphical diagrams
5. Fixed axis exchange diagram: changed from M slice (wrong) to S slice (correct)
6. Added ltr numbering (0→1→2) to edge-coordinate-system.png
7. Removed obsolete validation code and tests

### Key Code Locations
- Edge translation: `Edge.py:127-191`
- Slice navigation: `Slice.py:112-134`
- Axis detection: `Slice.py:98-108`
