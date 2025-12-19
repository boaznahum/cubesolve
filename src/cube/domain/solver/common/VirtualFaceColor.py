"""
Virtual Face Color for Even Cube Support
========================================

This module provides the virtual_face_colors context manager that temporarily
sets face colors for even cubes during solving.

Location: src/cube/domain/solver/common/VirtualFaceColor.py

This is in the common/ directory (not cage-specific) because:
- Any solver working with even cubes may need this mechanism
- The virtual color concept is general-purpose
- FaceTracker (which this depends on) is also in common/

THE PROBLEM:
-----------
On even cubes (4x4, 6x6), there is no fixed center piece:

1. face.center.color returns an arbitrary piece's color (WRONG!)
2. Part.match_faces() uses face.color, so it gives wrong results
3. Any solver that checks piece positions will fail on even cubes
   when centers are scrambled

THE SOLUTION:
------------
Use FaceTracker to establish which color each face should be, then
temporarily set Face._virtual_color so that face.color returns the
correct value.

ROTATION HANDLING:
-----------------
Virtual colors are set on Face OBJECTS, but Face objects don't move during
cube rotations (X, Y, Z). This module handles rotations by:

1. Tracking a FaceName -> Color mapping (not Face -> Color)
2. When cube rotations are detected, the mapping is transformed
3. After transformation, Face._virtual_color values are updated

For example, after Y rotation:
- Face F should now have what Face R had before
- Face R should now have what Face B had before
- etc.

USAGE:
-----
```python
from cube.domain.solver.common.VirtualFaceColor import (
    create_even_cube_face_trackers,
    virtual_face_colors
)

# In any solver working with even cubes:
if cube.n_slices % 2 == 0:  # Even cube
    trackers = create_even_cube_face_trackers(self)
    with virtual_face_colors(cube, trackers):
        self._solve_corners()  # face.color now returns correct values
        self._solve_centers()  # Rotations are handled automatically!
else:
    # Odd cube - no virtual colors needed
    self._solve_corners()
    self._solve_centers()
```

HOW IT WORKS:
------------
1. create_even_cube_face_trackers() uses FaceTracker to find which color
   each face should be (same algorithm as NxNCentersV3 for even cubes)

2. virtual_face_colors() context manager:
   - Saves current _virtual_color for all faces
   - Sets _virtual_color based on trackers
   - Wraps cube rotation methods to track rotations
   - After each rotation, transforms virtual colors appropriately
   - On exit (even on exception), restores previous _virtual_color values

3. Face.color property checks _virtual_color first:
   - If set: returns _virtual_color (the "correct" color)
   - If None: returns center.color (normal behavior)

4. Part.match_faces() now works correctly because face.color is correct

IMPORTANT: This is a TEMPORARY override. After the context manager exits,
face.color returns to normal (center.color). By that point, centers should
be solved so center.color will be correct anyway.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Callable

from cube.domain.model import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.FaceTracker import FaceTracker
from cube.domain.solver.beginner.NxnCentersFaceTracker import NxNCentersFaceTrackers

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.domain.solver.protocols import SolverElementsProvider, OperatorProtocol
    from cube.domain.algs import Alg


# =============================================================================
# ROTATION TRANSFORMS
# =============================================================================
# These define how virtual colors should transform after cube rotations.
# Each transform maps: old_face_position -> where_color_came_from
#
# Example: After Y rotation, F position now has what was at R position.
# So Y_TRANSFORM[F] = R means "new F color = old R color"
# =============================================================================

# Y rotation: Viewed from above, cube rotates CW (looking at U face).
# Content moves: R -> F -> L -> B -> R
# So virtual colors transform: new F = old R, new L = old F, etc.
Y_TRANSFORM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.R,
    FaceName.R: FaceName.B,
    FaceName.B: FaceName.L,
    FaceName.L: FaceName.F,
    FaceName.U: FaceName.U,  # U stays
    FaceName.D: FaceName.D,  # D stays
}

# Y' rotation (inverse): content moves F -> R -> B -> L -> F
Y_PRIME_TRANSFORM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.L,
    FaceName.R: FaceName.F,
    FaceName.B: FaceName.R,
    FaceName.L: FaceName.B,
    FaceName.U: FaceName.U,
    FaceName.D: FaceName.D,
}

# X rotation: content moves D -> F -> U -> B -> D
X_TRANSFORM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.D,
    FaceName.U: FaceName.F,
    FaceName.B: FaceName.U,
    FaceName.D: FaceName.B,
    FaceName.L: FaceName.L,  # L stays
    FaceName.R: FaceName.R,  # R stays
}

# X' rotation (inverse): content moves U -> F -> D -> B -> U
X_PRIME_TRANSFORM: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.U,
    FaceName.U: FaceName.B,
    FaceName.B: FaceName.D,
    FaceName.D: FaceName.F,
    FaceName.L: FaceName.L,
    FaceName.R: FaceName.R,
}

# Z rotation: content moves L -> U -> R -> D -> L
Z_TRANSFORM: dict[FaceName, FaceName] = {
    FaceName.U: FaceName.L,
    FaceName.R: FaceName.U,
    FaceName.D: FaceName.R,
    FaceName.L: FaceName.D,
    FaceName.F: FaceName.F,  # F stays
    FaceName.B: FaceName.B,  # B stays
}

# Z' rotation (inverse): content moves U -> L -> D -> R -> U
Z_PRIME_TRANSFORM: dict[FaceName, FaceName] = {
    FaceName.U: FaceName.R,
    FaceName.R: FaceName.D,
    FaceName.D: FaceName.L,
    FaceName.L: FaceName.U,
    FaceName.F: FaceName.F,
    FaceName.B: FaceName.B,
}


def _apply_transform(
    mapping: dict[FaceName, Color],
    transform: dict[FaceName, FaceName]
) -> dict[FaceName, Color]:
    """
    Apply a rotation transform to a FaceName->Color mapping.

    Args:
        mapping: Current FaceName -> Color mapping
        transform: Rotation transform (new_face -> old_face)

    Returns:
        New FaceName -> Color mapping after rotation
    """
    return {new_face: mapping[old_face] for new_face, old_face in transform.items()}


class VirtualColorManager:
    """
    Manages virtual face colors and updates them after cube rotations.

    This class tracks a FaceName -> Color mapping and provides methods to:
    1. Apply the mapping to Face._virtual_color
    2. Transform the mapping after cube rotations (X, Y, Z)

    USAGE:
    -----
    This class is used internally by virtual_face_colors() context manager.
    The context manager sets up the VirtualColorManager and registers it as
    a rotation hook on the cube. After each rotation, the hook is called
    and virtual colors are updated automatically.

    The hook mechanism ensures virtual colors stay synchronized with cube
    rotations WITHOUT requiring the solver to explicitly track rotations.
    This includes query-mode rotations in rotate_and_check().
    """

    def __init__(self, cube: Cube, initial_mapping: dict[FaceName, Color]) -> None:
        """
        Initialize VirtualColorManager.

        Args:
            cube: The cube to manage virtual colors for
            initial_mapping: FaceName -> Color mapping from trackers
        """
        from cube.domain.model._elements import AxisName
        self._cube = cube
        self._mapping: dict[FaceName, Color] = initial_mapping.copy()
        self._apply_to_faces()

        # Register as rotation hook on the cube
        self._hook = self._on_rotation
        cube._rotation_hooks.append(self._hook)

    def _on_rotation(self, axis_name: "AxisName", n: int) -> None:
        """
        Hook called by Cube.rotate_whole() after any X/Y/Z rotation.

        Virtual colors must be updated to follow content movement. When Y rotates:
        - Content at F moves to L, R to F, B to R, L to B
        - Virtual colors must also transform so face.color matches what
          the content at that face "should be"

        Args:
            axis_name: The axis of rotation (X, Y, or Z)
            n: Number of 90° rotations. Positive = CW, negative = CCW.
        """
        from cube.domain.model._elements import AxisName

        # Normalize n to 0-3 range
        n = n % 4
        if n == 0:
            return  # No actual rotation

        # Select the transform based on axis
        if axis_name == AxisName.X:
            transform = X_TRANSFORM
        elif axis_name == AxisName.Y:
            transform = Y_TRANSFORM
        elif axis_name == AxisName.Z:
            transform = Z_TRANSFORM
        else:
            return

        # Apply the transform n times
        for _ in range(n):
            self._mapping = _apply_transform(self._mapping, transform)
        self._apply_to_faces()

    def _apply_to_faces(self) -> None:
        """
        Apply current mapping to Face._virtual_color and invalidate caches.

        This sets _virtual_color on each Face and clears all caches that
        depend on face.color (color_2_face, position_id).
        """
        for face in self._cube.faces:
            face._virtual_color = self._mapping.get(face.name)

        # Invalidate caches
        self._cube._color_2_face.clear()
        self._cube.reset_after_faces_changes()

    def handle_rotation(self, alg_name: str) -> None:
        """
        Handle a cube rotation by transforming the virtual color mapping.

        This method is called after each algorithm is played. It checks
        if the algorithm is a cube rotation (X, Y, Z) and if so, transforms
        the mapping appropriately.

        Args:
            alg_name: Name of the algorithm that was played (e.g., "Y", "X'", "Z2")
        """
        # Parse the algorithm name to detect rotations
        # Handle: X, X', X2, Y, Y', Y2, Z, Z', Z2
        transform: dict[FaceName, FaceName] | None = None
        count = 1

        if alg_name.startswith("X") or alg_name.startswith("x"):
            base = alg_name[1:] if len(alg_name) > 1 else ""
            if base == "'" or base == "'":  # X'
                transform = X_PRIME_TRANSFORM
            elif base == "2":  # X2
                transform = X_TRANSFORM
                count = 2
            else:  # X
                transform = X_TRANSFORM

        elif alg_name.startswith("Y") or alg_name.startswith("y"):
            base = alg_name[1:] if len(alg_name) > 1 else ""
            if base == "'" or base == "'":  # Y'
                transform = Y_PRIME_TRANSFORM
            elif base == "2":  # Y2
                transform = Y_TRANSFORM
                count = 2
            else:  # Y
                transform = Y_TRANSFORM

        elif alg_name.startswith("Z") or alg_name.startswith("z"):
            base = alg_name[1:] if len(alg_name) > 1 else ""
            if base == "'" or base == "'":  # Z'
                transform = Z_PRIME_TRANSFORM
            elif base == "2":  # Z2
                transform = Z_TRANSFORM
                count = 2
            else:  # Z
                transform = Z_TRANSFORM

        if transform is not None:
            # Apply the transform (possibly twice for X2/Y2/Z2)
            for _ in range(count):
                self._mapping = _apply_transform(self._mapping, transform)
            self._apply_to_faces()

    def clear(self) -> None:
        """
        Clear all virtual colors from faces and unregister the rotation hook.

        Called when exiting the virtual_face_colors context.
        """
        # Unregister rotation hook
        if self._hook in self._cube._rotation_hooks:
            self._cube._rotation_hooks.remove(self._hook)

        for face in self._cube.faces:
            face._virtual_color = None
        self._cube._color_2_face.clear()
        self._cube.reset_after_faces_changes()


def create_even_cube_face_trackers(provider: SolverElementsProvider) -> list[FaceTracker]:
    """
    Create FaceTrackers for all 6 faces of an even cube.

    Uses the same algorithm as NxNCentersV3 to establish face colors:
    1. Find face with max pieces of any color -> Track it (f1)
    2. Track opposite face (f2)
    3. Find third face respecting BOY orientation (f3)
    4. Track opposite (f4)
    5. Find last two faces respecting BOY (f5, f6)

    Args:
        provider: SolverElementsProvider (e.g., CageNxNSolver instance)

    Returns:
        List of 6 FaceTrackers, one for each face

    Raises:
        AssertionError: If cube is not even (n_slices % 2 != 0)

    Example:
        >>> trackers = create_even_cube_face_trackers(cage_solver)
        >>> for t in trackers:
        ...     print(f"{t.face.name}: should be {t.color}")
    """
    cube = provider.cube
    assert cube.n_slices % 2 == 0, "create_even_cube_face_trackers only for even cubes"

    # Use the same tracker creation logic as NxNCentersV3
    trackers_helper = NxNCentersFaceTrackers(provider)

    # Step 1: Find first face (max color count)
    f1: FaceTracker = trackers_helper.track_no_1()

    # Step 2: Track opposite
    f2 = f1.track_opposite()

    # Step 3: Find third face (respects BOY)
    f3 = trackers_helper._track_no_3([f1, f2])
    f4 = f3.track_opposite()

    # Step 4: Find last two (respects BOY)
    f5, f6 = trackers_helper._track_two_last([f1, f2, f3, f4])

    return [f1, f2, f3, f4, f5, f6]


@contextmanager
def virtual_face_colors(
    cube: Cube,
    trackers: list[FaceTracker]
) -> Iterator[VirtualColorManager]:
    """
    Context manager that temporarily sets virtual colors on cube faces.

    This enables the 3x3 solver to work correctly on even cubes where
    centers are scrambled. Face.color will return the "correct" color
    (from tracker) instead of the scrambled center color.

    ROTATION HANDLING:
        Rotations are tracked AUTOMATICALLY via a hook on Cube.rotate_whole().
        This catches ALL rotations, including:
        - Rotations via op.play()
        - Query-mode rotations in rotate_and_check()
        - Any other rotations via alg.play(cube)

        No manual rotation tracking is needed!

    Args:
        cube: The cube whose faces will have virtual colors set
        trackers: List of FaceTrackers from create_even_cube_face_trackers()

    Yields:
        VirtualColorManager - rotations are handled automatically via hook

    IMPORTANT - Save/Restore Pattern:
        This context manager SAVES the previous _virtual_color values
        and RESTORES them on exit. This ensures:
        1. Nested usage works correctly
        2. Previous state is preserved even if exception occurs
        3. No permanent side effects on Face objects

    Example:
        >>> trackers = create_even_cube_face_trackers(solver)
        >>> with virtual_face_colors(cube, trackers) as manager:
        ...     # Inside this block, face.color returns tracker.color
        ...     solve_corners()  # Y rotations are tracked automatically!
        ...     solve_centers()
        ... # After block, face.color returns center.color again
    """
    # =========================================================================
    # STEP 1: SAVE previous virtual colors (for restore on exit)
    # =========================================================================
    saved_colors: dict[Face, Color | None] = {}
    for face in cube.faces:
        saved_colors[face] = face._virtual_color

    try:
        # =====================================================================
        # STEP 2: CREATE FaceName->Color mapping from trackers
        # =====================================================================
        # Capture current tracker state as a FaceName->Color mapping.
        # This mapping will be transformed when rotations occur.
        # =====================================================================
        face_name_mapping: dict[FaceName, Color] = {}
        for tracker in trackers:
            face_name_mapping[tracker.face.name] = tracker.color

        # =====================================================================
        # STEP 3: CREATE VirtualColorManager
        # =====================================================================
        # The manager handles:
        # - Setting _virtual_color on Face objects
        # - Transforming the mapping after rotations
        # - Invalidating caches
        # =====================================================================
        manager = VirtualColorManager(cube, face_name_mapping)

        # =====================================================================
        # STEP 4: YIELD - execute the with-block
        # =====================================================================
        yield manager

    finally:
        # =====================================================================
        # STEP 5: UNREGISTER the rotation hook
        # =====================================================================
        # The manager registers a hook in __init__. We must unregister it here.
        if manager._hook in cube._rotation_hooks:
            cube._rotation_hooks.remove(manager._hook)

        # =====================================================================
        # STEP 6: RESTORE previous virtual colors (always, even on exception)
        # =====================================================================
        for face, old_color in saved_colors.items():
            face._virtual_color = old_color

        # =====================================================================
        # STEP 7: INVALIDATE ALL CACHES again
        # =====================================================================
        cube._color_2_face.clear()
        cube.reset_after_faces_changes()


@contextmanager
def virtual_face_colors_with_op(
    cube: Cube,
    trackers: list[FaceTracker],
    op: "OperatorProtocol"
) -> Iterator[None]:
    """
    Context manager that sets virtual colors AND tracks rotations automatically.

    This is now a simple wrapper around virtual_face_colors() since the rotation
    hook mechanism catches ALL rotations, including:
    - Rotations via op.play()
    - Query-mode rotations in rotate_and_check()
    - Any other rotations via alg.play(cube)

    The 'op' parameter is kept for backwards compatibility but is no longer used.

    Args:
        cube: The cube whose faces will have virtual colors set
        trackers: List of FaceTrackers from create_even_cube_face_trackers()
        op: The Operator (kept for API compatibility, not used)

    Yields:
        None - rotations are tracked automatically via cube rotation hook

    Example:
        >>> trackers = create_even_cube_face_trackers(solver)
        >>> with virtual_face_colors_with_op(cube, trackers, op):
        ...     solve_corners()  # Rotations like Y, X are tracked automatically
        ...     solve_centers()
    """
    # The op parameter is no longer needed since the rotation hook catches all
    # rotations at the cube level. We just delegate to virtual_face_colors().
    _ = op  # Mark as intentionally unused

    with virtual_face_colors(cube, trackers):
        yield
