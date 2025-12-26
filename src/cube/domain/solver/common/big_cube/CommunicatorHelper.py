"""
Communicator Helper for NxN Big Cubes
=====================================

This module provides utilities for working with the block commutator algorithm
used to solve center pieces on big cubes (NxN, where N > 3).

The Block Commutator Algorithm
------------------------------
The core algorithm is: [M', F, M', F', M, F, M, F']

This is a BALANCED commutator that 3-cycles center pieces:
- A (from UP) → C position (on Front)
- C (from Front) → B position (on Front after rotation)
- B (from Front) → A position (on UP)

The helper encapsulates the mathematical operations needed for:
- Index inversion (mirroring)
- Point rotation (clockwise/counter-clockwise)
- Coordinate mapping between faces (Front, Up, Back)
- Block operations (2D ranges, intersections, validity)

Design Philosophy
-----------------
This is a pure query class with no side effects. All methods are
coordinate transformations that don't modify the cube state.

Coordinate System
-----------------
For center pieces on a face:
- (0, 0) = top-left corner
- Row increases downward (0 to n_slices-1)
- Column increases rightward (0 to n_slices-1)
- n_slices = cube.size - 2 (e.g., 5x5 cube has 3x3 center grid)

Example for 5x5 cube (n_slices=3):
::

        Column →
        0   1   2
      ┌───┬───┬───┐
    0 │0,0│0,1│0,2│  ← Row 0
      ├───┼───┼───┤
    1 │1,0│1,1│1,2│  ← Row 1
      ├───┼───┼───┤
    2 │2,0│2,1│2,2│  ← Row 2
      └───┴───┴───┘

Key Transformations
-------------------
- inv(i): Mirror index → n_slices - 1 - i
- Clockwise rotation: (r, c) → (inv(c), r)
- Counter-clockwise: (r, c) → (c, inv(r))
- Back face mapping: (r, c) → (inv(r), inv(c))

See Also
--------
- NxNCenters : Uses these utilities for solving centers
- NxNEdges : Uses similar coordinate logic for edges
- docs/cube-coordinates-helper.md : Development tracking document
"""

from typing import Iterator, Tuple

from cube.domain.model.Cube import Cube

# Type aliases for clarity
Point = Tuple[int, int]
Block = Tuple[Point, Point]


class CommunicatorHelper:
    """
    Helper for the block commutator algorithm on NxN cubes.

    The block commutator [M', F, M', F', M, F, M, F'] is the core algorithm
    for 3-cycling center pieces between faces. This helper provides all the
    coordinate mathematics needed to set up and execute the commutator.

    The commutator 3-cycles pieces:
    ::

               UP (Source)
              ┌───┬───┬───┐
              │   │ A │   │  ← Piece A moves to C
              ├───┼───┼───┤
              │   │   │   │
              └───┴───┴───┘

             FRONT (Target)
              ┌───┬───┬───┐
              │   │ C │   │  ← C gets piece from A
              ├───┼───┼───┤
              │   │   │   │
              ├───┼───┼───┤
              │   │ B │   │  ← B moves to A position
              └───┴───┴───┘

    Parameters
    ----------
    cube : Cube
        The cube instance (used for n_slices and size information)

    Attributes
    ----------
    cube : Cube
        Reference to the cube
    n_slices : int
        Number of center slices per dimension (cube.size - 2)

    Examples
    --------
    >>> from cube.domain.model.Cube import Cube
    >>> cube = Cube(7, sp=service_provider)  # 7x7 cube
    >>> helper = CommunicatorHelper(cube)
    >>> helper.n_slices
    5

    >>> # Invert index (fundamental for all operations)
    >>> helper.inv(0)  # → 4
    >>> helper.inv(2)  # → 2 (middle stays)

    >>> # Rotate point clockwise (for F rotation setup)
    >>> helper.rotate_point_clockwise((0, 0))  # → (4, 0)

    >>> # Map coordinates to back face
    >>> helper.point_on_source(is_back=True, rc=(0, 0))  # → (4, 4)
    """

    def __init__(self, cube: Cube) -> None:
        """
        Initialize the helper with a cube reference.

        Parameters
        ----------
        cube : Cube
            The cube instance to work with
        """
        self._cube = cube

    @property
    def cube(self) -> Cube:
        """Get the cube instance."""
        return self._cube

    @property
    def n_slices(self) -> int:
        """
        Number of center slices per dimension.

        For an NxN cube, this is N-2.
        Example: 7x7 cube → 5 slices
        """
        return self._cube.n_slices

    def inv(self, i: int) -> int:
        """
        Invert (mirror) an index.

        This is the fundamental operation for coordinate mirroring.
        inv(i) = n_slices - 1 - i

        Parameters
        ----------
        i : int
            Index to invert (0 to n_slices-1)

        Returns
        -------
        int
            The mirrored index

        Examples
        --------
        For 7x7 cube (n_slices=5):
        >>> helper.inv(0)  # → 4
        >>> helper.inv(1)  # → 3
        >>> helper.inv(2)  # → 2 (middle)
        >>> helper.inv(4)  # → 0

        Note: inv(inv(i)) == i (self-inverse)
        """
        return self._cube.inv(i)

    def rotate_point_clockwise(self, rc: Point, n: int = 1) -> Point:
        """
        Rotate a point clockwise around the center of the face.

        The transformation for one 90° clockwise rotation is:
        (r, c) → (inv(c), r)

        Parameters
        ----------
        rc : Point
            The (row, column) coordinates to rotate
        n : int, optional
            Number of 90° rotations (default 1)

        Returns
        -------
        Point
            The rotated coordinates

        Examples
        --------
        For 5x5 cube (n_slices=3):
        ::

            Before:           After 90° CW:
              0  1  2           0  1  2
            ┌──┬──┬──┐        ┌──┬──┬──┐
            │A │  │  │ 0      │  │  │A │ 0
            ├──┼──┼──┤        ├──┼──┼──┤
            │  │  │  │ 1  →   │  │  │  │ 1
            ├──┼──┼──┤        ├──┼──┼──┤
            │  │  │  │ 2      │  │  │  │ 2
            └──┴──┴──┘        └──┴──┴──┘

            A at (0,0) → (inv(0), 0) = (2, 0)

        >>> helper.rotate_point_clockwise((0, 0))
        (2, 0)
        >>> helper.rotate_point_clockwise((0, 0), n=2)  # 180°
        (2, 2)
        """
        for _ in range(n % 4):
            rc = (self.inv(rc[1]), rc[0])
        return rc

    def rotate_point_counterclockwise(self, rc: Point, n: int = 1) -> Point:
        """
        Rotate a point counter-clockwise around the center of the face.

        The transformation for one 90° counter-clockwise rotation is:
        (r, c) → (c, inv(r))

        Parameters
        ----------
        rc : Point
            The (row, column) coordinates to rotate
        n : int, optional
            Number of 90° rotations (default 1)

        Returns
        -------
        Point
            The rotated coordinates

        Examples
        --------
        >>> helper.rotate_point_counterclockwise((0, 0))
        (0, 2)  # For n_slices=3
        >>> helper.rotate_point_counterclockwise((2, 0))
        (0, 0)
        """
        for _ in range(n % 4):
            rc = (rc[1], self.inv(rc[0]))
        return rc

    def point_on_source(self, is_back: bool, rc: Point) -> Point:
        """
        Convert front-face coordinates to source-face coordinates.

        When working with the UP face, coordinates are the same as front.
        When working with the BACK face, coordinates are mirrored in both axes.

        Parameters
        ----------
        is_back : bool
            True if source is the back face, False for up face
        rc : Point
            Coordinates in front-face reference frame

        Returns
        -------
        Point
            Coordinates in source-face reference frame

        Examples
        --------
        >>> helper.point_on_source(is_back=False, rc=(0, 0))
        (0, 0)  # UP has same coords
        >>> helper.point_on_source(is_back=True, rc=(0, 0))
        (4, 4)  # For n_slices=5, BACK is mirrored

        Visual:
        ::

            Front (reference):    Back (looking through cube):
              0  1  2               2  1  0   ← cols reversed
            ┌──┬──┬──┐            ┌──┬──┬──┐
            │A │  │  │ 0          │  │  │  │ 2  ← rows reversed
            ├──┼──┼──┤            ├──┼──┼──┤
            │  │  │  │ 1    →     │  │  │  │ 1
            ├──┼──┼──┤            ├──┼──┼──┤
            │  │  │  │ 2          │  │  │A'│ 0
            └──┴──┴──┘            └──┴──┴──┘

            A(0,0) on front → A'(2,2) on back
        """
        if is_back:
            return (self.inv(rc[0]), self.inv(rc[1]))
        else:
            return rc

    def point_on_target(self, source_is_back: bool, rc: Point) -> Point:
        """
        Convert source-face coordinates to target-face (front) coordinates.

        This is the inverse of point_on_source.

        Parameters
        ----------
        source_is_back : bool
            True if source is the back face
        rc : Point
            Coordinates in source-face reference frame

        Returns
        -------
        Point
            Coordinates in front-face (target) reference frame

        Notes
        -----
        For this operation, the transformation is symmetric:
        point_on_target(is_back, rc) == point_on_source(is_back, rc)

        This is because mirroring is self-inverse:
        inv(inv(x)) == x
        """
        if source_is_back:
            return (self.inv(rc[0]), self.inv(rc[1]))
        else:
            return rc

    def block_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Block:
        """
        Convert a block (rectangle) from front to source coordinates.

        Parameters
        ----------
        is_back : bool
            True if source is back face
        rc1 : Point
            First corner of block
        rc2 : Point
            Second corner of block

        Returns
        -------
        Block
            The block in source coordinates
        """
        return (self.point_on_source(is_back, rc1),
                self.point_on_source(is_back, rc2))

    @staticmethod
    def range_2d(rc1: Point, rc2: Point) -> Iterator[Point]:
        """
        Iterate over all points in a 2D block (rectangle).

        Iterates row by row, column by column (row-major order).
        Handles corners in any order (normalizes internally).

        Parameters
        ----------
        rc1 : Point
            First corner of block
        rc2 : Point
            Second corner of block

        Yields
        ------
        Point
            Each (row, column) in the block

        Examples
        --------
        >>> list(helper.range_2d((0, 0), (1, 1)))
        [(0, 0), (0, 1), (1, 0), (1, 1)]

        >>> list(helper.range_2d((1, 1), (0, 0)))  # Same result
        [(0, 0), (0, 1), (1, 0), (1, 1)]
        """
        r1, c1 = rc1
        r2, c2 = rc2

        # Normalize: ensure r1 <= r2 and c1 <= c2
        if r1 > r2:
            r1, r2 = r2, r1
        if c1 > c2:
            c1, c2 = c2, c1

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                yield (r, c)

    def range_2d_on_source(self, is_back: bool, rc1: Point, rc2: Point) -> Iterator[Point]:
        """
        Iterate over block points, converting to source coordinates.

        Parameters
        ----------
        is_back : bool
            True if source is back face
        rc1 : Point
            First corner (front coords)
        rc2 : Point
            Second corner (front coords)

        Yields
        ------
        Point
            Each point in source coordinates
        """
        src_rc1 = self.point_on_source(is_back, rc1)
        src_rc2 = self.point_on_source(is_back, rc2)
        yield from self.range_2d(src_rc1, src_rc2)

    @staticmethod
    def block_size(rc1: Point, rc2: Point) -> int:
        """
        Calculate the number of cells in a block.

        Parameters
        ----------
        rc1 : Point
            First corner
        rc2 : Point
            Second corner

        Returns
        -------
        int
            Number of cells (width * height)

        Examples
        --------
        >>> helper.block_size((0, 0), (0, 0))
        1
        >>> helper.block_size((0, 0), (1, 1))
        4
        >>> helper.block_size((0, 0), (2, 1))
        6
        """
        return (abs(rc2[0] - rc1[0]) + 1) * (abs(rc2[1] - rc1[1]) + 1)

    @staticmethod
    def block_dimensions(rc1: Point, rc2: Point) -> Tuple[int, int]:
        """
        Get the dimensions (height, width) of a block.

        Parameters
        ----------
        rc1 : Point
            First corner
        rc2 : Point
            Second corner

        Returns
        -------
        Tuple[int, int]
            (height, width) of the block
        """
        return (abs(rc2[0] - rc1[0]) + 1, abs(rc2[1] - rc1[1]) + 1)

    @staticmethod
    def ranges_intersect_1d(range1: Tuple[int, int], range2: Tuple[int, int]) -> bool:
        """
        Check if two 1D ranges intersect.

        Parameters
        ----------
        range1 : Tuple[int, int]
            First range (start, end) - order doesn't matter
        range2 : Tuple[int, int]
            Second range (start, end) - order doesn't matter

        Returns
        -------
        bool
            True if ranges overlap

        Examples
        --------
        >>> helper.ranges_intersect_1d((0, 2), (1, 3))
        True  # Overlap at 1-2
        >>> helper.ranges_intersect_1d((0, 1), (2, 3))
        False  # No overlap
        >>> helper.ranges_intersect_1d((0, 2), (2, 3))
        True  # Touch at 2
        """
        x1, x2 = range1
        x3, x4 = range2

        # Normalize ranges
        if x1 > x2:
            x1, x2 = x2, x1
        if x3 > x4:
            x3, x4 = x4, x3

        # Ranges don't intersect if one is completely before the other
        if x3 > x2:
            return False
        if x4 < x1:
            return False

        return True

    def get_four_symmetric_points(self, r: int, c: int) -> Iterator[Point]:
        """
        Get the four rotationally symmetric points for a given position.

        For any point (r, c), there are 4 symmetric positions under 90° rotations.
        Exception: the center point (for odd n_slices) maps to itself 4 times.

        Parameters
        ----------
        r : int
            Row index
        c : int
            Column index

        Yields
        ------
        Point
            Each of the 4 symmetric positions

        Examples
        --------
        For 5x5 cube (n_slices=3):
        >>> list(helper.get_four_symmetric_points(0, 0))
        [(0, 0), (0, 2), (2, 2), (2, 0)]

        >>> list(helper.get_four_symmetric_points(1, 1))  # Center
        [(1, 1), (1, 1), (1, 1), (1, 1)]
        """
        for _ in range(4):
            yield (r, c)
            r, c = c, self.inv(r)

    def is_center_point(self, r: int, c: int) -> bool:
        """
        Check if a point is the center of an odd-sized grid.

        Parameters
        ----------
        r : int
            Row index
        c : int
            Column index

        Returns
        -------
        bool
            True if this is the center point of an odd grid
        """
        if self.n_slices % 2 == 0:
            return False  # Even grids have no single center
        mid = self.n_slices // 2
        return r == mid and c == mid

    def visualize_grid(self, highlights: dict[Point, str] | None = None) -> str:
        """
        Create an ASCII visualization of the center grid.

        Parameters
        ----------
        highlights : dict[Point, str], optional
            Points to highlight with specific characters

        Returns
        -------
        str
            ASCII art representation of the grid

        Examples
        --------
        >>> print(helper.visualize_grid({(0, 0): 'A', (2, 2): 'B'}))
            0   1   2
          ┌───┬───┬───┐
        0 │ A │   │   │
          ├───┼───┼───┤
        1 │   │   │   │
          ├───┼───┼───┤
        2 │   │   │ B │
          └───┴───┴───┘
        """
        if highlights is None:
            highlights = {}

        n = self.n_slices
        lines = []

        # Header with column numbers
        header = "   " + "".join(f" {c}  " for c in range(n))
        lines.append(header)

        # Top border
        lines.append("  ┌" + "───┬" * (n - 1) + "───┐")

        for r in range(n):
            # Row with cells
            row_str = f"{r} │"
            for c in range(n):
                char = highlights.get((r, c), " ")
                row_str += f" {char} │"
            lines.append(row_str)

            # Row separator or bottom border
            if r < n - 1:
                lines.append("  ├" + "───┼" * (n - 1) + "───┤")
            else:
                lines.append("  └" + "───┴" * (n - 1) + "───┘")

        return "\n".join(lines)
