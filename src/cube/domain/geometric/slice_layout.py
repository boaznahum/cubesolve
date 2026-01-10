from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.domain.model.FaceName import FaceName
    from cube.domain.model.SliceName import SliceName
    from cube.domain.geometric._CubeLayout import _CubeLayout


class CLGColRow(Enum):
    """Indicates whether a slice cuts rows or columns on a face."""
    ROW = auto()
    COL = auto()


class SliceLayout(Protocol):
    """
    Holds all the geometry related to a slice.

    Each slice (M, E, S) has properties like:
    - Which face defines its rotation direction
    - How it cuts faces (rows vs columns)
    - Whether its indices align with face coordinates
    """

    def get_face_name(self) -> FaceName:
        """
        Return the face that defines the positive rotation direction for this slice.

        This is the face that the slice rotates "over" - when the slice rotates,
        it moves content in the same direction as rotating I think that face clockwise
        (viewed from outside the cube looking at that face).

        In terms of the LTR coordinate system (see docs/face-coordinate-system/):
        - Clockwise rotation moves content: T→R→(-T)→(-R)→T
        - Content flows from the T (top/bottom) direction toward the R (left/right) direction

        Returns:
            M slice → L face (middle layer between L and R, rotates like L)
            E slice → D face (middle layer between U and D, rotates like D)
            S slice → F face (middle layer between F and B, rotates like F)

        See also:
            - WholeCubeAlg.get_face_name() for whole-cube rotation equivalent
            - docs/face-coordinate-system/face-slice-rotation.md
        """
        ...

    def does_slice_cut_rows_or_columns(self, face_name: FaceName) -> CLGColRow:
        """
        Determine whether this slice cuts rows or columns on the given face.

        Derived from slice geometry: checks if the exit edge (to next face in cycle)
        is horizontal or vertical on this face.

        - Horizontal exit edge (top/bottom) → slice goes vertically → cuts rows
        - Vertical exit edge (left/right) → slice goes horizontally → cuts columns

        Args:
            face_name: The face to check.

        Returns:
            CLGColRow.ROW if slice cuts rows (forms vertical strips on face)
            CLGColRow.COL if slice cuts columns (forms horizontal strips on face)

        See also:
            is_horizontal_on_face() - alias that returns bool
        """
        ...

    def is_horizontal_on_face(self, face_name: FaceName) -> bool:
        """
        Check if slice forms horizontal strips (rows) on the given face.

        This is an alias for does_slice_cut_rows_or_columns that returns a bool:
        - True = slice forms horizontal strips = cuts columns = CLGColRow.COL
        - False = slice forms vertical strips = cuts rows = CLGColRow.ROW

        Args:
            face_name: The face to check.

        Returns:
            True if slice is horizontal on this face (cuts columns)
            False if slice is vertical on this face (cuts rows)
        """
        ...

    def does_slice_of_face_start_with_face(self, face_name: FaceName) -> bool:
        """
        Check if slice index 0 aligns with the face's natural coordinate origin.

        Each slice (M, E, S) has indices 0 to n_slices-1. Slice index 0 is always
        closest to the "reference face" for that slice type:
            - M[0] closest to L (M rotates like L)
            - E[0] closest to D (E rotates like D)
            - S[0] closest to F (S rotates like F)

        This method answers: when iterating slice indices on a given face,
        does index 0 correspond to row/col 0, or to row/col (n_slices-1)?

        Args:
            face_name: The face to check alignment on.

        Returns:
            True  → slice[0] aligns with face's row/col 0 (natural start)
            False → slice[0] aligns with face's row/col (n_slices-1) (inverted)

        Example: M slice on FRONT face (5x5 cube, n_slices=3)
        ======================================================

            M[0] is closest to L. On FRONT face, L is on the left side.
            Face coordinates: col 0 is on the left.
            So M[0] → col 0. Returns True (aligned).

                    L           R
                    ↓           ↓
                ┌───┬───┬───┐
                │M0 │M1 │M2 │   M[0]=col0, M[1]=col1, M[2]=col2
                ├───┼───┼───┤
                │M0 │M1 │M2 │   Returns True: slice indices align
                ├───┼───┼───┤   with face column indices
                │M0 │M1 │M2 │
                └───┴───┴───┘

        Example: M slice on BACK face (5x5 cube, n_slices=3)
        =====================================================

            M[0] is closest to L. On BACK face, L is on the RIGHT side
            (because we're looking from behind).
            Face coordinates: col 0 is on the left (which is R side of cube).
            So M[0] → col 2 (rightmost). Returns False (inverted).

                    R           L
                    ↓           ↓
                ┌───┬───┬───┐
                │M2 │M1 │M0 │   M[0]=col2, M[1]=col1, M[2]=col0
                ├───┼───┼───┤
                │M2 │M1 │M0 │   Returns False: slice indices are
                ├───┼───┼───┤   inverted relative to face columns
                │M2 │M1 │M0 │
                └───┴───┴───┘

        See also: does_slice_cut_rows_or_columns()
        """
        ...


class _SliceLayout(SliceLayout):

    def __init__(self, slice_name: "SliceName", layout: "_CubeLayout | None" = None):
        self._slice_name = slice_name
        self._layout: "_CubeLayout | None" = layout

    def get_face_name(self) -> "FaceName":

        """
        cluad: replace with memebr that passed inthe constructor from the CubeLayout
        :param slice_name:
        :return:
        """
        # Import at runtime to avoid circular import
        from cube.domain.model.FaceName import FaceName
        from cube.domain.model.SliceName import SliceName

        match self._slice_name:

            case SliceName.S:  # over F
                return FaceName.F

            case SliceName.M:  # over L
                return FaceName.L

            case SliceName.E:  # over D
                return FaceName.D

            case _:
                raise RuntimeError(f"Unknown Slice {self._slice_name}")

    def does_slice_cut_rows_or_columns(self, face_name: "FaceName") -> CLGColRow:
        """
        Determine whether this slice cuts rows or columns on the given face.

        Derived from first principles (Issue #55):
        - The slice is parallel to its rotation face and its opposite face
        - If these "axis faces" are the left/right neighbors of target face → vertical → cuts rows
        - If these "axis faces" are the top/bottom neighbors → horizontal → cuts columns

        Args:
            face_name: The face to check.

        Returns:
            CLGColRow.ROW if slice cuts rows (forms vertical strips on face)
            CLGColRow.COL if slice cuts columns (forms horizontal strips on face)

        See also:
            is_horizontal_on_face() - alias returning bool
        """
        if self._layout is None:
            raise RuntimeError(
                "Cannot derive does_slice_cut_rows_or_columns without layout reference. "
                "Use CubeLayout.get_slice() to get a properly initialized SliceLayout."
            )

        def compute() -> CLGColRow:
            from cube.domain.model.Cube import Cube
            from cube.domain.model.Face import Face

            # Get the rotation face for this slice (M→L, E→D, S→F)
            rotation_face_name = self.get_face_name()

            # Access the internal 3x3 cube to check face edge relationships
            assert self._layout is not None  # Already checked above
            internal_cube: Cube = self._layout._cube
            face: Face = internal_cube.face(face_name)

            # Get the left and right neighbors of the target face
            left_neighbor: FaceName = face.edge_left.get_other_face(face).name
            right_neighbor: FaceName = face.edge_right.get_other_face(face).name

            # If the slice's rotation face is a left/right neighbor,
            # the slice is vertical on this face (cuts rows)
            if rotation_face_name in (left_neighbor, right_neighbor):
                return CLGColRow.ROW
            else:
                return CLGColRow.COL

        # Use cache manager from layout
        cache_key = (self._slice_name, face_name)
        cache = self._layout.cache_manager.get("SliceLayout.does_slice_cut_rows_or_columns", CLGColRow)
        return cache.compute(cache_key, compute)

    def is_horizontal_on_face(self, face_name: "FaceName") -> bool:
        """
        Check if slice forms horizontal strips (rows) on the given face.

        This is an alias for does_slice_cut_rows_or_columns that returns a bool:
        - True = slice forms horizontal strips = cuts columns = CLGColRow.COL
        - False = slice forms vertical strips = cuts rows = CLGColRow.ROW

        Args:
            face_name: The face to check.

        Returns:
            True if slice is horizontal on this face (cuts columns)
            False if slice is vertical on this face (cuts rows)
        """
        return self.does_slice_cut_rows_or_columns(face_name) == CLGColRow.COL

    def does_slice_of_face_start_with_face(self, face_name: "FaceName") -> bool:
        from cube.domain.geometric._CubeGeometric import _CubeGeometric
        return _CubeGeometric._does_slice_of_face_start_with_face(self._slice_name, face_name)
