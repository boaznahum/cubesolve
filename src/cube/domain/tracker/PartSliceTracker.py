"""PartSlice tracker - tracks PartSlices through cube rotations.

Usage:
    # Single slice tracking
    with PartSliceTracker.with_tracker(edge_wing) as t:
        # ... cube rotations ...
        current = t.slice  # finds it by marker

    # Via convenience method on PartSlice
    with edge_wing.tracker() as t:
        current = t.slice

    # Multiple slice tracking
    with MultiSliceTracker.with_trackers(slices) as mt:
        # ... cube rotations ...
        first = mt[0].slice   # access by index
        all_current = mt.slices  # get all current positions
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import ExitStack
from types import TracebackType
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from cube.domain.model._elements import CenterSliceIndex, SliceIndex
from cube.domain.model.PartSlice import CenterSlice, CornerSlice, EdgeWing, PartSlice

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

PS = TypeVar("PS", bound=PartSlice)

_PART_SLICE_TRACKER_PREFIX = "_slice_track:"


def _possible_edge_indices(original: int, n_slices: int) -> tuple[int, int]:
    """Return the two possible slice indices for an edge after rotation."""
    return (original, n_slices - 1 - original)


def _possible_center_indices(original: CenterSliceIndex, n: int) -> tuple[CenterSliceIndex, ...]:
    """Return the four possible slice indices for a center after rotation."""
    r, c = original
    inv_r = n - 1 - r
    inv_c = n - 1 - c
    return (
        (r, c),           # 0°
        (c, inv_r),       # 90° CW
        (inv_r, inv_c),   # 180°
        (inv_c, r),       # 270° CW
    )


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

    __slots__ = ["_cube", "_key", "_slice_type", "_slice_index"]

    def __init__(self, part_slice: PS) -> None:
        """Create a tracker for the given part slice.

        Args:
            part_slice: The PartSlice to track.
        """
        # Use object id for unique key - guaranteed unique for object's lifetime
        self._key = f"{_PART_SLICE_TRACKER_PREFIX}{id(self):x}"
        self._cube: Cube = part_slice.cube
        self._slice_type: type[PS] = type(part_slice)  # type: ignore[assignment]
        self._slice_index: SliceIndex = part_slice.index

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

    @staticmethod
    def with_trackers(slices: Sequence[PS]) -> "MultiSliceTracker[PS]":
        """Create a multi-tracker for multiple slices.

        Convenience method to avoid importing MultiSliceTracker separately.

        Args:
            slices: Sequence of PartSlices to track.

        Returns:
            A MultiSliceTracker context manager.
        """
        return MultiSliceTracker(slices)

    def _get_slices_by_type(self) -> Iterator[PartSlice]:
        """Get only slices of the tracked type from the cube."""
        if issubclass(self._slice_type, EdgeWing):
            for edge in self._cube.edges:
                yield from edge.all_slices
        elif issubclass(self._slice_type, CornerSlice):
            for corner in self._cube.corners:
                yield from corner.all_slices
        elif issubclass(self._slice_type, CenterSlice):
            for center in self._cube.centers:
                yield from center.all_slices
        else:
            raise RuntimeError(f"Unknown slice type: {self._slice_type}")

    def _valid_slice_indices(self) -> frozenset[SliceIndex]:
        """Get the set of valid slice indices where the marker could be.

        Optimization: After rotations, the marker can only be at specific indices:
        - Corner: Always index 0 (corners have only one slice)
        - Edge: index x or inv(x) where inv(x) = n_slices - 1 - x
        - Center: 4 positions from rotating (r, c) by 0°, 90°, 180°, 270°
        """
        if isinstance(self._slice_index, int):
            # Edge or Corner slice index
            return frozenset(_possible_edge_indices(self._slice_index, self._cube.n_slices))
        else:
            # Center slice index (tuple)
            return frozenset(_possible_center_indices(self._slice_index, self._cube.n_slices))

    @property
    def slice(self) -> PS:
        """Find and return the tracked slice by searching for the marker.

        Optimized to only search the relevant slice type and valid indices.

        Returns:
            The tracked PartSlice.

        Raises:
            RuntimeError: If the tracked slice cannot be found.
        """
        valid_indices = self._valid_slice_indices()

        for s in self._get_slices_by_type():
            if s.index not in valid_indices:
                continue
            for edge in s.edges:
                if self._key in edge.moveable_attributes:
                    return s  # type: ignore[return-value]

        raise RuntimeError(f"Tracked slice not found with key {self._key}")

    def cleanup(self) -> None:
        """Remove the marker from the slice.

        Optimized to only search the relevant slice type and valid indices.
        """
        valid_indices = self._valid_slice_indices()

        for s in self._get_slices_by_type():
            if s.index not in valid_indices:
                continue
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


class MultiSliceTracker(Generic[PS]):
    """Track multiple PartSlices through cube rotations.

    Uses ExitStack internally for proper exception handling and cleanup order.

    Usage:
        with MultiSliceTracker.with_trackers(slices) as mt:
            # ... cube rotations ...
            first = mt[0].slice   # access tracker by index
            all_current = mt.slices  # get all current positions

    TODO: Support cleaner iteration without nested with/for:
        for t in MultiSliceTracker.with_trackers(slices):
            current = t.slice
        # auto cleanup when loop ends
    """

    __slots__ = ["_trackers", "_stack"]

    def __init__(self, slices: Sequence[PS]) -> None:
        """Create trackers for multiple slices.

        Args:
            slices: Sequence of PartSlices to track.
        """
        self._stack = ExitStack()
        self._trackers: list[PartSliceTracker[PS]] = [
            self._stack.enter_context(PartSliceTracker(s)) for s in slices
        ]

    @staticmethod
    def with_trackers(slices: Sequence[PS]) -> MultiSliceTracker[PS]:
        """Create a multi-tracker for the given slices.

        Args:
            slices: Sequence of PartSlices to track.

        Returns:
            A MultiSliceTracker context manager.
        """
        return MultiSliceTracker(slices)

    @overload
    def __getitem__(self, index: int) -> PartSliceTracker[PS]: ...

    @overload
    def __getitem__(self, index: slice) -> list[PartSliceTracker[PS]]: ...

    def __getitem__(self, index: int | slice) -> PartSliceTracker[PS] | list[PartSliceTracker[PS]]:
        """Access tracker by index.

        Args:
            index: Index or slice to access.

        Returns:
            The tracker at the given index, or list of trackers for a slice.
        """
        return self._trackers[index]

    def __len__(self) -> int:
        """Return number of trackers."""
        return len(self._trackers)

    def __iter__(self) -> Iterator[PartSliceTracker[PS]]:
        """Iterate over trackers."""
        return iter(self._trackers)

    @property
    def slices(self) -> list[PS]:
        """Get all tracked slices at their current positions.

        Returns:
            List of all tracked PartSlices.
        """
        return [t.slice for t in self._trackers]

    def __enter__(self) -> MultiSliceTracker[PS]:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        """Exit context manager - delegates to ExitStack for proper cleanup."""
        return self._stack.__exit__(exc_type, exc_val, exc_tb)
