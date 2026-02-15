"""Simple face tracker - no marking, no cleanup needed.

SimpleFaceTracker is used for trackers that don't mark slices:
- Odd cube trackers (use fixed center color)
- Opposite trackers (find opposite face)
- f5 trackers (use BOY predicate)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.model import Color
from cube.domain.model.CubeQueries2 import Pred
from cube.domain.model.Face import Face
from cube.domain.tracker._face_trackers import FaceTracker

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder


class SimpleFaceTracker(FaceTracker):
    """Tracker that doesn't mark slices. No cleanup needed.

    Used for:
    - Odd cube trackers (use fixed center color predicate)
    - Opposite trackers (find opposite face)
    - f5 trackers (use BOY predicate)

    TODO: Revisit this design - storing a predicate callable feels inelegant.
    """

    __slots__ = ["_pred"]

    def __init__(self, cube: "Cube", parent: FacesTrackerHolder, color: Color, pred: Pred[Face]) -> None:
        super().__init__(cube, parent, color)
        self._pred = pred

    @property
    def face(self) -> Face:
        """Find face using stored predicate."""
        return self._cube.cqr.find_face(self._pred)

    def cleanup(self, force_remove_visible:bool = False) -> None:
        """No-op - simple trackers don't mark anything."""
        pass
