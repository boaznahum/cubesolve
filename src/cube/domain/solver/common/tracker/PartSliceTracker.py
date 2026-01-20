"""PartSlice tracker - tracks a specific PartSlice through cube rotations.

Usage:
    # Via static method
    with PartSliceTracker.with_tracker(edge_wing) as t:
        # ... cube rotations ...
        current = t.slice  # finds it by marker

    # Via convenience method on PartSlice
    with edge_wing.tracker() as t:
        current = t.slice
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from cube.domain.model.PartSlice import PartSlice

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

PS = TypeVar("PS", bound=PartSlice)

_PART_SLICE_TRACKER_PREFIX = "_part_slice_track:"


class PartSliceTracker(Generic[PS]):
    """Tracks a PartSlice through cube rotations using markers.

    The tracker marks one of the slice's edges with a unique key.
    The `slice` property searches for this marker to find the slice
    even after it has moved due to cube rotations.

    Use as a context manager to ensure cleanup:
        with PartSliceTracker.with_tracker(my_slice) as t:
            # ... operations ...
            current = t.slice
    """

    __slots__ = ["_cube", "_key", "_slice_type"]

    _global_id: int = 0

    def __init__(self, part_slice: PS) -> None:
        """Create a tracker for the given part slice.

        Args:
            part_slice: The PartSlice to track.
        """
        PartSliceTracker._global_id += 1
        self._key = f"{_PART_SLICE_TRACKER_PREFIX}{PartSliceTracker._global_id}"
        self._cube: Cube = part_slice.cube
        self._slice_type: type[PS] = type(part_slice)  # type: ignore[assignment]

        # Mark the first edge
        part_slice.edges[0].moveable_attributes[self._key] = True

    @staticmethod
    def with_tracker(part_slice: PS) -> PartSliceTracker[PS]:
        """Create a tracker for the given part slice.

        Args:
            part_slice: The PartSlice to track.

        Returns:
            A PartSliceTracker context manager.
        """
        return PartSliceTracker(part_slice)

    @property
    def slice(self) -> PS:
        """Find and return the tracked slice by searching for the marker.

        TODO: Add caching for performance optimization.

        Returns:
            The tracked PartSlice.

        Raises:
            RuntimeError: If the tracked slice cannot be found.
        """
        for s in self._cube.get_all_part_slices():
            if isinstance(s, self._slice_type):
                for edge in s.edges:
                    if self._key in edge.moveable_attributes:
                        return s  # type: ignore[return-value]

        raise RuntimeError(f"Tracked slice not found with key {self._key}")

    def cleanup(self) -> None:
        """Remove the marker from the slice."""
        for s in self._cube.get_all_part_slices():
            for edge in s.edges:
                if self._key in edge.moveable_attributes:
                    del edge.moveable_attributes[self._key]
                    return

    def __enter__(self) -> PartSliceTracker[PS]:
        """Enter context manager."""
        return self

    def __exit__(self, _exc_type: object, _exc_val: object, _exc_tb: object) -> None:
        """Exit context manager - cleanup the marker."""
        self.cleanup()
