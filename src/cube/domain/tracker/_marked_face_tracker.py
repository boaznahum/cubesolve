"""Marked face tracker - marks center slice with tracking key, needs cleanup.

MarkedFaceTracker is used when a center slice is marked with a tracking key.
Created by factory when tracking is established.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.model import CenterSlice, Color
from cube.domain.model.Face import Face
from cube.domain.model.FaceName import FaceName
from cube.domain.tracker import _helper
from cube.domain.tracker._face_trackers import FaceTracker

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder


class MarkedFaceTracker(FaceTracker):
    """Tracker that marks a center slice. Needs cleanup.

    Created by factory when a center slice is marked with a tracking key
    in its c_attributes.

    Stores the key used to mark the slice.
    cleanup() searches for and removes that specific key.
    """

    __slots__ = ["_key", "_enable_track_piece_caching", "_cache_face", "_cache_piece"]

    def __init__(self, cube: "Cube", parent: FacesTrackerHolder, color: Color, key: str) -> None:
        super().__init__(cube, parent, color)
        self._key = key
        self._enable_track_piece_caching = cube.config.face_tracker.enable_track_piece_caching
        self._cache_face : Face | None = None
        self._cache_piece : CenterSlice | None = None

    @property
    def face(self) -> Face:
        """Find face containing the marked slice."""


        caching = self._enable_track_piece_caching

        cube = self._cube
        if not caching:
            # old behavior
            def _slice_pred(s: CenterSlice) -> bool:
                return self._key in s.edge.moveable_attributes

            def _face_pred(_f: Face) -> bool:
                return _f.cube.cqr.find_slice_in_face_center(_f, _slice_pred) is not None

            return self._cube.cqr.find_face(_face_pred)


        else:
            # caching doesnt work

            def _slice_pred(s: CenterSlice) -> bool:
                return self._key in s.edge.moveable_attributes


            cs = self._cache_piece
            if cs is not None and _slice_pred(cs):
                return cs.face

            found_cs: CenterSlice = cube.cqr.find_center_slice(_slice_pred)

            # even if not caching
            self._cache_piece = found_cs

            return found_cs.face


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
        the marked center slice to a different physical face.

        OPTIMIZATION: Check if marker is already on the correct face.
        If yes, skip cleanup/re-mark (operation didn't move centers or they
        ended up back where they started).

        Args:
            saved_face_name: The FaceName of the physical face to restore to.
        """
        # Smart check: If already on correct face, no action needed
        if self.face.name == saved_face_name:
            return  # Marker already correct - skip cleanup/re-mark

        # Marker moved - restore it:
        # 1. Cleanup existing marker (wherever it ended up)
        self.cleanup(force_remove_visible=True)  # force because we're putting a new one

        # 2. Find face by saved name
        face = self._cube.face(saved_face_name)

        # 3. Mark a center slice on that face with our tracking key
        _helper.find_and_track_slice(face, self._key, self._color)
