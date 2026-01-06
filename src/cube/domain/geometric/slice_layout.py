from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.domain.model.FaceName import FaceName
    from cube.domain.model.SliceName import SliceName


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

        Slice Traversal (content movement during rotation):
            M: F → U → B → D → F  (vertical cycle, like L rotation)
            E: R → B → L → F → R  (horizontal cycle, like D rotation)
            S: U → R → D → L → U  (around F/B axis, like F rotation)

        Args:
            face_name: The face to check.

        Returns:
            CLGColRow.ROW if slice cuts rows (forms a column on face)
            CLGColRow.COL if slice cuts columns (forms a row on face)
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

    def __init__(self, slice_name: "SliceName"):
        self._slice_name = slice_name

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

    def does_slice_cut_rows_or_columns(self, face_name: FaceName) -> CLGColRow:
        from cube.domain.geometric._CubeLayoutGeometry import _CubeLayoutGeometry
        return _CubeLayoutGeometry.does_slice_cut_rows_or_columns(self._slice_name, face_name)

    def does_slice_of_face_start_with_face(self, face_name: FaceName) -> bool:
        from cube.domain.geometric._CubeLayoutGeometry import _CubeLayoutGeometry
        return _CubeLayoutGeometry.does_slice_of_face_start_with_face(self._slice_name, face_name)
