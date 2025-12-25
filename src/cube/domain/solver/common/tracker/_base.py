"""Face tracker base classes.

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
from collections.abc import Iterable
from typing import TYPE_CHECKING

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.model import CenterSlice, Color
from cube.domain.model.CubeQueries2 import Pred
from cube.domain.model.Face import Face
from cube.domain.model.PartEdge import PartEdge
from cube.domain.solver.common.tracker.FacesTrackerHolder import FacesTrackerHolder

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

# Key prefix for tracker markers in c_attributes
# Format: "_nxn_centers_track:h{holder_id}:{color}{unique_id}"
_TRACKER_KEY_PREFIX = "_nxn_centers_track:"


def get_tracker_key_prefix() -> str:
    """Get the tracker key prefix for creating marker keys.

    Used by factory classes that create MarkedFaceTracker instances.
    """
    return _TRACKER_KEY_PREFIX


class FaceTracker(ABC):
    """Abstract base tracker - holds cube reference and color.

    Never instantiated directly. Use SimpleFaceTracker or MarkedFaceTracker.

    STATIC METHODS (holder-agnostic):
    =================================
    The static methods is_track_slice() and get_slice_tracker_color() are
    HOLDER-AGNOSTIC. They detect markers from ANY holder, not just a specific one.

    Use them only for display/debug purposes where holder identity doesn't matter.
    For holder-specific operations, use the instance methods.
    """

    __slots__ = ["_cube", "_color", "_parent"]

    def __init__(self, cube: "Cube", parent: FacesTrackerHolder, color: Color) -> None:
        self._cube = cube
        self._color = color
        self._parent = parent

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

    def _track_opposite(self) -> "SimpleFaceTracker":
        """Create tracker for the opposite face."""
        second_color = self._cube.original_layout.opposite_color(self._color)

        def _pred(_f: Face) -> bool:
            return _f.opposite is self.face

        return SimpleFaceTracker(self._cube, self.parent, second_color, _pred)

    @staticmethod
    def is_track_slice(s: CenterSlice) -> bool:
        """Check if ANY tracker has marked this slice.

        WARNING: This is holder-agnostic. It returns True if ANY holder
        has marked this slice, not just the current holder. Use only for
        debug/display purposes where holder identity doesn't matter.

        Args:
            s: CenterSlice to check.

        Returns:
            True if any tracker has marked this slice.
        """
        for k in s.edge.c_attributes.keys():
            if isinstance(k, str) and k.startswith(_TRACKER_KEY_PREFIX):
                return True
        return False

    @staticmethod
    def get_slice_tracker_color(s: CenterSlice) -> Color | None:
        """Get the tracker color for a marked slice.

        WARNING: This is holder-agnostic. It returns the color from ANY holder
        that has marked this slice. If multiple holders have marked the same
        slice (which shouldn't happen), returns the first one found.

        Use this for display purposes (e.g., renderer showing tracker indicators)
        where holder identity doesn't matter.

        Args:
            s: CenterSlice to check.

        Returns:
            The Color enum if tracked, None otherwise.
        """
        return FaceTracker.get_edge_tracker_color(s.edge)

    @staticmethod
    def get_edge_tracker_color(edge: PartEdge) -> Color | None:
        """Get the tracker color for a PartEdge.

        WARNING: This is holder-agnostic. It returns the color from ANY holder
        that has marked this edge. If multiple holders have marked the same
        edge (which shouldn't happen), returns the first one found.

        Use this for display purposes (e.g., renderer showing tracker indicators)
        where holder identity doesn't matter.

        Args:
            edge: PartEdge to check (from a center slice).

        Returns:
            The Color enum if tracked, None otherwise.
        """
        for key, value in edge.c_attributes.items():
            if isinstance(key, str) and key.startswith(_TRACKER_KEY_PREFIX):
                return value  # Value is the Color enum
        return None

    @property
    def parent(self) -> FacesTrackerHolder:
        return self._parent


    def other_faces(self) -> Iterable[FaceTracker]:
        # boaz: improve this

        return [t for t in self.parent.trackers
                if t.face is not self.face]

    @property
    def opposite(self) -> FaceTracker:
        # boaz: improve it
        for t in self.parent.trackers:
            if t.face.opposite is self.face:
                return t

        raise InternalSWError(f"Cant find opposite for {self} in {self.parent.trackers} ")


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

    def cleanup(self) -> None:
        """No-op - simple trackers don't mark anything."""
        pass


class MarkedFaceTracker(FaceTracker):
    """Tracker that marks a center slice. Needs cleanup.

    Created by factory when a center slice is marked with a tracking key
    in its c_attributes.

    Stores the key used to mark the slice.
    cleanup() searches for and removes that specific key.
    """

    __slots__ = ["_key"]

    def __init__(self, cube: "Cube", parent: FacesTrackerHolder, color: Color, key: str) -> None:
        super().__init__(cube, parent, color)
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
