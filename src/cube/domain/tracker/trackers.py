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

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.model import CenterSlice, Color
from cube.domain.model.CubeQueries2 import Pred
from cube.domain.model.Face import Face
from cube.domain.model.FaceName import FaceName
from cube.domain.model.PartEdge import PartEdge
from cube.domain.tracker import _helper
from cube.domain.tracker._helper import _TRACKER_VISUAL_MARKER

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder

# Key prefix for logical tracker data in moveable_attributes.
# Format: "_nxn_centers_track:h{holder_id}:{color}{unique_id}"
# This is the actual tracking mechanism — determines which face owns which color.
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
    def face_name(self) -> FaceName:
        return self.face.name

    @property
    def color(self) -> Color:
        return self._color

    @property
    def color_at_face_str(self) -> str:
        """Return color@face string representation of the tracked face.

        Delegates to the underlying Face.color_at_face_str property.

        Returns:
            String in format "COLOR@FACE" like "WHITE@D"
        """
        return self.face.color_at_face_str

    def __str__(self) -> str:
        return f"{self.color.name}@{self.face}"

    def __repr__(self) -> str:
        return self.__str__()

    @abstractmethod
    def cleanup(self, force_remove_visible:bool = False) -> None:
        """Remove any marks this tracker created. Abstract - must be implemented."""
        pass

    def save_physical_face(self) -> FaceName:
        """Save current physical face for later restoration.

        Returns the FaceName of the physical face this tracker is currently on.
        Used by preserve_physical_faces() context manager.

        Returns:
            The FaceName of the current physical face.
        """
        return self.face.name

    def restore_to_physical_face(self, saved_face_name: FaceName) -> None:
        """Restore tracker to the saved physical face.

        Called after operations that may move markers (like commutators).
        Each tracker type handles restoration according to its own rules:
        - SimpleFaceTracker: no-op (predicates remain stable)
        - MarkedFaceTracker: cleanup + re-mark on saved face

        Args:
            saved_face_name: The FaceName saved by save_physical_face().
        """
        # Default: no-op for SimpleFaceTracker (predicates are stable)
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
        for k in s.edge.moveable_attributes.keys():
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
        for key, value in edge.moveable_attributes.items():
            if isinstance(key, str) and key.startswith(_TRACKER_KEY_PREFIX):
                return value  # Value is the Color enum
        return None

    @property
    def parent(self) -> FacesTrackerHolder:
        return self._parent


    def other_faces(self) -> Iterable[FaceTracker]:
        # boaz: improve this

        return [t for t in self.parent.trackers
                if t is not self]

    def adjusted_faces(self) -> Iterable[FaceTracker]:
        # boaz: improve this

        return [t for t in self.parent.trackers
                if t is not self and t is not self.opposite]

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

    def cleanup(self, force_remove_visible:bool = False) -> None:
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
            return self._key in s.edge.moveable_attributes

        def _face_pred(_f: Face) -> bool:
            return _f.cube.cqr.find_slice_in_face_center(_f, _slice_pred) is not None

        return self._cube.cqr.find_face(_face_pred)


    def cleanup(self, force_remove_visible:bool = False) -> None:
        """Search for and remove the specific key and visual marker from the marked slice."""
        mm = self._cube.sp.marker_manager
        for f in self._cube.faces:
            for s in f.center.all_slices:
                if self._key in s.edge.moveable_attributes:
                    del s.edge.moveable_attributes[self._key]
                    if force_remove_visible or not self._cube.config.face_tracker.leave_last_annotation:
                        mm.remove_marker(s.edge, _helper.tracer_visual_key(self._key), moveable=True)
                    return

    def restore_to_physical_face(self, saved_face_name: FaceName) -> None:
        """Remove current marker, create new marker on saved physical face.

        This is called after operations (like commutators) that may have moved
        the marked center slice to a different physical face. We:
        1. Cleanup the existing marker (wherever it ended up)
        2. Find the physical face by saved name
        3. Mark a center slice on that face with our tracking key

        Args:
            saved_face_name: The FaceName of the physical face to restore to.
        """
        # 1. Cleanup existing marker, also visible one
        self.cleanup(force_remove_visible=True) # force because we are going to put new one

        # 2. Find face by saved name
        face = self._cube.face(saved_face_name)

        _helper.find_and_track_slice(face, self._key, self._color)


