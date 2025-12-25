"""Face tracker - tracks which color belongs to which face during solving.

See FACE_TRACKER.md in this directory for detailed documentation.

Each FaceTracker belongs to a FacesTrackerHolder identified by holder_id.
The holder_id is embedded in marker keys for per-holder cleanup.

TRACKER HIERARCHY:
==================

    FaceTracker (abstract base)      # Never instantiated directly
        │
        ├── SimpleFaceTracker        # For odd, opposite, f5 (no cleanup)
        │
        └── MarkedFaceTracker        # For marked slices (needs cleanup)

SimpleFaceTracker is used for trackers that don't mark slices:
- Odd cube trackers (use fixed center color)
- Opposite trackers (find opposite face)
- f5 trackers (use BOY predicate)

MarkedFaceTracker is used when a center slice is marked with a tracking key.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from cube.domain.model import CenterSlice, Color
from cube.domain.model.CubeQueries2 import Pred
from cube.domain.model.Face import Face

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

_TRACKER_KEY_PREFIX = "_nxn_centers_track:"


class FaceTracker(ABC):
    """Abstract base tracker - holds cube reference and color.

    Never instantiated directly. Use SimpleFaceTracker or MarkedFaceTracker.
    """

    __slots__ = ["_cube", "_color"]

    def __init__(self, cube: "Cube", color: Color) -> None:
        self._cube = cube
        self._color = color

    @property
    @abstractmethod
    def face(self) -> Face:
        """Find and return the tracked face. Abstract - must be implemented."""
        pass

    @property
    def color(self) -> Color:
        return self._color

    def __str__(self) -> str:
        return f"{self.color.name}@{self.face}"

    def __repr__(self) -> str:
        return self.__str__()

    @abstractmethod
    def cleanup(self) -> None:
        """Remove any marks this tracker created. Abstract - must be implemented."""
        pass

    def track_opposite(self) -> "SimpleFaceTracker":
        """Create tracker for the opposite face."""
        second_color = self._cube.original_layout.opposite_color(self._color)

        def _pred(_f: Face) -> bool:
            return _f.opposite is self.face

        return SimpleFaceTracker(self._cube, second_color, _pred)

    @staticmethod
    def is_track_slice(s: CenterSlice) -> bool:
        for k in s.edge.c_attributes.keys():
            if isinstance(k, str) and k.startswith(_TRACKER_KEY_PREFIX):
                return True
        return False


class SimpleFaceTracker(FaceTracker):
    """Tracker that doesn't mark slices. No cleanup needed.

    Used for:
    - Odd cube trackers (use fixed center color predicate)
    - Opposite trackers (find opposite face)
    - f5 trackers (use BOY predicate)

    TODO: Revisit this design - storing a predicate callable feels inelegant.
    """

    __slots__ = ["_pred"]

    def __init__(self, cube: "Cube", color: Color, pred: Pred[Face]) -> None:
        super().__init__(cube, color)
        self._pred = pred

    @property
    def face(self) -> Face:
        """Find face using stored predicate."""
        return self._cube.cqr.find_face(self._pred)

    def cleanup(self) -> None:
        """No-op - simple trackers don't mark anything."""
        pass


class MarkedFaceTracker(FaceTracker):
    """Tracker that marks a center slice. Needs cleanup.

    Created by _create_tracker_by_center_piece() when a center slice
    is marked with a tracking key in its c_attributes.

    Stores the key used to mark the slice.
    cleanup() searches for and removes that specific key.
    """

    __slots__ = ["_key"]

    def __init__(self, cube: "Cube", color: Color, key: str) -> None:
        super().__init__(cube, color)
        self._key = key

    @property
    def face(self) -> Face:
        """Find face containing the marked slice."""
        def _slice_pred(s: CenterSlice) -> bool:
            return self._key in s.edge.c_attributes

        def _face_pred(_f: Face) -> bool:
            return _f.cube.cqr.find_slice_in_face_center(_f, _slice_pred) is not None

        return self._cube.cqr.find_face(_face_pred)

    def cleanup(self) -> None:
        """Search for and remove the specific key from the marked slice."""
        for f in self._cube.faces:
            for s in f.center.all_slices:
                if self._key in s.edge.c_attributes:
                    del s.edge.c_attributes[self._key]
                    return


# Export prefix for TrackerFactory
TRACKER_KEY_PREFIX = _TRACKER_KEY_PREFIX
