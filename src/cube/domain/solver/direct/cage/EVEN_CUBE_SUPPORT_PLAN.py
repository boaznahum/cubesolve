"""
EVEN CUBE SUPPORT FOR CAGE SOLVER - ANALYSIS AND IMPLEMENTATION PLAN
====================================================================

This document analyzes how to support even cubes (4x4, 6x6, 8x8) in the Cage solver,
following the same approach we used for even cube support in the Beginner reducer.

TABLE OF CONTENTS:
1. Current State Analysis
2. Key Challenge: No Fixed Center on Even Cubes
3. FaceTracker: The Key Mechanism
4. Implementation Plan (Edges -> Cage -> Centers)
5. Step-by-Step Implementation Details

================================================================================
1. CURRENT STATE ANALYSIS
================================================================================

BEGINNER REDUCER (already supports even cubes):
----------------------------------------------
Order: Centers -> Edges -> 3x3 solve
- Centers: NxNCentersV3 uses FaceTracker for even cubes
- Edges: NxNEdges uses majority color (no center reference needed)
- 3x3: Detects parity via exceptions, fixes and retries

CAGE SOLVER (only supports odd cubes):
-------------------------------------
Order: Edges -> Corners -> Centers
- Edges: NxNEdges - ALREADY SUPPORTS EVEN CUBES
- Corners: 3x3 solver - FAILS ON EVEN CUBES (uses face.center.color)
- Centers: NxNCentersV3 - ALREADY SUPPORTS EVEN CUBES

CONCLUSION:
----------
The ONLY blocker for even cube support is Phase 1b (corner solving).
The 3x3 solver uses face.center.color to determine which color each face should be,
but even cubes have NO fixed center - all centers are scrambled after Phase 1a.

================================================================================
2. KEY CHALLENGE: NO FIXED CENTER ON EVEN CUBES
================================================================================

ODD CUBE (5x5):
--------------
- Center grid is 3x3, middle piece (1,1) is THE center
- face.center.color returns THIS piece's color
- 3x3 solver knows: "Front face should be BLUE" because center IS blue

EVEN CUBE (4x4):
---------------
- Center grid is 2x2, NO middle piece
- face.center.color returns... what? (implementation-dependent, but WRONG)
- 3x3 solver doesn't know which color each face should be!

THE PROBLEM IN DETAIL:
---------------------
After Phase 1a (edges solved):
  - Corners: Scrambled, need to be positioned
  - Centers: Scrambled (4+ pieces per face, mixed colors)

When 3x3 solver runs:
  - It looks at face.center.color to decide where corners go
  - Example: "This corner has white, it should go to the face with white center"
  - But on 4x4, which face IS the white face? Centers are scrambled!

================================================================================
3. FACETRACKER: THE KEY MECHANISM
================================================================================

FaceTracker solves the "which face should be which color" problem.

HOW IT WORKS:
------------
1. Put a MARKER on a center piece (using c_attributes dictionary)
2. Define a predicate that finds where that marker is
3. The predicate searches ALL faces for the marker

From FaceTracker.py:
```python
@staticmethod
def by_center_piece(_slice: CenterSlice) -> FaceTracker:
    # Put marker on the slice's edge (sticker)
    key = _TRACKER_KEY_PREFIX + str(_slice.color) + str(unique_id)
    edge = _slice.edge
    edge.c_attributes[key] = True  # <-- THE MARKER

    # Create predicate that finds this marker
    def _slice_pred(s: CenterSlice):
        return key in s.edge.c_attributes

    def _face_pred(_f: Face):
        return _f.cube.cqr.find_slice_in_face_center(_f, _slice_pred) is not None

    return FaceTracker(color, _face_pred)
```

USAGE PATTERN (from NxNCentersV3):
---------------------------------
For even cubes, establish 6 face trackers that form a valid BOY layout:

```python
# Step 1: Find face with most pieces of any color -> Track it
f1: FaceTracker = self._trackers.track_no_1()  # Uses _find_face_with_max_colors()

# Step 2: Track opposite face
f2 = f1.track_opposite()

# Step 3: Find third face (respects BOY orientation)
f3 = self._trackers._track_no_3([f1, f2])
f4 = f3.track_opposite()

# Step 4: Last two faces (must form valid BOY)
f5, f6 = self._trackers._track_two_last([f1, f2, f3, f4])
```

KEY INSIGHT:
-----------
FaceTracker.face PROPERTY dynamically searches for the marker!
So even after cube rotations, tracker.face returns the CURRENT face where the marker is.

================================================================================
4. IMPLEMENTATION PLAN: EDGES -> CAGE -> CENTERS
================================================================================

Following the same order as beginner reducer even cube support:

PHASE 1: EDGE SUPPORT (ALREADY DONE!)
------------------------------------
NxNEdges already handles even cubes:
- Line 124-130: If even cube, uses _find_max_of_color() instead of middle slice
- Parity detection works (1 edge left = parity)
- Parity fix works (M-slice or R/L-slice algorithms)

STATUS: COMPLETE - No changes needed

PHASE 2: CAGE (CORNER) SUPPORT (THIS IS THE WORK)
------------------------------------------------
Problem: 3x3 solver uses face.center.color which doesn't exist on even cubes

SOLUTION OPTIONS:

Option A: Establish FaceTrackers BEFORE corner solving
--------------------------------------------------------
1. After edge solving, create FaceTrackers for all 6 faces
2. Store face->color mapping: {Face: Color}
3. Pass this mapping to 3x3 solver (requires new parameter/protocol)
4. 3x3 solver uses mapping instead of face.center.color

Pros: Clean separation, 3x3 solver stays pure
Cons: Major API change to 3x3 solver protocol

Option B: Solve ONE center face first to establish reference
------------------------------------------------------------
1. After edge solving, use NxNCentersV3 to solve JUST the white face centers
2. Now face.center.color works for white face
3. 3x3 solver can start L1 (white face is reference)
4. Problem: L2/L3 still need other face colors!

Pros: Minimal change to 3x3 solver
Cons: Solving one face breaks "cage first" philosophy

Option C: Create CubeColorMapping that 3x3 solver queries (RECOMMENDED)
----------------------------------------------------------------------
1. Create new component: CageFaceColorMapper
2. After edge solving, establish FaceTrackers (like NxNCentersV3 does)
3. Store in cube or pass to 3x3 solver
4. Modify 3x3 solver to accept optional color mapper
5. If mapper exists, use mapper.get_face_color(face) instead of face.center.color

Pros: Clean, explicit, testable
Cons: Requires changes to multiple files

Option D: Modify Face class to support "virtual color" (SIMPLEST)
----------------------------------------------------------------
1. Add Face.virtual_color property (optional, defaults to center.color)
2. Before corner solving, set virtual_color on each face based on FaceTrackers
3. 3x3 solver already works IF we modify its color lookups

Pros: Minimal API changes
Cons: Adds state to Face class

RECOMMENDATION: Option C or D - both are clean and follow existing patterns.

PHASE 3: CENTER SUPPORT (ALREADY DONE!)
--------------------------------------
NxNCentersV3 already handles even cubes:
- Line 302-331: Even cube branch uses FaceTracker system
- preserve_3x3_state=True already implemented for cage method
- Commutators preserve paired edges and solved corners

STATUS: COMPLETE - No changes needed

================================================================================
5. STEP-BY-STEP IMPLEMENTATION DETAILS
================================================================================

STEP 1: CREATE CageFaceColorMapper (new file)
--------------------------------------------
Location: src/cube/domain/solver/direct/cage/CageFaceColorMapper.py

```python
class CageFaceColorMapper:
    '''
    Establishes face->color mapping for even cubes where no fixed center exists.
    Uses FaceTracker mechanism from NxNCentersV3.
    '''

    def __init__(self, cube: Cube) -> None:
        self._cube = cube
        self._face_colors: dict[Face, Color] = {}
        self._trackers: list[FaceTracker] = []

        # Only needed for even cubes
        if cube.n_slices % 2 == 0:
            self._establish_mapping()

    def _establish_mapping(self) -> None:
        '''Create FaceTrackers and map Face -> Color'''
        trackers = NxNCentersFaceTrackers(self._solver_provider)

        f1 = trackers.track_no_1()
        f2 = f1.track_opposite()
        f3 = trackers._track_no_3([f1, f2])
        f4 = f3.track_opposite()
        f5, f6 = trackers._track_two_last([f1, f2, f3, f4])

        self._trackers = [f1, f2, f3, f4, f5, f6]

        # Build mapping
        for tracker in self._trackers:
            self._face_colors[tracker.face] = tracker.color

    def get_face_color(self, face: Face) -> Color:
        '''Get the color this face SHOULD be (for corner solving)'''
        if self._cube.n_slices % 2:
            # Odd cube - use actual center
            return face.center.color
        else:
            # Even cube - use established mapping
            return self._face_colors[face]

    def refresh_mapping(self) -> None:
        '''Refresh after cube rotations (tracker.face may have changed)'''
        self._face_colors.clear()
        for tracker in self._trackers:
            self._face_colors[tracker.face] = tracker.color
```

STEP 2: MODIFY CageNxNSolver
---------------------------
Location: src/cube/domain/solver/direct/cage/CageNxNSolver.py

Changes:
1. Create CageFaceColorMapper after edge solving
2. Pass mapper to 3x3 solver (or store for solver to query)

```python
def _solve_impl(self, sr: SolverResults) -> SolverResults:
    # Phase 1a: Edge Solving (unchanged)
    if not self._are_edges_solved():
        had_parity = self._solve_edges()

    # NEW: Establish face color mapping for even cubes
    if self._cube.n_slices % 2 == 0:
        self._face_mapper = CageFaceColorMapper(self._cube)
        # Store on cube or pass to solver

    # Phase 1b: Corner Solving
    if not self._cube.solved:
        self._solve_corners()  # Needs to use mapper

    # Phase 2: Center Solving (unchanged)
    ...
```

STEP 3: MODIFY 3x3 SOLVER COLOR LOOKUPS
--------------------------------------
Location: Multiple files in src/cube/domain/solver/beginner/

Need to find all uses of face.center.color in:
- L1Cross.py - Finding white face, positioning edges
- L1Corners.py - Finding white corners
- L2.py - Middle layer edges
- L3Cross.py - Yellow face cross
- L3Corners.py - Yellow corners

Option: Create helper method that checks for mapper:
```python
def _get_face_target_color(self, face: Face) -> Color:
    '''Get the color this face should be'''
    # Check if mapper exists (even cube in cage mode)
    mapper = getattr(self.cube, '_face_color_mapper', None)
    if mapper:
        return mapper.get_face_color(face)
    # Default: use center color (odd cube or after centers solved)
    return face.center.color
```

STEP 4: HANDLE EVEN CUBE PARITY
------------------------------
Even cubes can have edge parity and corner parity.
Current handling in NxNSolverOrchestrator:
- Catches EvenCubeEdgeParityException from L3Cross
- Catches EvenCubeCornerSwapException from L3Corners
- Fixes parity and re-reduces

For Cage solver:
- Same exceptions will be thrown
- Need to catch and handle in CageNxNSolver._solve_corners()
- After fix, re-run edge pairing (might disturb some edges)

```python
def _solve_corners(self) -> None:
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            self._solver_3x3.solve_3x3()
            break
        except EvenCubeEdgeParityException:
            self._handle_edge_parity()
            # Re-pair edges, re-establish mapper
            self._solve_edges()
            self._face_mapper.refresh_mapping()
        except EvenCubeCornerSwapException:
            self._handle_corner_parity()
            # May need to re-pair some edges
```

STEP 5: UPDATE SOLVERNAME TO ALLOW EVEN CUBES
--------------------------------------------
Location: src/cube/domain/solver/SolverName.py

Current:
```python
CAGE = SolverMeta("Cage", skip_even="Cage method only supports odd cubes")
```

After implementation:
```python
CAGE = SolverMeta("Cage")  # Remove skip_even
```

STEP 6: ADD TESTS
----------------
Location: tests/solvers/test_cage_solver.py

Add tests for:
- 4x4 scramble and solve
- 6x6 scramble and solve
- Parity detection on even cubes
- FaceColorMapper correctness

================================================================================
SUMMARY: IMPLEMENTATION ORDER
================================================================================

1. EDGES - DONE (NxNEdges already supports even cubes)

2. CAGE (CORNERS) - TODO:
   a. Create CageFaceColorMapper class
   b. Integrate with CageNxNSolver
   c. Modify 3x3 solver to use mapper for face colors
   d. Add parity exception handling to CageNxNSolver

3. CENTERS - DONE (NxNCentersV3 with preserve_3x3_state=True already works)

4. FINAL:
   a. Remove skip_even from SolverName.CAGE
   b. Add even cube tests
   c. Update documentation

================================================================================
"""

# This file is documentation-as-code. No executable code.
# See the implementation in other files once this plan is approved.
