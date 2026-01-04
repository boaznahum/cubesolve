"""
Rubik's Cube Virtual Model
===========================

This module implements a virtual NxN Rubik's Cube that supports standard face rotations,
slice operations, and whole-cube rotations. The model works for any cube size from 3x3
to NxN (including 4x4, 5x5, etc.).

Core Design Philosophy
----------------------
Unlike physical cubes where pieces move in 3D space, this model keeps all parts at
FIXED POSITIONS and rotates their COLORS instead. This design decision:

- Simplifies state management (no 3D coordinates needed)
- Enables faster queries (parts have predictable locations)
- Makes validation easier (graph structure never changes)
- Provides natural algorithm representation

Object Hierarchy
----------------
::

    Cube
     ├─ Face (6) - F, B, L, R, U, D
     │   ├─ Edge (4 per face, shared with adjacent faces)
     │   ├─ Corner (4 per face, shared with 2 adjacent faces)
     │   └─ Center (1 per face, NxN grid for big cubes)
     │
     ├─ 12 Edges (shared between pairs of faces)
     │   └─ EdgeWing slices (N-2 slices per edge)
     │
     ├─ 8 Corners (shared between triples of faces)
     │   └─ CornerSlice (always 1 per corner)
     │
     └─ Slice (3) - M, E, S (middle layers)

Part Sharing
------------
The most important concept: **Parts are shared between faces!**

A single Edge object is referenced by TWO Face objects.
A single Corner object is referenced by THREE Face objects.

Example::

    # The front-up edge is ONE object with TWO references
    front.edge_top is up.edge_bottom  # True!

    # Rotating front changes the edge
    # This AUTOMATICALLY updates up.edge_bottom (same object)

This sharing eliminates the need to manually synchronize adjacent faces.

Quick Start
-----------
::

    # Create a standard 3x3 cube
    >>> from cube.domain.model.Cube import Cube
    >>> cube = Cube(size=3)

    # Perform rotations
    >>> cube.front.rotate(1)   # F move (90° clockwise)
    >>> cube.right.rotate(-1)  # R' move (counter-clockwise)

    # Check state
    >>> cube.solved
    False

    # Find pieces
    >>> from cube.domain.model.cube_boy import Color
    >>> white_red = frozenset([Color.WHITE, Color.RED])
    >>> edge = cube.find_edge_by_color(white_red)

    # Reset
    >>> cube.reset()
    >>> cube.solved
    True

For NxN Cubes
-------------
::

    # Create a 4x4 or 5x5
    >>> cube = Cube(size=4)
    >>> cube.n_slices  # Number of middle slices: size - 2
    2

    # Edges have multiple slices
    >>> edge = cube.front.edge_top
    >>> len(edge._slices)  # 2 slices for 4x4
    2

    # Centers are NxN grids
    >>> center = cube.front.center
    >>> center.get_slice((0, 0))  # Top-left center piece
    CenterSlice(...)

Terminology Mapping
-------------------
==================  ====================
Physical Cube       Code Term
==================  ====================
Sticker             PartEdge
Piece               Part / PartSlice
Edge piece          Edge
Corner piece        Corner
Center piece        Center
Face                Face
Move (F, R, U)      face.rotate(n)
Wide move (Fw)      rotate_face_and_slice()
Slice (M, E, S)     rotate_slice()
==================  ====================

See Also
--------
- ARCHITECTURE.md : Detailed architecture documentation with diagrams
- Face : Individual face with rotation operations
- Part : Base class for edges/corners/centers with identity concepts
- Edge, Corner, Center : Specific part types
- CubeQueries2 : Query operations for finding pieces

Notes
-----
The model uses the BOY (Blue-Orange-Yellow) color scheme by default:
- Front (F) = Blue
- Right (R) = Red
- Up (U) = Yellow
- Left (L) = Orange
- Down (D) = White
- Back (B) = Green
"""

from collections.abc import Iterable, MutableSequence
from typing import TYPE_CHECKING, Collection, Protocol, Tuple

from cube.domain.exceptions import InternalSWError
from cube.utils.config_protocol import ConfigProtocol, IServiceProvider

from ._elements import AxisName, PartColorsID
from .PartSlice import CornerSlice, EdgeWing, PartSlice
from .Center import Center
from .Corner import Corner
from cube.domain.model.geometric.cube_boy import Color, FaceName
from cube.domain.model.geometric import CubeLayout, create_layout
from .cube_slice import Slice, SliceName
from .Edge import Edge
from .Face import Face
from .Part import Part
from .PartEdge import PartEdge

if TYPE_CHECKING:
    from .Cube3x3Colors import Cube3x3Colors
    from .CubeListener import CubeListener
    from .CubeQueries2 import CubeQueries2


class CubeSupplier(Protocol):

    @property
    def cube(self) -> "Cube":
        raise NotImplementedError()


class Cube(CubeSupplier):
    """
    Virtual Rubik's Cube supporting NxN sizes (3x3, 4x4, 5x5, etc.).

    The Cube is the root object containing all faces, parts (edges, corners, centers),
    and slices. It maintains the complete state of the puzzle and provides operations
    for rotations and queries.

    Cube Structure
    --------------
    ::

                        ┌───────────┐
                        │           │
                        │  YELLOW   │  U (Up)
                        │           │
            ┌───────────┼───────────┼───────────┬───────────┐
            │           │           │           │           │
            │  ORANGE   │   BLUE    │    RED    │   GREEN   │
            │           │           │           │           │
            │  L (Left) │  F (Front)│  R (Right)│  B (Back) │
            └───────────┼───────────┼───────────┴───────────┘
                        │           │
                        │   WHITE   │  D (Down)
                        │           │
                        └───────────┘

    Face Names and Colors (BOY Scheme):
    - F (Front)  = Blue
    - R (Right)  = Red
    - U (Up)     = Yellow
    - L (Left)   = Orange
    - D (Down)   = White
    - B (Back)   = Green

    Parameters
    ----------
    size : int
        The cube size (3 for 3x3, 4 for 4x4, etc.). Must be >= 2.

    Attributes
    ----------
    front, back, left, right, up, down : Face
        The six faces of the cube. These are the primary interface for rotations.
    size : int
        The cube dimension (N for NxN cube).
    n_slices : int
        Number of middle slices: size - 2. For 3x3: 1, for 4x4: 2, etc.
    solved : bool
        True if the cube is in solved state (all faces show single colors).
    cqr : CubeQueries2
        Query interface for finding parts and checking state.

    Examples
    --------
    Create and manipulate a 3x3 cube:

    >>> cube = Cube(size=3)
    >>> cube.solved
    True

    >>> # Perform moves
    >>> cube.front.rotate(1)   # F: 90° clockwise
    >>> cube.right.rotate(-1)  # R': counter-clockwise
    >>> cube.up.rotate(2)      # U2: 180°

    >>> cube.solved
    False

    Access cube parts:

    >>> # Get the front-up edge (shared between two faces)
    >>> fu_edge = cube.front.edge_top
    >>> assert fu_edge is cube.up.edge_bottom  # Same object!

    >>> # Get corner at intersection of front, right, up
    >>> fru_corner = cube.fru
    >>> # Or: cube.front.corner_top_right
    >>> # Or: cube.right.corner_top_left  (all same object)

    Find pieces by color:

    >>> from cube.domain.model.cube_boy import Color
    >>> # Find the white-red edge piece
    >>> white_red = frozenset([Color.WHITE, Color.RED])
    >>> edge = cube.find_edge_by_color(white_red)
    >>> edge.in_position  # Is it in the correct slot?
    >>> edge.match_faces  # Is it correctly oriented?

    Working with NxN cubes:

    >>> cube = Cube(size=5)
    >>> cube.n_slices  # Middle slices: 5-2 = 3
    3

    >>> # Each edge has 3 slices (outer-middle-outer)
    >>> edge = cube.front.edge_top
    >>> len(edge._slices)
    3

    >>> # Centers are 3x3 grids
    >>> center = cube.front.center
    >>> center_piece = center.get_slice((1, 1))  # Middle center

    Reset to solved state:

    >>> cube.reset()
    >>> cube.solved
    True

    >>> # Reset with different size
    >>> cube.reset(cube_size=4)
    >>> cube.size
    4

    Notes
    -----
    **Fixed Parts, Rotating Colors:**
    Unlike physical cubes, parts never move in 3D space. Only their colors change
    during rotations. This makes the model simpler and more efficient for algorithms.

    **Part Sharing:**
    Edge objects are shared between 2 faces, corners between 3 faces. When you rotate
    a face, the colors change on the shared parts, automatically updating all adjacent
    faces. No manual synchronization needed!

    **Performance:**
    - Cube creation: O(N²) where N is size
    - Face rotation: O(N) for edges, O(N²) for centers
    - Queries: O(1) with caching
    - Sanity check: O(N²) - can be disabled for production

    See Also
    --------
    Face : Individual face with rotation methods
    Part : Base class for pieces (Edge, Corner, Center)
    CubeQueries2 : Advanced query operations
    ARCHITECTURE.md : Detailed architecture documentation

    References
    ----------
    .. [1] Rubik's Cube Notation: https://ruwix.com/the-rubiks-cube/notation/
    .. [2] Cube Algorithms: https://alg.cubing.net/
    """
    __slots__ = [
        "_size",  # 3x3, 4x4
        "_front", "_left", "_up", "_right", "_down", "_back",
        "_faces",
        "_color_2_face",
        "_edges", "_corners", "_centers",
        "_slice_m", "_slice_e", "_slice_s",
        "_slices",
        "_modify_counter",
        "_last_sanity_counter",
        "_original_layout",
        "_cqr",
        "_sp",
        "_layout",
    ]

    _front: Face
    _left: Face
    _up: Face
    _right: Face
    _down: Face
    _back: Face
    _color_2_face: dict[Color, Face]
    _faces: dict[FaceName, Face]
    _slices: dict[SliceName, Slice]

    def __init__(self, size: int, sp: IServiceProvider) -> None:
        super().__init__()
        self._size = size
        self._sp = sp
        self._modify_counter = 0
        self._last_sanity_counter = 0
        self._original_layout: CubeLayout | None = None
        self._in_query_mode: bool = False  # Skip texture updates during query operations
        self._listeners: list["CubeListener"] = []
        self._is_even_cube_shadow: bool = False

        from .geometric import cube_boy

        self._layout: CubeLayout = cube_boy.get_boy_layout(self._sp)
        self._reset()

        from cube.domain.model.CubeQueries2 import CubeQueries2

        self._cqr: CubeQueries2 = CubeQueries2(self)

    def _reset(self, cube_size=None) -> None:

        if cube_size:
            self._size = cube_size

        assert self._size >= 2
        self._original_layout = None

        self._modify_counter = 0
        self._last_sanity_counter = 0

        self._color_2_face = {}

        boy = self._layout

        f: Face = Face(self, FaceName.F, boy[FaceName.F])
        l: Face = Face(self, FaceName.L, boy[FaceName.L])  # noqa: E741 TODO: fix
        u: Face = Face(self, FaceName.U, boy[FaceName.U])
        r: Face = Face(self, FaceName.R, boy[FaceName.R])
        d: Face = Face(self, FaceName.D, boy[FaceName.D])
        b: Face = Face(self, FaceName.B, boy[FaceName.B])

        self._faces = {
            FaceName.F: f,
            FaceName.L: l,
            FaceName.U: u,
            FaceName.R: r,
            FaceName.D: d,
            FaceName.B: b
        }

        # Set opposite face relationships using layout.opposite()
        # Only set once per pair to avoid duplicate calls
        set_pairs: set[frozenset[FaceName]] = set()
        for fn, face in self._faces.items():
            opposite_fn = boy.opposite(fn)
            pair = frozenset([fn, opposite_fn])
            if pair not in set_pairs:
                face.set_opposite(self._faces[opposite_fn])
                set_pairs.add(pair)

        self._front = f
        self._left = l
        self._up = u
        self._right = r
        self._down = d
        self._back = b

        edges: list[Edge] = []

        # see document right-top-left-coordinates.jpg
        # 12 edges
        f._edge_top = u._edge_bottom = _create_edge(edges, f, u, True)
        f._edge_left = l._edge_right = _create_edge(edges, f, l, True)
        f._edge_right = r._edge_left = _create_edge(edges, f, r, True)
        f._edge_bottom = d._edge_top = _create_edge(edges, f, d, True)

        # Note: u must be f1 for consistency with u._edge_top (U-B edge) - see Issue #53
        l._edge_top = u._edge_left = _create_edge(edges, u, l, False)
        l._edge_bottom = d._edge_left = _create_edge(edges, l, d, True)

        d._edge_right = r._edge_bottom = _create_edge(edges, d, r, False)
        d._edge_bottom = b._edge_bottom = _create_edge(edges, d, b, False)

        r._edge_right = b._edge_left = _create_edge(edges, r, b, True)

        l._edge_left = b._edge_right = _create_edge(edges, l, b, True)

        u._edge_top = b._edge_top = _create_edge(edges, u, b, False)
        u._edge_right = r._edge_top = _create_edge(edges, u, r, True)

        self._edges = edges

        corners: list[Corner] = []

        f._corner_top_left = l._corner_top_right = u._corner_bottom_left = _create_corner(corners, f, l, u)
        f._corner_top_right = r._corner_top_left = u._corner_bottom_right = _create_corner(corners, f, r, u)
        f._corner_bottom_left = l._corner_bottom_right = d._corner_top_left = _create_corner(corners, f, l, d)
        f._corner_bottom_right = r._corner_bottom_left = d._corner_top_right = _create_corner(corners, f, r, d)

        b._corner_top_left = r._corner_top_right = u._corner_top_right = _create_corner(corners, b, r, u)
        b._corner_top_right = l._corner_top_left = u._corner_top_left = _create_corner(corners, b, l, u)
        b._corner_bottom_left = r._corner_bottom_right = d._corner_bottom_right = _create_corner(corners, b, r, d)
        b._corner_bottom_right = l._corner_bottom_left = d._corner_bottom_left = _create_corner(corners, b, l, d)

        self._corners = corners

        for _f in self._faces.values():
            _f.finish_init()

        self._centers = [_f.center for _f in self._faces.values()]

        slice_s: Slice = Slice(self, SliceName.S,  # Middle over F
                               l.edge_top, u.center, r.edge_top,
                               r.center,
                               r.edge_bottom, d.center, l.edge_bottom,
                               l.center
                               )

        slice_m: Slice = Slice(self, SliceName.M,  # Middle over L
                               f.edge_top, u.center, b.edge_top,
                               b.center,
                               b.edge_bottom, d.center, f.edge_bottom,
                               f.center
                               )

        slice_e: Slice = Slice(self, SliceName.E,  # Middle over D
                               f.edge_left, f.center, f.edge_right,
                               r.center,
                               b.edge_left, b.center, b.edge_right,
                               l.center
                               )

        self._slices = {SliceName.S: slice_s, SliceName.M: slice_m, SliceName.E: slice_e}
        for s in self._slices.values():
            s.finish_init()

        # self.front.edge_top.annotate()

    @property
    def cube(self) -> "Cube":
        return self

    @property
    def layout(self) -> CubeLayout:
        return self._layout

    @property
    def sp(self) -> IServiceProvider:
        """Get the service provider."""
        return self._sp

    @property
    def config(self) -> ConfigProtocol:
        """Get the configuration (convenience property)."""
        assert self._sp is not None, "Cube requires a service provider (sp parameter)"
        return self._sp.config

    @property
    def cqr(self) -> "CubeQueries2":
        return self._cqr

    @property
    def is_even_cube_shadow(self) -> bool:
        """True if this is a shadow 3x3 of an even cube for parity handling."""
        return self._is_even_cube_shadow

    @is_even_cube_shadow.setter
    def is_even_cube_shadow(self, value: bool) -> None:
        self._is_even_cube_shadow = value

    def add_listener(self, listener: "CubeListener") -> None:
        """Register a listener to be notified of cube events.

        Args:
            listener: Object implementing CubeListener protocol
        """
        self._listeners.append(listener)

    def remove_listener(self, listener: "CubeListener") -> None:
        """Remove a previously registered listener.

        Args:
            listener: The listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    @property
    def size(self) -> int:
        return self._size

    @property
    def n_slices(self) -> int:
        """
        Number of middle slices per axis (between outer faces).

        For any NxN cube, the number of middle slices is N-2. These are the layers
        between the two outer faces on each axis (M slices between L/R, E slices
        between U/D, S slices between F/B).

        Returns
        -------
        int
            Number of middle slices: size - 2

        Examples
        --------
        >>> cube = Cube(size=3)
        >>> cube.n_slices
        1
        >>> # 3x3 has one M, one E, and one S slice

        >>> cube = Cube(size=4)
        >>> cube.n_slices
        2
        >>> # 4x4 has two M, two E, and two S slices

        >>> cube = Cube(size=5)
        >>> cube.n_slices
        3
        >>> # 5x5 has three of each slice type

        Notes
        -----
        **Slice Structure:**
        - 3x3: 1 middle slice per axis (total 3 slice types: M, E, S)
        - 4x4: 2 middle slices per axis (no center cubies)
        - 5x5: 3 middle slices per axis
        - NxN: (N-2) middle slices per axis

        **Minimum Size:**
        - 2x2 cubes have 0 middle slices (only faces, no M/E/S)
        - All cubes >= 3 have at least 1 middle slice per axis

        See Also
        --------
        rotate_slice : Rotate middle slices
        size : Cube dimension (N for NxN)
        """
        return self._size - 2

    def inv(self, i: int) -> int:
        return self.n_slices - 1 - i

    @property
    def front(self) -> Face:
        return self._front

    @property
    def left(self):
        return self._left

    @property
    def right(self) -> Face:
        return self._right

    @property
    def up(self):
        return self._up

    @property
    def back(self):
        return self._back

    @property
    def down(self):
        return self._down

    ###########################################################
    # Name order in edges nand corners
    #  First front/back, then right/left then up/down
    @property
    def fru(self) -> Corner:
        """

        :return:  Corner FRU
        """
        return self._front.corner_top_right

    @property
    def frd(self) -> Corner:
        """

        :return:  Corner FRD
        """
        return self._front.corner_bottom_right

    @property
    def flu(self) -> Corner:
        """

        :return:  Corner FLU
        """
        return self._front.corner_top_left

    @property
    def fld(self) -> Corner:
        """

        :return:  Corner FLD
        """
        return self._front.corner_bottom_left

    @property
    def bru(self) -> Corner:
        """

        :return:  Corner RUB
        """
        return self._right.corner_top_right

    @property
    def brd(self) -> Corner:
        """

        :return:  Corner BRD
        """
        return self._right.corner_bottom_right

    @property
    def blu(self) -> Corner:
        """

        :return:  Corner BLU
        """
        return self._left.corner_top_left

    @property
    def bld(self) -> Corner:
        """

        :return:  Corner BLD
        """
        return self._left.corner_bottom_left

    @property
    def fu(self) -> Edge:
        """

        :return:  Edge FU
        """
        return self._front.edge_top

    def fr(self) -> Edge:
        """

        :return:  Edge FR
        """
        return self._front.edge_right

    @property
    def fl(self) -> Edge:
        """

        :return:  Edge FL
        """
        return self._front.edge_left

    @property
    def bl(self) -> Edge:
        """

        :return:  Edge LB
        """
        return self.left.edge_left

    @property
    def br(self) -> Edge:
        """

        :return:  Edge RB
        """
        return self.right.edge_right

    @property
    def bu(self) -> Edge:
        """

        :return:  Edge UB
        """
        return self._up.edge_top

    @property
    def ru(self) -> Edge:
        """

        :return:  Edge RU
        """
        return self._right.edge_top

    @property
    def lu(self) -> Edge:
        """

        :return:  Edge LU
        """
        return self._left.edge_top

    @property
    def faces(self) -> Iterable[Face]:
        return self._faces.values()

    @property
    def edges(self) -> Iterable[Edge]:
        return self._edges

    @property
    def corners(self) -> Iterable[Corner]:
        return self._corners

    @property
    def centers(self) -> Iterable[Center]:
        return self._centers

    def face(self, name: FaceName) -> Face:
        return self._faces[name]

    def get_slice(self, name: SliceName) -> Slice:
        return self._slices[name]

    def reset_after_faces_changes(self):
        """
        Call after faces colors aare changes, M, S, E rotations
        :return:
        """
        self._color_2_face.clear()

        for f in self.faces:
            f.reset_after_faces_changes()

    def clear_c_attributes(self) -> None:
        """
        Clear all color-associated attributes (c_attributes) from all cube parts.

        c_attributes are markers/flags that move WITH the colors during rotations.
        Unlike structural attributes, c_attributes follow stickers as they move around
        the cube during face rotations.

        This method clears c_attributes on:
        - All Centers (via center slices)
        - All Edges (via edge slices/wings)
        - All Corners (via corner slices)

        Use Cases
        ---------
        - Clearing test markers between test iterations
        - Resetting debug annotations without full cube reset()
        - Removing tracking markers after algorithm analysis

        Example
        -------
        >>> cube = Cube(3)
        >>> # Add a marker to front center
        >>> cube.front.center.get_center_slice((1,1)).c_attributes["marker"] = "X"
        >>> # Do some operations...
        >>> cube.front.rotate(1)
        >>> # Clear all markers
        >>> cube.clear_c_attributes()
        >>> # All c_attributes are now empty

        Notes
        -----
        This does NOT affect:
        - Cube colors (use reset() for that)
        - Structural attributes (edge.attributes) which stay with positions
        - Cube state or solution status

        See Also
        --------
        reset : Full cube reset to solved state (also clears c_attributes via new objects)
        PartEdge : Has both attributes (positional) and c_attributes (color-following)
        """
        for edge in self.edges:
            edge.clear_c_attributes()
        for corner in self.corners:
            corner.clear_c_attributes()
        for center in self.centers:
            center.clear_c_attributes()

    def x_rotate(self, n):
        """
        Rotate entire cube around X-axis (same direction as R face).

        This performs a whole-cube rotation that reorients the cube in 3D space without
        changing the relative positions of pieces. It's equivalent to rotating the R face
        clockwise, the L face counter-clockwise, and all M slices in between.

        Parameters
        ----------
        n : int
            Number of quarter turns. Positive = rotate in R direction (clockwise when viewing from right),
            negative = rotate in L direction (counter-clockwise when viewing from right).

        Returns
        -------
        None

        Examples
        --------
        Single rotation:

        >>> cube = Cube(size=3)
        >>> cube.x_rotate(1)  # x: Rotate cube so Front becomes Up
        >>> # Front → Up → Back → Down → Front

        Multiple rotations:

        >>> cube.x_rotate(2)  # x2: Front becomes Back, Up becomes Down

        Counter-clockwise:

        >>> cube.x_rotate(-1)  # x': Front becomes Down

        Notes
        -----
        **Axis Direction:**
        - X-axis goes from Left face through center to Right face
        - Positive rotation follows Right face direction
        - Negative rotation follows Left face direction

        **Face Transformations (x rotation):**
        - Front → Up → Back → Down → Front (cycle)
        - Left and Right faces rotate in place

        **Use Cases:**
        - Reorienting the cube during solving
        - Standardizing cube position before applying algorithms
        - Viewing different faces without changing the state

        **Performance:**
        - O(N²) - must rotate all middle slices plus two outer faces

        See Also
        --------
        y_rotate : Rotate around Y-axis (U direction)
        z_rotate : Rotate around Z-axis (F direction)
        rotate_whole : Generic whole-cube rotation
        """
        for _ in range(0, n % 4):
            self.rotate_slice(SliceName.M, -1)  # L
            self.right.rotate(1)
            self.left.rotate(-1)

    def y_rotate(self, n=1):
        """
        Rotate entire cube around Y-axis (same direction as U face).

        This performs a whole-cube rotation that reorients the cube in 3D space without
        changing the relative positions of pieces. It's equivalent to rotating the U face
        clockwise, the D face counter-clockwise, and all E slices in between.

        Parameters
        ----------
        n : int, optional
            Number of quarter turns. Positive = rotate in U direction (clockwise when viewing from top),
            negative = rotate in D direction (counter-clockwise when viewing from top).
            Default is 1.

        Returns
        -------
        None

        Examples
        --------
        Single rotation:

        >>> cube = Cube(size=3)
        >>> cube.y_rotate(1)  # y: Rotate cube so Front becomes Left
        >>> # Front → Left → Back → Right → Front

        Multiple rotations:

        >>> cube.y_rotate(2)  # y2: Front becomes Back, Left becomes Right

        Counter-clockwise:

        >>> cube.y_rotate(-1)  # y': Front becomes Right

        Notes
        -----
        **Axis Direction:**
        - Y-axis goes from Down face through center to Up face
        - Positive rotation follows Up face direction
        - Negative rotation follows Down face direction

        **Face Transformations (y rotation):**
        - Front → Left → Back → Right → Front (cycle)
        - Up and Down faces rotate in place

        **Use Cases:**
        - Reorienting cube to view different sides
        - Algorithm setup (e.g., y U R U' R')
        - Standardizing F2L pair positions

        **Performance:**
        - O(N²) - must rotate all E slices plus two outer faces

        See Also
        --------
        x_rotate : Rotate around X-axis (R direction)
        z_rotate : Rotate around Z-axis (F direction)
        rotate_whole : Generic whole-cube rotation
        """
        for _ in range(0, n % 4):
            self.rotate_slice(SliceName.E, -1)
            self.up.rotate(1)
            self.down.rotate(-1)

    def z_rotate(self, n=1):
        """
        Rotate entire cube around Z-axis (same direction as F face).

        This performs a whole-cube rotation that reorients the cube in 3D space without
        changing the relative positions of pieces. It's equivalent to rotating the F face
        clockwise, the B face counter-clockwise, and all S slices in between.

        Parameters
        ----------
        n : int, optional
            Number of quarter turns. Positive = rotate in F direction (clockwise when viewing from front),
            negative = rotate in B direction (counter-clockwise when viewing from front).
            Default is 1.

        Returns
        -------
        None

        Examples
        --------
        Single rotation:

        >>> cube = Cube(size=3)
        >>> cube.z_rotate(1)  # z: Rotate cube so Up becomes Right
        >>> # Up → Right → Down → Left → Up

        Multiple rotations:

        >>> cube.z_rotate(2)  # z2: Up becomes Down, Right becomes Left

        Counter-clockwise:

        >>> cube.z_rotate(-1)  # z': Up becomes Left

        Notes
        -----
        **Axis Direction:**
        - Z-axis goes from Back face through center to Front face
        - Positive rotation follows Front face direction
        - Negative rotation follows Back face direction

        **Face Transformations (z rotation):**
        - Up → Right → Down → Left → Up (cycle)
        - Front and Back faces rotate in place

        **Use Cases:**
        - Adjusting grip or cube orientation
        - Algorithm variations (e.g., z R U R' U')
        - Ergonomic improvements during solving

        **Performance:**
        - O(N²) - must rotate all S slices plus two outer faces

        See Also
        --------
        x_rotate : Rotate around X-axis (R direction)
        y_rotate : Rotate around Y-axis (U direction)
        rotate_whole : Generic whole-cube rotation
        """
        for _ in range(0, n % 4):
            self.rotate_slice(SliceName.S, 1)
            self.front.rotate(1)
            self.back.rotate(-1)

    def rotate_whole(self, axis_name: AxisName, n=1):
        match axis_name:

            case AxisName.X:
                self.x_rotate(n)

            case AxisName.Y:
                self.y_rotate(n)

            case AxisName.Z:
                self.z_rotate(n)

            case _:
                raise RuntimeError(f"Unknown Axis {axis_name}")

    def rotate_slice(self, slice_name: SliceName, n: int, slices: Iterable[int] | None = None):
        """
        Rotate middle slices (M, E, S) without rotating any faces.

        This method performs slice moves that affect only the middle layers of the cube,
        not the outer faces. For 3x3 cubes, there's one middle slice per axis. For NxN cubes,
        there are N-2 middle slices per axis.

        Parameters
        ----------
        slice_name : SliceName
            Which slice axis to rotate: M (Middle/vertical), E (Equator/horizontal), or S (Standing/front-back).
            - M: Slice parallel to L and R faces (between left and right)
            - E: Slice parallel to U and D faces (between up and down)
            - S: Slice parallel to F and B faces (between front and back)
        n : int
            Number of quarter turns. Positive/negative directions follow the slice conventions:
            - M follows L direction (positive = same as L)
            - E follows D direction (positive = same as D)
            - S follows F direction (positive = same as F)
        slices : Iterable[int] | None, optional
            Which slice indices to rotate. Range: [0, n_slices-1] where n_slices = size - 2.
            Default is None, which rotates all middle slices.
            For 3x3: only [0] exists (single middle slice).
            For 4x4: [0, 1] exist (two middle slices).

        Returns
        -------
        None

        Examples
        --------
        Standard M slice on 3x3:

        >>> cube = Cube(size=3)
        >>> cube.rotate_slice(SliceName.M, 1)  # M: middle slice parallel to L/R
        >>> # For 3x3, this rotates the single middle slice

        E slice (equator):

        >>> cube.rotate_slice(SliceName.E, 1)  # E: middle slice parallel to U/D

        S slice (standing):

        >>> cube.rotate_slice(SliceName.S, 1)  # S: middle slice parallel to F/B

        Multiple slices on 4x4:

        >>> cube = Cube(size=4)
        >>> cube.rotate_slice(SliceName.M, 1, [0])     # First middle slice only
        >>> cube.rotate_slice(SliceName.M, 1, [1])     # Second middle slice only
        >>> cube.rotate_slice(SliceName.M, 1, [0, 1])  # Both middle slices

        Rotate all middle slices at once (5x5 example):

        >>> cube = Cube(size=5)
        >>> cube.rotate_slice(SliceName.E, 1)  # Rotates all 3 middle slices

        Counter-clockwise:

        >>> cube.rotate_slice(SliceName.M, -1)  # M'

        Notes
        -----
        **Slice Naming Conventions:**
        - M (Middle): Between L and R faces, follows L direction
        - E (Equator): Between U and D faces, follows D direction
        - S (Standing): Between F and B faces, follows F direction

        **Slice Count:**
        - 3x3: 1 slice per axis (n_slices = 1)
        - 4x4: 2 slices per axis (n_slices = 2)
        - 5x5: 3 slices per axis (n_slices = 3)
        - NxN: size - 2 slices per axis

        **Slice Indexing:**
        - Index 0 = slice closest to one face (e.g., for M: closest to L)
        - Index n_slices-1 = slice closest to opposite face (e.g., for M: closest to R)

        **Affected Parts:**
        - Edges: 4 edge slices per slice layer
        - Centers: Center pieces in the slice grid

        **Performance:**
        - O(N) per slice for edges
        - O(N²) for centers

        See Also
        --------
        rotate_face_and_slice : Rotate face + adjacent slices (wide moves)
        x_rotate, y_rotate, z_rotate : Rotate entire cube
        """

        a_slice: Slice = self.get_slice(slice_name)

        a_slice.rotate(n, slices)

    def get_rotate_slice_involved_parts(self, slice_name: SliceName,
                                        slice_indexes: int | Iterable[int] | None = None) -> Collection[PartSlice]:

        """

        :param slice_indexes: [0..n-2-1] [0, n_slices-1], default is [0, n_slices-1]
        :param slice_name:
        :return:
        """

        a_slice: Slice = self.get_slice(slice_name)

        return a_slice.get_rotate_involved_parts(slice_indexes)

    def get_face_and_rotation_info(self, face_name: FaceName,
                                   _slices: Iterable[int] | None = None) -> Tuple[Iterable[int], bool, SliceName]:
        """

        :param face_name:
        :param _slices:
        :return: indexes (of face and slices), neg slices, slice name
        """

        if not _slices:
            _slices = [0]

        size = self.size

        for i in _slices:
            assert 0 <= i <= size - 2

        neg_slice_index: bool
        slice_name: SliceName

        match face_name:

            case FaceName.R:
                slice_name, neg_slice_index = (SliceName.M, True)
            case FaceName.L:
                slice_name, neg_slice_index = (SliceName.M, False)

            case FaceName.U:
                slice_name, neg_slice_index = (SliceName.E, True)
            case FaceName.D:
                slice_name, neg_slice_index = (SliceName.E, False)
            case FaceName.F:
                slice_name, neg_slice_index = (SliceName.S, False)
            case FaceName.B:
                slice_name, neg_slice_index = (SliceName.S, True)

            case _:
                raise InternalSWError(f"Unknown face {face_name}")

        return _slices, neg_slice_index, slice_name

    def rotate_face_and_slice(self, n: int, face_name: FaceName, _slices: Iterable[int] | None = None):
        """
        Perform wide move: rotate face and adjacent slices together.

        This method implements "wide moves" like Fw (front + first slice), Rw (right + first slice),
        etc. It rotates both the specified face AND one or more adjacent middle slices.

        Parameters
        ----------
        n : int
            Number of quarter turns. Positive = clockwise, negative = counter-clockwise.
            For example: 1 = 90°, 2 = 180°, -1 = 90° counter-clockwise.
        face_name : FaceName
            Which face to rotate (F, B, L, R, U, or D).
        _slices : Iterable[int] | None, optional
            Which layers to rotate, where 0 = the face itself, 1 = first adjacent slice,
            2 = second adjacent slice, etc. Range: [0, size-2].
            Default is [0], which rotates only the face (standard move like F, R, U).
            Pass [0, 1] for standard wide move (Fw, Rw, etc.).

        Returns
        -------
        None

        Examples
        --------
        Standard face rotation (F move):

        >>> cube = Cube(size=3)
        >>> cube.rotate_face_and_slice(1, FaceName.F)  # F: 90° clockwise
        >>> # Or more simply: cube.front.rotate(1)

        Wide rotation (Fw move on 3x3):

        >>> cube = Cube(size=3)
        >>> cube.rotate_face_and_slice(1, FaceName.F, [0, 1])  # Fw
        >>> # Rotates front face + first middle slice (S)

        Wide rotation on 4x4 (rotate face + 2 slices):

        >>> cube = Cube(size=4)
        >>> cube.rotate_face_and_slice(1, FaceName.R, [0, 1, 2])  # Rw on 4x4
        >>> # Rotates right face + first two slices

        Rotate only a middle slice (not the face):

        >>> cube = Cube(size=4)
        >>> cube.rotate_face_and_slice(1, FaceName.R, [1])
        >>> # Rotates only the first slice adjacent to R (not R face itself)

        Counter-clockwise wide move:

        >>> cube.rotate_face_and_slice(-1, FaceName.U, [0, 1])  # Uw'

        Notes
        -----
        **Slice Indexing:**
        - 0 = the face itself
        - 1 = first slice adjacent to the face
        - 2 = second slice adjacent to the face
        - Maximum index = size - 2

        **Relation to Standard Moves:**
        - F = rotate_face_and_slice(1, FaceName.F, [0])
        - Fw = rotate_face_and_slice(1, FaceName.F, [0, 1])
        - M = rotate_slice(SliceName.M, n)  # Use rotate_slice instead

        **Performance:**
        - O(N) for edges per slice
        - O(N²) for face if slice 0 is included

        See Also
        --------
        rotate_slice : Rotate middle slices (M, E, S) without faces
        Face.rotate : Rotate a single face only
        """

        actual_slices: Iterable[int]
        neg_slice_index: bool
        slice_name: SliceName

        actual_slices, neg_slice_index, slice_name = self.get_face_and_rotation_info(face_name, _slices)

        slice_rotate_n = n

        if neg_slice_index:
            slice_rotate_n = -slice_rotate_n

        for i in actual_slices:

            if i == 0:
                self.face(face_name).rotate(n)

            else:
                # it is inner slice index

                # slice index is cube index -1
                si = i - 1
                if neg_slice_index:
                    si = self.inv(si)
                # can be optimized, by passing sequence
                self.rotate_slice(slice_name, slice_rotate_n, [si])

    def get_rotate_face_and_slice_involved_parts(self, face_name: FaceName, slices: Iterable[int] | None = None) -> \
            Collection[PartSlice]:

        """

        :param face_name:
        :param slices: [0, n-2] not including last face
        :return:
        """

        actual_slices: Iterable[int]
        neg_slice_index: bool
        slice_name: SliceName

        actual_slices, neg_slice_index, slice_name = self.get_face_and_rotation_info(face_name, slices)

        parts: MutableSequence[PartSlice] = []

        for i in actual_slices:
            if i == 0:
                face = self.face(face_name)
                parts.extend(face.slices)

            else:

                # slice index is cube index -1
                a_slice: Slice = self.get_slice(slice_name)
                si = i - 1
                if neg_slice_index:
                    si = self.inv(si)

                _slice_parts = a_slice.get_rotate_involved_parts(si)
                parts.extend(_slice_parts)

        return parts

    def modified(self):
        self._modify_counter += 1

    def is_sanity(self, force_check=False) -> bool:
        # noinspection PyBroadException
        try:
            self.sanity(force_check)
            return True
        except Exception:
            return False

    def sanity(self, force_check=False):
        """
        Validate cube integrity and structure.

        Performs comprehensive checks to ensure the cube is in a valid state. This includes
        verifying part connections, color consistency, face relationships, and data structure
        integrity. Helpful for debugging and ensuring algorithms don't corrupt the cube.

        Parameters
        ----------
        force_check : bool, optional
            If True, always perform validation even if config.CHECK_CUBE_SANITY is False.
            Default is False (respect config setting).

        Returns
        -------
        None

        Raises
        ------
        Various exceptions
            Raises appropriate exceptions if any integrity violations are detected.
            The specific exception type depends on what validation failed.

        Examples
        --------
        Basic validation:

        >>> cube = Cube(size=3)
        >>> cube.front.rotate(1)
        >>> cube.sanity()  # Passes if cube structure is valid
        >>> # No return value means validation passed

        Force validation regardless of config:

        >>> cube.sanity(force_check=True)

        Check if cube is valid (without raising exception):

        >>> is_valid = cube.is_sanity()
        >>> if is_valid:
        ...     print("Cube structure is valid")

        Notes
        -----
        **What Gets Checked:**
        - Part sharing: Edges are shared by exactly 2 faces, corners by 3
        - Color count: Each color appears correct number of times
        - Face relationships: Opposite faces, edge connections
        - Part identity: fixed_id, colors_id, position_id consistency
        - Graph structure: All parts reachable, no orphaned pieces
        - Slice integrity: Middle slice connections valid

        **Performance:**
        - O(N²) where N is cube size
        - Only runs if cube has been modified since last check
        - Can be disabled via config.CHECK_CUBE_SANITY for production

        **Caching:**
        - Sanity checks are cached based on modification counter
        - If cube hasn't changed since last check, validation is skipped
        - Use force_check=True to bypass cache

        **When to Use:**
        - After implementing new rotation algorithms
        - When debugging solver issues
        - Before/after complex move sequences
        - In test suites to verify correctness

        **Production Use:**
        - Set config.CHECK_CUBE_SANITY = False to disable for performance
        - Sanity checks add ~10-20% overhead during rotations
        - Recommended for development, optional for production

        See Also
        --------
        is_sanity : Check validity without raising exceptions
        solved : Check if cube is in solved state
        CubeSanity.do_sanity : Actual validation implementation
        """

        if not force_check and self._modify_counter == self._last_sanity_counter:
            return

        # if True:
        #     return

        # noinspection PyUnreachableCode
        try:
            self._do_sanity(force_check)
            self._last_sanity_counter = self._modify_counter
        except:
            raise

    def _do_sanity(self, force_check=False):
        if not (force_check or self.config.check_cube_sanity):
            return

        from .CubeSanity import CubeSanity

        CubeSanity.do_sanity(self)

        return

    @property
    def solved(self):
        return (self._front.solved and
                self._left.solved and
                self._right.solved and
                self._up.solved and
                self._back.solved and
                self._down.solved)

    @property
    def is3x3(self):
        return all(f.is3x3 for f in self.faces) and self.is_boy

    def reset(self, cube_size=None):
        """
        Reset cube to solved state, optionally changing size.

        This reinitializes the cube to a pristine solved state with all faces showing solid colors.
        It can also change the cube size (e.g., from 3x3 to 4x4) while resetting.

        Parameters
        ----------
        cube_size : int | None, optional
            New cube size (e.g., 3 for 3x3, 4 for 4x4, 5 for 5x5).
            If None (default), keeps the current size and just resets to solved state.
            Must be >= 2 if provided.

        Returns
        -------
        None

        Examples
        --------
        Reset after scrambling (keep same size):

        >>> cube = Cube(size=3)
        >>> cube.front.rotate(1)
        >>> cube.right.rotate(1)
        >>> cube.solved
        False
        >>> cube.reset()
        >>> cube.solved
        True

        Change cube size during reset:

        >>> cube = Cube(size=3)
        >>> cube.size
        3
        >>> cube.reset(cube_size=4)
        >>> cube.size
        4
        >>> cube.solved
        True

        Reset 5x5 to 3x3:

        >>> cube = Cube(size=5)
        >>> cube.reset(cube_size=3)
        >>> cube.size
        3

        Notes
        -----
        **What Gets Reset:**
        - All faces return to solid colors (BOY color scheme by default)
        - All parts return to correct positions and orientations
        - Modification counters are reset
        - Cache is cleared
        - Original layout is preserved

        **Size Changes:**
        - Changing size creates an entirely new cube structure
        - All internal objects (faces, parts, slices) are recreated
        - Previous cube state is completely discarded

        **IMPORTANT - Stale References:**
        After reset(), ALL internal objects (Face, Edge, Part, Slice) are NEW instances.
        Any references held by client code become stale and point to orphaned objects.

        Example of the bug::

            # WRONG - holds stale references after reset:
            for source_face in cube.faces:  # Gets face references
                for dest_face in ...:
                    # ... do something ...
                    cube.reset()  # Creates NEW face objects!
                    # source_face and dest_face are now STALE - they point to old objects

            # CORRECT - refresh references after reset:
            for source_name in [f.name for f in cube.faces]:  # Store names, not objects
                source_face = cube.get_face(source_name)  # Get fresh reference
                for dest_face in ...:
                    # ... do something ...
                    cube.reset()
                    source_face = cube.get_face(source_name)  # Refresh after reset

        **BOY Color Scheme:**
        After reset, the default color scheme is:
        - Front = Blue
        - Right = Red
        - Up = Yellow
        - Left = Orange
        - Down = White
        - Back = Green

        **Performance:**
        - O(N²) where N is the cube size
        - Creates all new part objects and connections

        See Also
        --------
        __init__ : Initial cube creation
        solved : Check if cube is in solved state
        """
        self._reset(cube_size)
        # Notify listeners after reset (while cube is still in solved state)
        for listener in self._listeners:
            listener.on_reset()

    def color_2_face(self, c: Color) -> Face:
        if not self._color_2_face:
            self._color_2_face = {f.color: f for f in self._faces.values()}

        return self._color_2_face[c]

    def find_part_by_colors(self, part_colors_id: PartColorsID) -> Part:

        for f in self.faces:
            p = f.find_part_by_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain part {str(part_colors_id)}")

    def find_part_by_pos_colors(self, part_colors_id: PartColorsID) -> Part:

        """
        Given a color id, find where it should be located in cube
        :param part_colors_id:
        :return:
        """

        for f in self.faces:
            p = f.find_part_by_pos_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain part {str(part_colors_id)}")

    def find_edge_by_color(self, part_colors_id: PartColorsID) -> Edge:
        """
        Find edge piece by its current colors (not position).

        This searches the cube for an edge that currently displays the specified color combination,
        regardless of where that edge is located or whether it's correctly oriented.

        Parameters
        ----------
        part_colors_id : PartColorsID
            A frozenset containing exactly 2 colors that identify the edge.
            For example: frozenset([Color.WHITE, Color.RED])

        Returns
        -------
        Edge
            The edge piece that currently has these colors.

        Raises
        ------
        ValueError
            If no edge with these colors exists on the cube.

        Examples
        --------
        Find white-red edge:

        >>> from cube.domain.model.cube_boy import Color
        >>> cube = Cube(size=3)
        >>> white_red = frozenset([Color.WHITE, Color.RED])
        >>> edge = cube.find_edge_by_color(white_red)
        >>> edge.in_position  # Check if it's in the correct slot
        >>> edge.match_faces  # Check if it's correctly oriented

        After scrambling, find where the piece moved:

        >>> cube.front.rotate(1)
        >>> cube.up.rotate(1)
        >>> edge = cube.find_edge_by_color(white_red)
        >>> # Edge still has white-red colors, but may be in different position

        Find blue-orange edge:

        >>> blue_orange = frozenset([Color.BLUE, Color.ORANGE])
        >>> edge = cube.find_edge_by_color(blue_orange)

        Notes
        -----
        **Colors vs Position:**
        - This method finds pieces by their CURRENT colors
        - Use find_edge_by_pos_colors() to find pieces by their HOME position

        **Edge Identity:**
        - Each edge has two "stickers" (PartEdge objects)
        - The frozenset contains the colors currently visible on both stickers
        - Color order doesn't matter: {WHITE, RED} == {RED, WHITE}

        **Use Cases:**
        - Tracking specific pieces during solving
        - Implementing solver algorithms
        - Checking piece positions in tutorials

        **Performance:**
        - O(E) where E = number of edges (12 for standard cube)
        - Linear search through all edges

        See Also
        --------
        find_corner_by_colors : Find corner by current colors
        find_edge_by_pos_colors : Find edge by home position
        Edge.in_position : Check if edge is in correct slot
        Edge.match_faces : Check if edge is correctly oriented
        """

        for f in self.faces:
            p = f.find_edge_by_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain edge {str(part_colors_id)}")

    def find_corner_by_colors(self, part_colors_id: PartColorsID) -> Corner:
        """
        Find corner piece by its current colors (not position).

        This searches the cube for a corner that currently displays the specified color combination,
        regardless of where that corner is located or whether it's correctly oriented.

        Parameters
        ----------
        part_colors_id : PartColorsID
            A frozenset containing exactly 3 colors that identify the corner.
            For example: frozenset([Color.WHITE, Color.RED, Color.BLUE])

        Returns
        -------
        Corner
            The corner piece that currently has these colors.

        Raises
        ------
        ValueError
            If no corner with these colors exists on the cube.
        AssertionError
            If part_colors_id doesn't contain exactly 3 colors.

        Examples
        --------
        Find white-red-blue corner:

        >>> from cube.domain.model.cube_boy import Color
        >>> cube = Cube(size=3)
        >>> wrb = frozenset([Color.WHITE, Color.RED, Color.BLUE])
        >>> corner = cube.find_corner_by_colors(wrb)
        >>> corner.in_position  # Check if it's in the correct slot
        >>> corner.match_faces  # Check if it's correctly oriented

        After scrambling:

        >>> cube.front.rotate(1)
        >>> cube.right.rotate(1)
        >>> corner = cube.find_corner_by_colors(wrb)
        >>> # Corner still has white-red-blue colors, but in different position

        Find yellow-orange-green corner:

        >>> yog = frozenset([Color.YELLOW, Color.ORANGE, Color.GREEN])
        >>> corner = cube.find_corner_by_colors(yog)

        Notes
        -----
        **Colors vs Position:**
        - This method finds pieces by their CURRENT colors
        - Use find_corner_by_pos_colors() to find pieces by their HOME position

        **Corner Identity:**
        - Each corner has three "stickers" (PartEdge objects)
        - The frozenset contains the colors currently visible on all three stickers
        - Color order doesn't matter: {WHITE, RED, BLUE} == {BLUE, WHITE, RED}

        **Corner Orientation:**
        - A corner can be in correct position but wrong orientation
        - Use corner.match_faces to check if colors align with face centers
        - Corners can be oriented 3 different ways (0°, 120°, 240°)

        **Use Cases:**
        - Tracking specific pieces during solving
        - Implementing corner-first solving methods
        - OLL/PLL algorithm selection
        - Verifying corner positions in tutorials

        **Performance:**
        - O(C) where C = number of corners (8 for standard cube)
        - Linear search through all corners

        See Also
        --------
        find_edge_by_color : Find edge by current colors
        find_corner_by_pos_colors : Find corner by home position
        Corner.in_position : Check if corner is in correct slot
        Corner.match_faces : Check if corner is correctly oriented
        """

        assert len(part_colors_id) == 3  # it is a corner

        for f in self.faces:
            p = f.find_corner_by_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain corner {str(part_colors_id)}")

    def find_edge_by_pos_colors(self, part_colors_id: PartColorsID) -> Edge:
        """
        Find the edge that it's position matches color id
        :param part_colors_id:
        :return:
        """
        for f in self.faces:
            p = f.find_edge_by_pos_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain edge {str(part_colors_id)}")

    def find_corner_by_pos_colors(self, part_colors_id: PartColorsID) -> Corner:
        """
        Find the edge that it's position matches color id
        :param part_colors_id:
        :return:
        """
        for f in self.faces:
            p = f.find_corner_by_pos_colors(part_colors_id)
            if p:
                return p

        raise ValueError(f"Cube doesn't contain corner {str(part_colors_id)}")

    def find_center_by_pos_colors(self, part_colors_id: PartColorsID) -> Center:
        """
        Find the edge that it's position matches color id
        :param part_colors_id:
        :return:
        """
        for f in self.faces:
            center = f.center
            if center.position_id is part_colors_id:
                return center

        raise ValueError(f"Cube doesn't contain center {str(part_colors_id)}")

    def get_all_part_slices(self) -> Collection[PartSlice]:
        """
        Get all PartSlice objects in the cube (CenterSlice, EdgeWing, CornerSlice).

        Returns a set because faces share slices (e.g., an edge slice belongs to 2 faces).
        """
        slices: set[PartSlice] = set()

        for f in self.faces:
            slices.update(f.slices)

        return slices

    @property
    def original_layout(self) -> CubeLayout:
        """

        :return: BOY layout
        """

        if not self._original_layout:
            faces: dict[FaceName, Color] = {f.name: f.original_color for f in self._faces.values()}
            lo = create_layout(True, faces, self._sp)

            self._original_layout = lo

        return self._original_layout

    @property
    def current_layout(self) -> CubeLayout:
        """

        :return: current layout, valid only in case of 3x3, guess center color by taking middle slice
        """

        faces: dict[FaceName, Color] = {f.name: f.center.color for f in self._faces.values()}
        return create_layout(False, faces, self._sp)

    @property
    def is_boy(self) -> bool:
        """Check if cube is in standard BOY orientation.

        Compares current center colors against the global BOY definition.
        """
        return self.current_layout.is_boy()

    @property
    def is_even(self) -> bool:
        return self.size % 2 == 0

    def get_3x3_colors(self) -> "Cube3x3Colors":
        """Extract edge/corner/center colors as a 3x3 snapshot.

        For NxN cubes, uses the representative edge slices (middle slice for edges).
        Does NOT require cube to actually be 3x3 - works on any NxN cube.

        Returns:
            Cube3x3Colors containing the colors of all edges, corners, and centers.
            Each edge/corner has colors keyed by face name.
        """
        from ._part import (
            CornerName,
            EdgeName,
            _faces_2_corner_name,
            _faces_2_edge_name,
        )
        from .Cube3x3Colors import CornerColors, Cube3x3Colors, EdgeColors

        edges_dict: dict[EdgeName, EdgeColors] = {}
        for edge in self.edges:
            # e1 and e2 are PartEdges, each belongs to a face
            edge_colors: dict[FaceName, Color] = {
                edge.e1.face.name: edge.e1.color,
                edge.e2.face.name: edge.e2.color,
            }
            edge_name = _faces_2_edge_name(edge_colors.keys())
            edges_dict[edge_name] = EdgeColors(edge_colors)

        corners_dict: dict[CornerName, CornerColors] = {}
        for corner in self.corners:
            pe = corner.slice.edges
            corner_colors: dict[FaceName, Color] = {
                pe[0].face.name: pe[0].color,
                pe[1].face.name: pe[1].color,
                pe[2].face.name: pe[2].color,
            }
            corner_name = _faces_2_corner_name(corner_colors.keys())
            corners_dict[corner_name] = CornerColors(corner_colors)

        centers_dict: dict[FaceName, Color] = {}
        for face in self.faces:
            centers_dict[face.name] = face.center.get_slice((0, 0)).edges[0].color

        return Cube3x3Colors(edges=edges_dict, corners=corners_dict, centers=centers_dict)

    def set_3x3_colors(self, colors: "Cube3x3Colors") -> None:
        """Set edge/corner/center colors from a 3x3 snapshot.

        Applies colors to the cube's edges, corners, and centers. For NxN cubes,
        sets the representative slices (middle slice for edges).

        After applying, resets all color caches and runs sanity check.

        Args:
            colors: Cube3x3Colors with the colors to apply (face-keyed).

        Raises:
            AssertionError: If the resulting cube state is invalid.
        """
        from ._part import _faces_2_corner_name, _faces_2_edge_name

        # Set edge colors - match by edge name derived from faces
        for edge in self.edges:
            # Get the face names from this edge's PartEdges
            f1_name = edge.e1.face.name
            f2_name = edge.e2.face.name
            edge_name = _faces_2_edge_name([f1_name, f2_name])
            ec = colors.edges[edge_name]
            edge.e1._color = ec.colors[f1_name]
            edge.e2._color = ec.colors[f2_name]

        # Set corner colors - match by corner name derived from faces
        for corner in self.corners:
            pe = corner.slice.edges
            f_names = [pe[0].face.name, pe[1].face.name, pe[2].face.name]
            corner_name = _faces_2_corner_name(f_names)
            cc = colors.corners[corner_name]
            pe[0]._color = cc.colors[f_names[0]]
            pe[1]._color = cc.colors[f_names[1]]
            pe[2]._color = cc.colors[f_names[2]]

        # Set center colors
        for face_name, color in colors.centers.items():
            face = self.face(face_name)
            face.center.get_slice((0, 0)).edges[0]._color = color

        # Reset caches (required after direct color changes)
        self.reset_after_faces_changes()
        self.modified()  # Increment counter so sanity cache works correctly

        # Validate
        assert self.is_sanity(force_check=True), "Invalid cube state after set_3x3_colors"


def _create_edge(edges: list[Edge], f1: Face, f2: Face, right_top_left_same_direction: bool) -> Edge:
    """

    :param f1:
    :param f2:
    :param right_top_left_same_direction: tru if on both faces, the left to top/right is the same direction
    See right-top-left-coordinates.jpg
    :return:
    """

    n = f1.cube.n_slices

    def _create_slice(i) -> EdgeWing:
        p1: PartEdge = f1.create_part()
        p2: PartEdge = f2.create_part()

        return EdgeWing(i, p1, p2)

    e: Edge = Edge(f1, f2, right_top_left_same_direction, [_create_slice(i) for i in range(n)])

    edges.append(e)

    return e


def _create_corner(corners: list[Corner], f1: Face, f2: Face, f3: Face) -> Corner:
    p1: PartEdge = f1.create_part()
    p2: PartEdge = f2.create_part()
    p3: PartEdge = f3.create_part()

    _slice = CornerSlice(p1, p2, p3)

    c: Corner = Corner(_slice)

    corners.append(c)

    return c
