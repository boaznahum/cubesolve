# Cage Method Solver - Design Document

## Critical Design Constraints

### 1. STATELESS SOLVER

The solver must be **completely stateless**. It must be able to continue any
interrupted operation by **inspecting the cube state only**.

```
WRONG:
    class Solver:
        self._current_phase = "edges"   # ❌ Internal state
        self._solved_count = 5          # ❌ Internal state

RIGHT:
    class Solver:
        def _are_edges_solved(self):
            return all(e.is3x3 for e in cube.edges)  # ✅ Inspect cube

        def _are_centers_solved(self):
            return all(f.center.is3x3 for f in cube.faces)  # ✅ Inspect cube
```

**Exception**: In rare cases, temporary markers can be placed ON THE CUBE
(using `c_attributes`), but they MUST be removed when done. See `FaceTracker`.

### 2. EVEN CUBE FACE COLOR PROBLEM

On **even cubes (4x4, 6x6, etc.)**, faces do NOT have a fixed color!

```
ODD cube (3x3, 5x5):
    - Center piece IS the face color
    - cube.front.color → always correct

EVEN cube (4x4, 6x6):
    - NO fixed center piece
    - Face "color" is UNDEFINED until we DECIDE it
    - Cannot say "the red face" or "white_face"
```

**Solution**: Use `FaceTracker` to track faces by:
1. Finding face with MAX pieces of a single color
2. Tracking that face/color pair
3. Building a valid "BOY" (standard color arrangement)

```python
# WRONG for even cubes:
target_color = face.center.color  # ❌ No fixed center!

# RIGHT for even cubes:
face, color = find_face_with_max_colors()  # ✅
tracker = FaceTracker.search_color_and_track(face, color)
```

---

## Cage Method Overview

```
Phase 1: BUILD THE CAGE
    Step 1a: Solve all EDGES (pair wings, place correctly)
    Step 1b: Solve all CORNERS (standard 3x3 methods)

Phase 2: FILL THE CAGE
    Step 2: Solve CENTERS using commutators
```

---

## Detailed Pseudo-Code

### Main Solve Flow

```
solve():
    # Check current state (STATELESS - inspect cube)
    if is_solved():
        return

    # Phase 1: Build the cage
    if not are_edges_solved():
        solve_edges()

    if not are_corners_solved():
        solve_corners()

    # Phase 2: Fill the cage
    if not are_centers_solved():
        solve_centers()
```

### State Inspection (Stateless)

```
are_edges_solved():
    # Check by inspecting cube, not internal state
    return all(edge.is3x3 for edge in cube.edges)

are_corners_solved():
    # All corners in correct position with correct orientation
    for corner in cube.corners:
        if not corner_is_solved(corner):
            return False
    return True

are_centers_solved():
    # All centers have uniform color
    return all(face.center.is3x3 for face in cube.faces)
```

---

### Phase 1a: Solve Edges

Edges can be solved similarly to reduction edge pairing,
but with MORE FREEDOM because centers don't matter yet.

```
solve_edges():
    """
    Pair all wings and place edges in correct positions.

    Key insight: We can use ANY slice moves freely because
    centers are solved LAST.
    """

    while not are_edges_solved():
        # Find an unsolved edge (STATELESS - inspect cube)
        edge = find_unsolved_edge()
        if edge is None:
            break

        # Solve this edge
        solve_single_edge(edge)

find_unsolved_edge():
    # Inspect cube to find work
    for edge in cube.edges:
        if not edge.is3x3:
            return edge
    return None

solve_single_edge(edge):
    # Bring edge to working position
    bring_edge_to_front_left(edge)
    edge = cube.front.edge_left

    # Get required colors for this position
    # NOTE: On even cubes, this requires careful handling!
    required_colors = determine_edge_colors(edge)

    # For each wing slice on this edge
    for wing_index in range(edge.n_slices):
        wing = edge.get_slice(wing_index)

        if wing_matches(wing, required_colors):
            continue  # Already correct

        # Find source wing with correct colors
        source = find_wing_with_colors(required_colors, exclude=edge)

        if source is not None:
            # Standard case: bring source and swap
            bring_to_front_right(source.parent)
            execute_wing_swap(wing_index)
        else:
            # Wing on same edge but flipped
            flip_wing_on_edge(edge, wing_index)
```

#### Even Cube Edge Color Determination

```
determine_edge_colors(edge):
    """
    Determine what colors this edge SHOULD have.

    For ODD cubes: Use adjacent face center colors
    For EVEN cubes: Use face trackers or majority color
    """

    face1, face2 = edge.faces

    if cube.n_slices % 2:  # ODD
        # Easy: center defines face color
        return (face1.center.color, face2.center.color)
    else:  # EVEN
        # Must determine from existing pieces or trackers
        # Option 1: Use tracked face colors (if solving centers first)
        # Option 2: Use majority color on adjacent centers

        color1 = get_dominant_color(face1.center)
        color2 = get_dominant_color(face2.center)
        return (color1, color2)

get_dominant_color(center):
    """Find the most common color on a center."""
    color_counts = {}
    for slice in center.all_slices:
        c = slice.color
        color_counts[c] = color_counts.get(c, 0) + 1
    return max(color_counts, key=color_counts.get)
```

---

### Phase 1b: Solve Corners

Corners are identical to 3x3 corners on any size cube.

```
solve_corners():
    """
    Solve all 8 corners using standard 3x3 methods.
    Can use F2L-style insertion or layer-by-layer.
    """

    # First: position corners (ignore orientation)
    while not all_corners_positioned():
        solve_corner_position()

    # Then: orient corners
    while not all_corners_oriented():
        solve_corner_orientation()

all_corners_positioned():
    # Check if each corner is in its correct position
    for corner in cube.corners:
        if not corner_in_correct_position(corner):
            return False
    return True

corner_in_correct_position(corner):
    """
    Check if corner's colors match its position.

    For EVEN cubes: Must use determined face colors!
    """
    corner_colors = corner.colors_id  # frozenset of 3 colors
    expected_colors = get_expected_corner_colors(corner.position)
    return corner_colors == expected_colors
```

---

### Phase 2: Solve Centers (Commutators)

This is the KEY phase of Cage Method. Since edges and corners
are solved, we can use commutators freely.

```
solve_centers():
    """
    Solve all centers using commutators.

    Since edges/corners are fixed, commutators only affect centers.

    For EVEN cubes: Must establish face color mapping first!
    """

    # For even cubes, determine face-color assignments
    if cube.n_slices % 2 == 0:
        face_colors = establish_face_color_mapping()
    else:
        face_colors = {f: f.center.color for f in cube.faces}

    # Solve each face
    for face in get_face_solving_order():
        target_color = face_colors[face]
        solve_face_centers(face, target_color)

establish_face_color_mapping():
    """
    For EVEN cubes: Determine which color each face should be.

    Strategy:
    1. Find face with most pieces of single color → assign that color
    2. Opposite face gets opposite color
    3. Repeat for remaining faces
    4. Validate it forms a valid BOY arrangement
    """

    mapping = {}
    used_colors = set()

    # First pair
    f1, c1 = find_face_with_max_colors(exclude_faces=[], exclude_colors=used_colors)
    mapping[f1] = c1
    mapping[f1.opposite] = get_opposite_color(c1)
    used_colors.add(c1)
    used_colors.add(get_opposite_color(c1))

    # Second pair
    remaining_faces = [f for f in cube.faces if f not in mapping]
    f3, c3 = find_face_with_max_colors(exclude_faces=mapping.keys(), exclude_colors=used_colors)
    mapping[f3] = c3
    mapping[f3.opposite] = get_opposite_color(c3)
    used_colors.add(c3)
    used_colors.add(get_opposite_color(c3))

    # Third pair (last 2 faces, last 2 colors)
    # Must check which assignment makes valid BOY
    ...

    return mapping

solve_face_centers(face, target_color):
    """Solve all center pieces on one face."""

    # Bring face to front for easier manipulation
    bring_face_to_front(face)
    face = cube.front

    # For each center position
    n = cube.n_slices - 2  # center size (excluding edges)
    for r in range(n):
        for c in range(n):
            solve_center_position(face, r, c, target_color)

solve_center_position(face, row, col, target_color):
    """Solve a single center position using commutators."""

    # Check current state (STATELESS)
    current = face.center.get_center_slice((row, col))
    if current.color == target_color:
        return  # Already correct

    # Find a piece of target_color elsewhere
    source = find_center_of_color(target_color, exclude_face=face)

    if source is None:
        # All target_color pieces are on this face but wrong position
        # Use internal swap commutator
        source = find_on_same_face(face, target_color, exclude=(row, col))
        execute_internal_swap_commutator(face, (row, col), source)
    else:
        # Standard case: piece on different face
        source_face, source_row, source_col = source
        execute_center_commutator(
            target_face=face, target_pos=(row, col),
            source_face=source_face, source_pos=(source_row, source_col)
        )
```

---

### Center Commutator Implementation

```
execute_center_commutator(target_face, target_pos, source_face, source_pos):
    """
    Execute commutator to cycle 3 center pieces.

    Pattern: [A, B] = A B A' B'
    Where:
        A = slice move (M/E/S depending on orientation)
        B = face rotation

    The commutator cycles:
        target_pos → buffer → source_pos → target_pos
    """

    # Setup: Orient cube so target is on front, source is accessible
    setup_moves = calculate_setup(target_face, source_face)
    execute(setup_moves)

    # Determine which slices to use
    target_col = target_pos[1]
    source_col = source_pos[1]

    # Commutator multiplier (1 for Up, 2 for Back)
    mul = 1 if source_is_up() else 2

    # The commutator sequence
    target_slice = Algs.M[target_col + 1]  # 1-indexed
    source_slice = Algs.M[source_col + 1]

    # Execute: [target_slice', F, source_slice', F'] pattern
    execute([
        target_slice.prime * mul,
        Algs.F,
        source_slice.prime * mul,
        Algs.F.prime,
        target_slice * mul,
        Algs.F,
        source_slice * mul,
        Algs.F.prime
    ])

    # Undo setup
    execute(inverse(setup_moves))
```

---

## Parity in Cage Method

### ANSWERED: Cage method DOES have parity issues on even cubes!

**For ODD cubes (5x5, 7x7):**
- Edge parity handled inside `NxNEdges.solve()` (partial edge parity)
- No corner/OLL/PLL parity issues

**For EVEN cubes (4x4, 6x6):**
Edge pairing can create "impossible" 3x3 states due to hidden parity:

1. **OLL Edge Parity**: 1 or 3 edges with wrong orientation
2. **PLL Corner Parity**: 2 corners need swap (diagonal)
3. **PLL Edge Swap Parity**: 2 edges need swap (impossible permutation)

**Root Cause**: On even cubes, edge wing slices have no fixed center reference.
When pairing edges, we choose which slice goes where. This choice affects
the final orientation and permutation parity of the "virtual 3x3".

**Solution**: Use **beginner solver** for even cube shadow cubes.
- CFOP solver detects parity and raises exceptions
- Attempting to fix parity, re-pair edges, and retry causes oscillation
- Beginner solver completes without detecting/raising parity exceptions
- The cube still ends up solved because beginner doesn't rely on parity checks

---

## Implementation Checklist

### Phase 1: Infrastructure - DONE
- [x] Create `CageNxNSolver` inheriting from `BaseSolver`
- [x] Implement state inspection methods (stateless)
- [x] Handle even cube face color determination via `FaceTracker`

### Phase 2: Edge Solving - DONE
- [x] Implement `solve_edges()` - reuses `NxNEdges` directly
- [x] Handle edge color determination for even cubes (via `NxNEdges._find_max_of_color`)
- [x] Reuse patterns from `NxNEdges` - entire class reused!
- [x] Edge parity handled by `NxNEdges._do_last_edge_parity()`

### Phase 3: Corner Solving - DONE
- [x] Shadow cube approach: build virtual 3x3, solve, apply moves
- [x] Odd cubes: use CFOP solver (configurable)
- [x] Even cubes: use beginner solver (avoids parity oscillation)
- [x] Face color mapping via `FaceTracker` for even cubes

### Phase 4: Center Solving - DONE
- [x] Implement `CageCenters` wrapping `NxNCenters`
- [x] Use face trackers from Phase 3 for color mapping
- [x] Preserves edges and corners

### Phase 5: Testing - DONE
- [x] Test on 4x4 (even, no fixed center) - 30 tests passing
- [x] Test on 5x5, 7x7 (odd, has fixed center)
- [x] Test on 6x6 (even, larger)
- [x] Test multiple scramble seeds

---

## References

- Existing reducer: `solver/reducers/BeginnerReducer.py`
- Face tracking: `solver/beginner/NxnCentersFaceTracker.py`
- Center solving patterns: `solver/beginner/NxNCenters.py`
- Edge solving patterns: `solver/beginner/NxNEdges.py`
