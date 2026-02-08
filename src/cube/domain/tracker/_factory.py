"""Face tracker creation for NxN center solving.

THE FACE TRACKING PROBLEM:
==========================

When solving centers on an NxN cube, we need to know which color belongs on each face.
This is trivial for ODD cubes (5x5, 7x7) but complex for EVEN cubes (4x4, 6x6).

ODD CUBES - SIMPLE CASE:
------------------------
Odd cubes have a FIXED center piece that never moves:

    ┌─┬─┬─┬─┬─┐
    │ │ │ │ │ │
    ├─┼─┼─┼─┼─┤
    │ │ │ │ │ │
    ├─┼─┼─┼─┼─┤
    │ │ │█│ │ │  <- Fixed center (always same color)
    ├─┼─┼─┼─┼─┤
    │ │ │ │ │ │
    ├─┼─┼─┼─┼─┤
    │ │ │ │ │ │
    └─┴─┴─┴─┴─┘

The face color IS the fixed center piece color. Simple!


EVEN CUBES - THE PROBLEM:
-------------------------
Even cubes have NO fixed center - all center pieces can move:

    ┌─┬─┬─┬─┐
    │?│?│?│?│
    ├─┼─┼─┼─┤
    │?│?│?│?│  <- No fixed center!
    ├─┼─┼─┼─┤     Which color belongs here?
    │?│?│?│?│
    ├─┼─┼─┼─┤
    │?│?│?│?│
    └─┴─┴─┴─┘

After scrambling, the front face might have pieces of ALL 6 colors!
How do we know which color SHOULD be on this face?


WHY MAJORITY COLOR?
===================

We use MAJORITY COLOR because statistically, a scrambled face is most likely
to have the most pieces of its "correct" color.

Example - 4x4 scrambled front face (should be RED):
    ┌─┬─┬─┬─┐
    │R│B│R│O│
    ├─┼─┼─┼─┤
    │R│R│G│R│   Count: R=7, B=2, O=2, G=2, W=2, Y=1
    ├─┼─┼─┼─┤          ^^^
    │W│R│R│Y│   RED is majority -> this face should be RED
    ├─┼─┼─┼─┤
    │O│B│W│G│
    └─┴─┴─┴─┘

This heuristic works because:
1. A random scramble distributes ~16 pieces of each color across 6 faces
2. Each face has 16 center slots (on 4x4)
3. Probability favors having more "correct" pieces than any single "wrong" color


THE BOY CONSTRAINT:
===================

BOY = "Blue-Orange-Yellow" - the standard Rubik's cube color arrangement.
Opposite faces have complementary colors:
    - White opposite Yellow
    - Red opposite Orange
    - Blue opposite Green

When assigning colors to faces, we MUST respect BOY layout!
We can't just pick any 6 color assignments - they must form a valid cube.

Example of INVALID assignment (not BOY):
    - Front = Red, Back = Red  <- WRONG! Opposite faces can't be same color

The algorithm ensures BOY by:
1. Pick face 1 by majority -> face 2 is opposite (automatic)
2. Pick face 3 by majority from remaining -> face 4 is opposite
3. Pick face 5 such that (face5, face6) form valid BOY with faces 1-4


TRACKING MECHANISM:
===================

Once we determine which color belongs on a face, we need to TRACK that face
even as the cube rotates during solving.

For even cubes, we MARK a specific center slice as the "tracker":
    ┌─┬─┬─┬─┐
    │ │ │ │ │
    ├─┼─┼─┼─┤
    │ │★│ │ │  <- This slice is marked as tracker
    ├─┼─┼─┼─┤     It remembers: "wherever I am, that face should be RED"
    │ │ │ │ │
    ├─┼─┼─┼─┤
    │ │ │ │ │
    └─┴─┴─┴─┘

When the cube rotates, the tracker slice moves with it, always pointing
to the correct face for that color.

CLEANUP: After solving, these tracker marks must be removed (cleanup_trackers).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence
from typing import TYPE_CHECKING, Tuple

from cube.domain.model import CenterSlice, Color

if TYPE_CHECKING:
    from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.geometric import create_layout
from cube.domain.geometric.cube_layout import CubeLayout
from cube.domain.model.CubeQueries2 import Pred
from cube.domain.model.Face import Face
from cube.domain.model.FaceName import FaceName
from cube.domain.tracker.trackers import (
    _TRACKER_VISUAL_MARKER,
    FaceTracker,
    MarkedFaceTracker,
    SimpleFaceTracker,
    get_tracker_key_prefix,
)
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.solver.protocols import SolverElementsProvider
from cube.utils.OrderedSet import OrderedSet


class NxNCentersFaceTrackers(SolverHelper):
    """Creates face trackers for NxN center solving.

    This class determines which color belongs on each face of an even cube
    by analyzing the current piece distribution and finding majority colors.

    ALGORITHM OVERVIEW:
    ===================

    Step 1: Find face with highest count of any single color
            -> This becomes face 1, that color is its "correct" color
            -> Face 2 = opposite of face 1 (automatic by BOY)

    Step 2: From remaining 4 faces, find the one with highest count
            of a color NOT used by faces 1-2
            -> This becomes face 3
            -> Face 4 = opposite of face 3

    Step 3: The last 2 faces and 2 colors must be matched
            such that the result is a valid BOY layout
            -> Try both assignments, pick the valid one

    WHY THIS ORDER?
    ===============

    We pick faces in order of "confidence" - faces with higher majority
    counts are more likely to be correctly identified. By assigning
    the most confident faces first, we reduce error propagation.

    Example:
        Face A has 12 red pieces (75% majority) <- HIGH confidence
        Face B has 5 blue pieces (31% majority) <- LOW confidence

        We assign face A first, then use remaining colors for face B.

    USAGE:
    ======
        trackers = NxNCentersFaceTrackers(solver, holder_id=42)
        t1 = trackers.track_no_1()        # First face (highest majority)
        t2 = t1.track_opposite()          # Opposite face
        t3 = trackers._track_no_3([t1, t2])  # Third face
        t4 = t3.track_opposite()          # Opposite face
        t5, t6 = trackers._track_two_last([t1, t2, t3, t4])  # Last two
    """

    __slots__ = ["_holder_id"]

    # Class variable for unique tracker IDs
    _global_tracer_id: int = 0

    def __init__(self, solver: SolverElementsProvider, holder_id: int) -> None:
        super().__init__(solver, "NxNCentersFaceTrackers")
        self._holder_id = holder_id

    # =========================================================================
    # Factory methods - create FaceTrackers using self._holder_id
    # =========================================================================

    def _create_tracker(self, parent_container: "FacesTrackerHolder", color: Color, pred: Pred[Face]) -> SimpleFaceTracker:
        """Create a SimpleFaceTracker."""
        return SimpleFaceTracker(self.cube, parent_container, color, pred)

    def _create_tracker_by_center_piece(self, parent_container: "FacesTrackerHolder",_slice: CenterSlice) -> MarkedFaceTracker:
        """Mark a center slice and create a MarkedFaceTracker for it.

        Returns MarkedFaceTracker which stores the key for cleanup.
        """
        NxNCentersFaceTrackers._global_tracer_id += 1
        unique_id = NxNCentersFaceTrackers._global_tracer_id

        prefix = get_tracker_key_prefix()
        key = f"{prefix}h{self._holder_id}:{_slice.color}{unique_id}"

        edge = _slice.edge
        edge.moveable_attributes[key] = _slice.color  # Store Color for renderer

        cube = _slice.parent.cube
        if cube.config.solver_annotate_trackers:
            cube.sp.marker_manager.add_marker(edge, "tracker_c0", cube.sp.marker_factory.c0(), moveable=True)
        if cube.config.face_tracker.annotate:
            cube.sp.marker_manager.add_marker(edge, _TRACKER_VISUAL_MARKER, cube.sp.marker_factory.center_tracker(), moveable=True)

        return MarkedFaceTracker(cube, parent_container, _slice.color, key)

    def _create_tracker_by_color(self, parent_container: FacesTrackerHolder, face: Face, color: Color) -> MarkedFaceTracker:
        """Find slice with color on face and create tracker for it."""
        _slice = face.cube.cqr.find_slice_in_face_center(face, lambda s: s.color == color)
        assert _slice
        return self._create_tracker_by_center_piece(parent_container, _slice)

    def _create_tracker_on_face(self, parent_container: FacesTrackerHolder, face: Face, color: Color) -> MarkedFaceTracker:
        """Mark any center slice on face and assign a specific tracker color.

        Unlike _create_tracker_by_color which requires a slice of the target
        color to exist on the face, this marks any available center slice.
        Used for the last two faces where the BOY-determined color may not
        be present on the face yet (it will be placed there during solving).
        """
        NxNCentersFaceTrackers._global_tracer_id += 1
        unique_id = NxNCentersFaceTrackers._global_tracer_id

        prefix = get_tracker_key_prefix()
        key = f"{prefix}h{self._holder_id}:{color}{unique_id}"

        # Prefer a slice matching our target color (more stable during solving),
        # fall back to any available center slice.
        _slice = None
        for s in face.center.all_slices:
            if s.color == color:
                _slice = s
                break
        if _slice is None:
            _slice = next(iter(face.center.all_slices))
        edge = _slice.edge
        edge.moveable_attributes[key] = color  # Store assigned color

        cube = face.cube
        if cube.config.solver_annotate_trackers:
            cube.sp.marker_manager.add_marker(edge, "tracker_c0", cube.sp.marker_factory.c0(), moveable=True)
        if cube.config.face_tracker.annotate:
            cube.sp.marker_manager.add_marker(edge, _TRACKER_VISUAL_MARKER, cube.sp.marker_factory.center_tracker(), moveable=True)

        return MarkedFaceTracker(cube, parent_container, color, key)

    def _create_tracker_odd(self, parent_container: FacesTrackerHolder, f: Face) -> SimpleFaceTracker:
        """Create tracker for odd cube using fixed center."""
        cube = f.cube
        n_slices = cube.n_slices
        assert n_slices % 2

        rc = (n_slices // 2, n_slices // 2)
        color = f.center.get_center_slice(rc).color

        def pred(_f: Face) -> bool:
            return _f.center.get_center_slice(rc).color == color

        return self._create_tracker(parent_container, color, pred)

    # =========================================================================
    # Tracker creation for BOY layout
    # =========================================================================

    def track_no_1(self, parent_container: "FacesTrackerHolder") -> FaceTracker:
        """Create tracker for face 1 - the face with highest majority color.

        ODD CUBE:
        ---------
        Simply uses the front face's fixed center piece.

        EVEN CUBE:
        ----------
        Searches ALL faces for the highest count of any single color.

        Example - finding face 1 on a scrambled 4x4:
            Front: R=5, B=3, O=4, G=2, W=1, Y=1  -> max=5 (Red)
            Back:  R=2, B=4, O=3, G=3, W=2, Y=2  -> max=4 (Blue)
            Up:    R=3, B=2, O=2, G=8, W=0, Y=1  -> max=8 (Green) <- WINNER!
            ...

        Face 1 = Up, Color = Green (highest majority across all faces)

        WHY HIGHEST MAJORITY?
        ---------------------
        The face with the strongest majority signal is most likely to be
        correctly identified. Starting with high-confidence assignments
        reduces the chance of cascading errors.

        Returns:
            FaceTracker for face 1 with its assigned color.
            :param container:
        """
        cube = self.cube
        if cube.n_slices % 2:
            return self._create_tracker_odd(parent_container, cube.front)
        else:
            f, c = self._find_face_with_max_colors()
            return self._create_tracker_by_color(parent_container, f, c)

    def _track_no_3(self, parent_container: FacesTrackerHolder, two_first: Sequence[FaceTracker]) -> FaceTracker:
        """Create tracker for face 3 - highest majority from remaining faces/colors.

        After faces 1 and 2 are assigned (face 2 = opposite of face 1),
        we have 4 remaining faces and 4 remaining colors.

        ALGORITHM:
        ----------
        1. Exclude faces 1 and 2 from search
        2. Exclude colors used by faces 1 and 2
        3. Find highest majority among remaining (4 faces × 4 colors)

        Example:
            Face 1 = Up (Green), Face 2 = Down (Blue)  <- already assigned
            Remaining faces: Front, Back, Left, Right
            Remaining colors: Red, Orange, White, Yellow

            Search:
                Front: R=6, O=3, W=4, Y=3  -> max=6 (Red) <- WINNER!
                Back:  R=2, O=5, W=3, Y=5  -> max=5 (Orange/Yellow tie)
                Left:  R=4, O=4, W=5, Y=3  -> max=5 (White)
                Right: R=4, O=4, W=4, Y=5  -> max=5 (Yellow)

            Face 3 = Front, Color = Red

        WHY EXCLUDE USED COLORS?
        ------------------------
        Each color can only appear on ONE face (BOY constraint).
        If Green is assigned to Up, no other face can be Green.
        By excluding used colors, we ensure valid assignments.

        WHY THIS ALWAYS WORKS:
        ----------------------
        Faces 1+2 contain only 2/6 = 1/3 of all center pieces.
        The remaining 4 faces contain 4/6 = 2/3 of pieces.
        At least one face among them MUST have pieces of an unused color.

        Args:
            parent_container: The FacesTrackerHolder that owns this tracker.
            two_first: Trackers for faces 1 and 2.

        Returns:
            FaceTracker for face 3 with its assigned color.
        """
        cube = self.cube

        assert len(two_first) == 2

        # WHY NOT USE SET ? BECAUSE the order is unpredictable, and we want the solution to be such
        #left = list({*cube.faces} - {two_first[0].face, two_first[1].face})
        left = {f: None for f in cube.faces}
        # don't try left.keys() - again it will be converted to set
        left.pop(two_first[0].face)
        left.pop(two_first[1].face)

        assert not cube.n_slices % 2

        c12 = {two_first[0].color, two_first[1].color}

        left_colors = set(cube.original_layout.colors()) - c12

        # # can be any, still doesn't prevent BOY
        # There will always a face that contains a color that is not included in f1, f2
        # because f1, f2 contains only 1/3 of all pieces
        f3, f3_color = self._find_face_with_max_colors(left, left_colors)

        return self._create_tracker_by_color(parent_container, f3, f3_color)

    def _track_two_last(self, parent_container: FacesTrackerHolder, four_first: Sequence[FaceTracker]) -> Tuple[FaceTracker, FaceTracker]:
        """Create trackers for faces 5 and 6 - the final BOY-constrained assignment.

        After 4 faces are assigned, we have:
        - 2 remaining faces (f5, f6)
        - 2 remaining colors (c5, c6)

        THE CRITICAL BOY CONSTRAINT:
        ============================

        We can't just randomly assign colors to the last 2 faces!
        The assignment must result in a valid BOY (Blue-Orange-Yellow) layout.

        Example - why this matters:
            Already assigned:
                Up = Green, Down = Blue       (opposites ✓)
                Front = Red, Back = Orange    (opposites ✓)

            Remaining:
                Faces: Left, Right
                Colors: White, Yellow

            Two possible assignments:
                Option A: Left=White, Right=Yellow
                Option B: Left=Yellow, Right=White

            Only ONE of these creates a valid BOY cube!
            (In standard layout: Left=Yellow opposite Right=White is wrong)

        ALGORITHM:
        ----------
        1. Get remaining 2 faces and 2 colors
        2. Try assigning color c5 to face f5
        3. Check if this creates valid BOY layout using CubeLayout.same()
        4. If not valid, swap: assign c6 to f5 instead
        5. f6 automatically gets the remaining color (opposite of f5)

        WHY THIS WORKS:
        ---------------
        With 2 faces and 2 colors, there are only 2 possible assignments.
        Exactly ONE of them is valid BOY (or both if cube was not properly shuffled).
        We try one, verify with CubeLayout, and use the other if invalid.

        Args:
            parent_container: The FacesTrackerHolder that owns this tracker.
            four_first: Trackers for faces 1-4.

        Returns:
            Tuple of (face_5_tracker, face_6_tracker).
        """
        cube = self.cube

        if not cube.config.face_tracker.use_simple_f5_tracker:
            return self._track_two_last_old(parent_container, four_first)
        else:


            assert cube.n_slices % 2 == 0

            left_two_faces: list[Face] = list(OrderedSet(cube.faces) - {f.face for f in four_first})

            assert len(left_two_faces) == 2

            first_4_colors: set[Color] = set((f.color for f in four_first))

            left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - first_4_colors

            c5: Color = left_two_colors.pop()
            c6: Color = left_two_colors.pop()

            f5 = left_two_faces.pop()

            color = c5
            pred = self._create_f5_pred(four_first, color)

            if pred(f5):
                # f5/c5 make it a BOY
                pass
            else:
                color = c6
                pred = self._create_f5_pred(four_first, color)
                assert pred(f5)

            f5_track = self._create_tracker(parent_container, color, pred)

        f6_track = f5_track._track_opposite()

        return f5_track, f6_track

    def _track_two_last_old(self, parent_container: FacesTrackerHolder, four_first: Sequence[FaceTracker]) -> Tuple[FaceTracker, FaceTracker]:
        """Create trackers for faces 5 and 6 - the final BOY-constrained assignment.

        After 4 faces are assigned, we have:
        - 2 remaining faces (f5, f6)
        - 2 remaining colors (c5, c6)

        THE CRITICAL BOY CONSTRAINT:
        ============================

        We can't just randomly assign colors to the last 2 faces!
        The assignment must result in a valid BOY (Blue-Orange-Yellow) layout.

        Example - why this matters:
            Already assigned:
                Up = Green, Down = Blue       (opposites ✓)
                Front = Red, Back = Orange    (opposites ✓)

            Remaining:
                Faces: Left, Right
                Colors: White, Yellow

            Two possible assignments:
                Option A: Left=White, Right=Yellow
                Option B: Left=Yellow, Right=White

            Only ONE of these creates a valid BOY cube!
            (In standard layout: Left=Yellow opposite Right=White is wrong)

        ALGORITHM:
        ----------
        1. Get remaining 2 faces and 2 colors
        2. Try assigning color c5 to face f5
        3. Check if this creates valid BOY layout using CubeLayout.same()
        4. If not valid, swap: assign c6 to f5 instead
        5. f6 automatically gets the remaining color (opposite of f5)

        WHY THIS WORKS:
        ---------------
        With 2 faces and 2 colors, there are only 2 possible assignments.
        Exactly ONE of them is valid BOY (or both if cube was not properly shuffled).
        We try one, verify with CubeLayout, and use the other if invalid.

        Args:
            parent_container: The FacesTrackerHolder that owns this tracker.
            four_first: Trackers for faces 1-4.

        Returns:
            Tuple of (face_5_tracker, face_6_tracker).
        """
        cube = self.cube

        assert cube.n_slices % 2 == 0

        left_two_faces: list[Face] = list(OrderedSet(cube.faces) - {f.face for f in four_first})

        assert len(left_two_faces) == 2

        first_4_colors: set[Color] = set((f.color for f in four_first))

        left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - first_4_colors

        c5: Color = left_two_colors.pop()
        c6: Color = left_two_colors.pop()

        f5: Face = left_two_faces.pop()

        color = c5
        pred = self._create_f5_pred(four_first, color)

        if pred(f5):
            # f5/c5 make it a BOY
            pass
        else:
            color = c6
            # other = c5
            # f5/c5 make it a BOY
            pred = self._create_f5_pred(four_first, color)
            assert pred(f5)

        f5_track = self._create_tracker(parent_container, color, pred)
        f6_track = f5_track._track_opposite()

        return f5_track, f6_track


    def _create_f5_pred(self, four_first: Sequence[FaceTracker], color: Color) -> Pred[Face]:
        """Create a predicate that tests if a face/color assignment makes valid BOY.

        This predicate is used by FaceTracker.by_pred() to dynamically track face 5.
        It returns True if assigning `color` to face `f` creates a valid BOY layout.

        The predicate is evaluated each time we need to locate face 5, allowing
        the tracker to follow the face even as the cube rotates.

        Args:
            four_first: Already assigned trackers for faces 1-4.
            color: The color we're testing for face 5.

        Returns:
            Predicate function that takes a Face and returns bool.
        """
        cube = self.cube

        four_first = [*four_first]

        first_4_colors: set[Color] = set((f.color for f in four_first))

        def _pred(f: Face) -> bool:

            """

            :param f:
            :return: True if f/color make it a boy
            """

            left_two_faces: set[Face] = {*cube.faces} - {f.face for f in four_first}

            if f not in left_two_faces:
                return False

            left_two_colors: set[Color] = set(self.cube.original_layout.colors()) - first_4_colors

            assert color in left_two_colors

            c5: Color = left_two_colors.pop()
            c6: Color = left_two_colors.pop()

            f5: Face = left_two_faces.pop()
            f6: Face = left_two_faces.pop()

            # make f as f5
            if f5 is not f:
                f5, f6 = f, f5

            if c5 is not color:
                c5, c6 = color, c5

            try1 = {f.face.name: f.color for f in four_first}
            try1[f5.name] = c5
            try1[f6.name] = c6
            cl: CubeLayout = create_layout(False, try1, self.cube.sp)

            if cl.same(self.cube.original_layout):
                return True  # f/color make it a BOY

            f5, f6 = (f6, f5)
            try1 = {f.face.name: f.color for f in four_first}
            try1[f5.name] = c5
            try1[f6.name] = c6
            cl = create_layout(False, try1, self.cube.sp)
            assert cl.same(self.cube.original_layout)

            return False

        return _pred

    @staticmethod
    def _is_track_slice(s: CenterSlice) -> bool:
        """Check if a center slice is marked as a tracker."""
        return FaceTracker.is_track_slice(s)

    # Note: Tracker cleanup is now handled by FacesTrackerHolder.cleanup()
    # which uses per-holder IDs for safe cleanup. No global cleanup method here.

    # Using a variable instead of `if True:` so mypy/pyright will type-check
    # the disabled debug code. Set to False to enable debug output.
    _SKIP_DEBUG = True

    def _debug_print_track_slices(self, message: str):
        """Print track slices for debugging. Disabled by default via _SKIP_DEBUG."""
        if self._SKIP_DEBUG:
            return

        print(f"=== track slices: {message}================================")
        for f in self.cube.faces:
            for s in f.center.all_slices:

                if self._is_track_slice(s):
                    print(f"Track slice: {s} {s.color} on {f}")
        print("===================================")

    def _find_face_with_max_colors(self, faces: Iterable[Face] | None = None,
                                   colors: Collection[Color] | None = None) -> Tuple[Face, Color]:
        """Find the face with the highest count of any single color.

        THE CORE MAJORITY ALGORITHM:
        ============================

        This is the heart of the even-cube face tracking algorithm.
        It searches all (face, color) combinations and returns the pair
        with the highest count.

        Example search on 4x4:
            Searching faces=[Front, Back, Up, Down, Left, Right]
            Searching colors=[R, O, B, G, W, Y]

            Results matrix (count of each color on each face):
                      R   O   B   G   W   Y
            Front:    5   3   4   2   1   1   -> max = 5 (R)
            Back:     2   4   3   3   2   2   -> max = 4 (O)
            Up:       3   2   2   8   0   1   -> max = 8 (G) <- GLOBAL MAX
            Down:     2   3   2   1   3   5   -> max = 5 (Y)
            Left:     2   2   3   1   5   3   -> max = 5 (W)
            Right:    2   2   2   1   5   4   -> max = 5 (W)

            Winner: (Up, Green) with count 8

        OPTIONAL FILTERING:
        -------------------
        - `faces` parameter: Search only these faces (exclude already assigned)
        - `colors` parameter: Search only these colors (exclude already used)

        This is used when assigning face 3 (exclude faces 1-2 and their colors).

        Args:
            faces: Faces to search (default: all 6 faces).
            colors: Colors to search (default: all 6 colors).

        Returns:
            Tuple of (face, color) with highest count.
        """
        n_max = -1
        f_max: Face | None = None
        c_max: Color | None = None
        cube = self.cube

        if colors is None:
            colors = cube.original_layout.colors()

        if faces is None:
            faces = cube.faces

        self.debug("_find_face_with_max_colors:", [*faces])

        for f in faces:
            for c in colors:
                n = self.cqr.count_color_on_face(f, c)
                if n > n_max:
                    n_max = n
                    f_max = f
                    c_max = c

        assert f_max and c_max  # mypy
        return f_max, c_max

