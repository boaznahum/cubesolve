from typing import Protocol

from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName


class SliceLayout(Protocol):
    """
    claude: document this class, find usage, read __init__py.py
    Hold al the geometry related too slice
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


class _SliceLayout(SliceLayout):

    def __init__(self, slice_name: SliceName):
        self._slice_name: SliceName = slice_name

    def get_face_name(self) -> FaceName:

        """
        cluad: replace with memebr that passed inthe constructor from the CubeLayout
        :param slice_name:
        :return:
        """

        match self._slice_name:

            case SliceName.S:  # over F
                return FaceName.F

            case SliceName.M:  # over L
                return FaceName.L

            case SliceName.E:  # over D
                return FaceName.D

            case _:
                raise RuntimeError(f"Unknown Slice {self._slice_name}")
