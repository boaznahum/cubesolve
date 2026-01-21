"""MarkedPartTracker - tracks Parts through cube rotations using slice markers.

Similar to PartSliceTracker but tracks whole Parts (Edge, Corner, Center)
by putting a marker on one of their slices. Assumes operations don't slice
the part (i.e., the slices stay together).

Why This Tracker Exists (Big Cube Problem)
------------------------------------------
For big cubes (4x4, 5x5, etc.), the existing color-based trackers
(EdgeTracker, CornerTracker in Tracker.py) cannot be used because:

1. **Parts don't have unique colors**: In a 4x4 cube, multiple edge wings
   share the same two colors. EdgeTracker.of_color() would find the wrong one.

2. **position_id changes on slice moves**: The color-based tracker uses
   position_id which changes when you do slice moves (M, E, S). This breaks
   tracking during the reduction phase of big cube solving.

3. **colors_id changes on ANY rotation**: Can't use colors_id to track
   because it changes every time you rotate anything.

The MarkedPartTracker solves this by putting a marker on one of the part's
PartEdge.moveable_attributes. This marker moves with the colors during
rotations, so we can always find where our target part "moved" to.

When to Use This Tracker
------------------------
- Tracking Parts (Edge, Corner, Center) through face rotations
- Big cube solving when multiple parts share the same colors
- Any situation where you need to track a specific part instance

Limitations
-----------
- **Cannot track through slice moves**: If you do M, E, S moves, the marker
  stays with one slice while other slices of the part move elsewhere.
  Use PartSliceTracker for individual slices if you need slice moves.

Usage:
    # Single part tracking
    with MarkedPartTracker.of(edge) as t:
        # ... cube rotations (whole cube, face rotations, NOT slice moves) ...
        current = t.part  # finds it by marker

    # Track part via one of its slices (type-safe)
    edge_wing: EdgeWing = ...
    with MarkedPartTracker.of_slice(edge_wing) as t:
        # t.part is typed as Edge (inferred from EdgeWing)
        current_edge = t.part

    # Multiple part tracking
    with MultiPartTracker.of(edges) as mt:
        # ... cube rotations ...
        first = mt[0].part   # access by index
        all_current = mt.parts  # get all current positions
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import ExitStack
from types import TracebackType
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from cube.domain.model._elements import CenterSliceIndex, SliceIndex
from cube.domain.model.Part import Part
from cube.domain.model.PartSlice import PartSlice

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

from cube.domain.model.Center import Center
from cube.domain.model.Corner import Corner
from cube.domain.model.Edge import Edge

P = TypeVar("P", bound=Part)

_MARKED_PART_TRACKER_PREFIX = "_part_track:"


def _possible_edge_indices(original: int, n_slices: int) -> tuple[int, int]:
    """Return the two possible slice indices for an edge after rotation.

    When a face rotates, an edge slice at index x can move to index x or inv(x),
    where inv(x) = n_slices - 1 - x.
    """
    return (original, n_slices - 1 - original)


def _possible_center_indices(original: CenterSliceIndex, n: int) -> tuple[CenterSliceIndex, ...]:
    """Return the four possible slice indices for a center after rotation.

    When a face rotates, a center slice at (r, c) can move to one of four positions
    corresponding to 0°, 90°, 180°, 270° rotations.
    """
    r, c = original
    inv_r = n - 1 - r
    inv_c = n - 1 - c
    return (
        (r, c),           # 0°
        (c, inv_r),       # 90° CW
        (inv_r, inv_c),   # 180°
        (inv_c, r),       # 270° CW
    )


class MarkedPartTracker(Generic[P]):
    """Tracks a Part through cube rotations using markers on slices.

    The tracker marks an edge of one of the part's slices with a unique key.
    The `part` property searches for this marker to find the part
    even after it has moved due to cube rotations.

    Important: This tracker assumes operations don't slice the part.
    Use only with whole-cube rotations (x, y, z) and face rotations,
    NOT with slice moves (M, E, S) that would separate slices.

    Use as a context manager to ensure cleanup:
        with MarkedPartTracker.of(my_edge) as t:
            # ... operations ...
            current = t.part
    """

    __slots__ = ["_cube", "_key", "_part_type", "_slice_index"]

    def __init__(self, part: P, *, mark_slice: PartSlice | None = None) -> None:
        """Create a tracker for the given part.

        Args:
            part: The Part to track (Edge, Corner, or Center).
            mark_slice: Optional specific slice to mark. If None, marks the first slice.
                       When provided via of_slice(), this is the slice that was given.
        """
        # Use object id for unique key - guaranteed unique for object's lifetime
        self._key = f"{_MARKED_PART_TRACKER_PREFIX}{id(self):x}"
        self._cube: Cube = part.cube
        self._part_type: type[P] = type(part)  # type: ignore[assignment]

        # Mark the specified slice or the first slice
        slice_to_mark = mark_slice if mark_slice is not None else next(iter(part.all_slices))
        slice_to_mark.edges[0].moveable_attributes[self._key] = True

        # Store the slice index for optimized search
        self._slice_index: SliceIndex = slice_to_mark.index

    @staticmethod
    def of(part: P) -> MarkedPartTracker[P]:
        """Create a tracker for the given part.

        Args:
            part: The Part to track.

        Returns:
            A MarkedPartTracker context manager.
        """
        return MarkedPartTracker(part)

    @staticmethod
    def of_many(parts: Sequence[P]) -> "MultiPartTracker[P]":
        """Create a multi-tracker for multiple parts.

        Convenience method to avoid importing MultiPartTracker separately.

        Args:
            parts: Sequence of Parts to track.

        Returns:
            A MultiPartTracker context manager.
        """
        return MultiPartTracker(parts)

    @staticmethod
    def of_slice(part_slice: PartSlice[P]) -> "MarkedPartTracker[P]":
        """Create a tracker for the parent Part of a PartSlice.

        This is useful when you have a specific slice (e.g., EdgeWing) and want
        to track the entire Part (e.g., Edge) it belongs to.

        The return type is automatically inferred from the slice type because
        PartSlice is now generic over its parent Part type:
        - EdgeWing (PartSlice[Edge]) -> MarkedPartTracker[Edge]
        - CornerSlice (PartSlice[Corner]) -> MarkedPartTracker[Corner]
        - CenterSlice (PartSlice[Center]) -> MarkedPartTracker[Center]

        Args:
            part_slice: The PartSlice whose parent Part to track.
                       Supports EdgeWing, CornerSlice, CenterSlice.

        Returns:
            A MarkedPartTracker for the parent Part with correct type inference.

        Example:
            edge_wing: EdgeWing = ...
            with MarkedPartTracker.of_slice(edge_wing) as t:
                # t.part is typed as Edge (no overloads needed!)
                current_edge = t.part
        """
        return MarkedPartTracker(part_slice.parent, mark_slice=part_slice)  # type: ignore[arg-type]

    def _get_parts_by_type(self) -> Iterator[Part]:
        """Get only parts of the tracked type from the cube."""
        if issubclass(self._part_type, Edge):
            return iter(self._cube.edges)
        elif issubclass(self._part_type, Corner):
            return iter(self._cube.corners)
        elif issubclass(self._part_type, Center):
            return iter(self._cube.centers)
        else:
            raise RuntimeError(f"Unknown part type: {self._part_type}")

    def _valid_slice_indices(self) -> frozenset[SliceIndex]:
        """Get the set of valid slice indices where the marker could be.

        Optimization: After rotations, the marker can only be at specific indices:
        - Corner: Always index 0 (corners have only one slice)
        - Edge: index x or inv(x) where inv(x) = n_slices - 1 - x
        - Center: 4 positions from rotating (r, c) by 0°, 90°, 180°, 270°
        """
        if isinstance(self._slice_index, int):
            # Edge slice index
            return frozenset(_possible_edge_indices(self._slice_index, self._cube.n_slices))
        else:
            # Center slice index (tuple)
            return frozenset(_possible_center_indices(self._slice_index, self._cube.n_slices))

    @property
    def part(self) -> P:
        """Find and return the tracked part by searching for the marker.

        Optimized to only search the relevant part type and valid slice indices.

        Returns:
            The tracked Part.

        Raises:
            RuntimeError: If the tracked part cannot be found.
        """
        valid_indices = self._valid_slice_indices()

        for part in self._get_parts_by_type():
            for s in part.all_slices:
                if s.index not in valid_indices:
                    continue
                for edge in s.edges:
                    if self._key in edge.moveable_attributes:
                        return part  # type: ignore[return-value]

        raise RuntimeError(f"Tracked part not found with key {self._key}")

    def cleanup(self) -> None:
        """Remove the marker from the part.

        Optimized to only search the relevant part type and valid slice indices.
        """
        valid_indices = self._valid_slice_indices()

        for part in self._get_parts_by_type():
            for s in part.all_slices:
                if s.index not in valid_indices:
                    continue
                for edge in s.edges:
                    if self._key in edge.moveable_attributes:
                        del edge.moveable_attributes[self._key]
                        return

    def __enter__(self) -> MarkedPartTracker[P]:
        """Enter context manager."""
        return self

    def __exit__(self, _exc_type: object, _exc_val: object, _exc_tb: object) -> None:
        """Exit context manager - cleanup the marker."""
        self.cleanup()


class MultiPartTracker(Generic[P]):
    """Track multiple Parts through cube rotations.

    Uses ExitStack internally for proper exception handling and cleanup order.

    Usage:
        with MultiPartTracker.of(parts) as mt:
            # ... cube rotations ...
            first = mt[0].part   # access tracker by index
            all_current = mt.parts  # get all current positions
    """

    __slots__ = ["_trackers", "_stack"]

    def __init__(self, parts: Sequence[P]) -> None:
        """Create trackers for multiple parts.

        Args:
            parts: Sequence of Parts to track.
        """
        self._stack = ExitStack()
        self._trackers: list[MarkedPartTracker[P]] = [
            self._stack.enter_context(MarkedPartTracker(p)) for p in parts
        ]

    @staticmethod
    def of(parts: Sequence[P]) -> MultiPartTracker[P]:
        """Create a multi-tracker for the given parts.

        Args:
            parts: Sequence of Parts to track.

        Returns:
            A MultiPartTracker context manager.
        """
        return MultiPartTracker(parts)

    @overload
    def __getitem__(self, index: int) -> MarkedPartTracker[P]: ...

    @overload
    def __getitem__(self, index: slice) -> list[MarkedPartTracker[P]]: ...

    def __getitem__(self, index: int | slice) -> MarkedPartTracker[P] | list[MarkedPartTracker[P]]:
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

    def __iter__(self) -> Iterator[MarkedPartTracker[P]]:
        """Iterate over trackers."""
        return iter(self._trackers)

    @property
    def parts(self) -> list[P]:
        """Get all tracked parts at their current positions.

        Returns:
            List of all tracked Parts.
        """
        return [t.part for t in self._trackers]

    def __enter__(self) -> MultiPartTracker[P]:
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
