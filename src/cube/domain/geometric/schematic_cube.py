"""
The fixed geometric facts of a Rubik's cube, independent of color scheme.

A color scheme (like BOY — Blue-Orange-Yellow) assigns colors to faces
and can vary. But the underlying geometry cannot: Up is opposite Down,
Left is opposite Right, Front is opposite Back. A clockwise face rotation
always cycles top->right->bottom->left. These are physical facts about how
a human holds and views the cube.

This class works ONLY with FaceName — it must never accept or return
physical domain objects like Face or Edge. It is purely about the
abstract face topology.

Singleton — there is only one cube geometry, unlike CubeFaceColorSchema
which can vary.

Fundamental facts (everything else is derived):
  1. Three opposite pairs: F<->B, U<->D, L<->R
  2. The 12 edge wiring assignments — which face's edge_top/right/bottom/left
     connects to which other face's edge_top/right/bottom/left,
     plus f1/f2 ordering and right_top_left_same_direction flag.
  3. The 8 corner wiring assignments — which face's corner_top_left/etc.
     connects to which other faces' corners.
     (Duplicated from Cube._reset, see comment there.)
"""

from __future__ import annotations

from itertools import permutations

from cube.domain.model.FaceName import FaceName
from cube.domain.model.part_names import CornerName, CornerPosition, EdgeName, EdgePosition

F, L, U, R, D, B = FaceName.F, FaceName.L, FaceName.U, FaceName.R, FaceName.D, FaceName.B
TOP, RIGHT, BOTTOM, LEFT = EdgePosition.TOP, EdgePosition.RIGHT, EdgePosition.BOTTOM, EdgePosition.LEFT

TL = CornerPosition.TOP_LEFT
TR = CornerPosition.TOP_RIGHT
BR = CornerPosition.BOTTOM_RIGHT
BL = CornerPosition.BOTTOM_LEFT


# ============================================================================
# Schematic classes
# ============================================================================

class SchematicEdge:
    """A named edge with full wiring information from Cube._reset().

    Captures the two faces sharing this edge, their edge positions,
    and the right_top_left_same_direction coordinate flag.
    """
    name: EdgeName
    f1: FaceName
    f2: FaceName
    pos_on_f1: EdgePosition
    pos_on_f2: EdgePosition
    right_top_left_same_direction: bool
    __slots__ = ("name", "f1", "f2", "pos_on_f1", "pos_on_f2",
                 "right_top_left_same_direction")

    def __init__(self, name: EdgeName,
                 f1: FaceName, pos_on_f1: EdgePosition,
                 f2: FaceName, pos_on_f2: EdgePosition,
                 right_top_left_same_direction: bool) -> None:
        self.name = name
        self.f1 = f1
        self.f2 = f2
        self.pos_on_f1 = pos_on_f1
        self.pos_on_f2 = pos_on_f2
        self.right_top_left_same_direction = right_top_left_same_direction

    def __repr__(self) -> str:
        return (f"SchematicEdge({self.name}, "
                f"{self.f1}.{self.pos_on_f1}={self.f2}.{self.pos_on_f2}, "
                f"same_dir={self.right_top_left_same_direction})")


class SchematicCorner:
    """A named corner with face-position wiring from Cube._reset().

    Captures the 3 faces at this corner and which corner position
    (TOP_LEFT, etc.) on each face.
    """
    name: CornerName
    positions: dict[FaceName, CornerPosition]
    __slots__ = ("name", "positions")

    def __init__(self, name: CornerName,
                 positions: dict[FaceName, CornerPosition]) -> None:
        self.name = name
        self.positions = positions

    @property
    def face_names(self) -> tuple[FaceName, FaceName, FaceName]:
        """The 3 face names, in insertion order (matches CornerName string)."""
        f1, f2, f3 = self.positions
        return (f1, f2, f3)

    def __repr__(self) -> str:
        parts = ", ".join(f"{fn}.{cp}" for fn, cp in self.positions.items())
        return f"SchematicCorner({self.name}, {parts})"


class SchematicFace:
    """A named face in the schematic cube.

    Lightweight — just the face name. Edge/corner queries go through
    SchematicCube mappings.
    """
    name: FaceName
    __slots__ = ("name",)

    def __init__(self, name: FaceName) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"SchematicFace({self.name})"


# ============================================================================
# Fundamental facts — only these, everything else is derived
# ============================================================================

# Opposite face pairs
_OPPOSITE: dict[FaceName, FaceName] = {F: B, U: D, L: R}
_REV_OPPOSITE: dict[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}
_ALL_OPPOSITE: dict[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}


def _derive_edge_name(f1: FaceName, f2: FaceName) -> EdgeName:
    """Derive the EdgeName from two face names."""
    for name_str in (f1.value + f2.value, f2.value + f1.value):
        try:
            return EdgeName(name_str)
        except ValueError:
            continue
    raise ValueError(f"No EdgeName for faces {f1}, {f2}")


def _derive_corner_name(faces: tuple[FaceName, ...]) -> CornerName:
    """Derive the CornerName from three face names."""
    for perm in permutations(faces):
        name_str = "".join(fn.value for fn in perm)
        try:
            return CornerName(name_str)
        except ValueError:
            continue
    raise ValueError(f"No CornerName for faces {faces}")


def _edge(f1: FaceName, p1: EdgePosition,
          f2: FaceName, p2: EdgePosition,
          same_dir: bool) -> SchematicEdge:
    """Create a SchematicEdge, deriving the EdgeName from the two faces."""
    return SchematicEdge(_derive_edge_name(f1, f2), f1, p1, f2, p2, same_dir)


def _corner(fp1: tuple[FaceName, CornerPosition],
            fp2: tuple[FaceName, CornerPosition],
            fp3: tuple[FaceName, CornerPosition]) -> SchematicCorner:
    """Create a SchematicCorner, deriving the CornerName from the three faces."""
    name = _derive_corner_name((fp1[0], fp2[0], fp3[0]))
    return SchematicCorner(name, {fp1[0]: fp1[1], fp2[0]: fp2[1], fp3[0]: fp3[1]})


# The 12 edge wiring assignments from Cube._reset.
# f1 is the first face passed to _create_edge() in Cube._reset.
# The ordering and direction flag matter for slice index mapping.
#
# DUPLICATION NOTE: This is the same truth expressed in Cube._reset as:
#   f._edge_top = u._edge_bottom = _create_edge(edges, f, u, True)
# See Cube._reset for the authoritative source.
_SCHEMATIC_EDGES: dict[EdgeName, SchematicEdge] = {e.name: e for e in [
    _edge(F, TOP,    U, BOTTOM, True),   # front._edge_top = up._edge_bottom
    _edge(F, LEFT,   L, RIGHT,  True),   # front._edge_left = left._edge_right
    _edge(F, RIGHT,  R, LEFT,   True),   # front._edge_right = right._edge_left
    _edge(F, BOTTOM, D, TOP,    True),   # front._edge_bottom = down._edge_top
    _edge(U, LEFT,   L, TOP,    False),  # left._edge_top = up._edge_left (f1=up)
    _edge(L, BOTTOM, D, LEFT,   True),   # left._edge_bottom = down._edge_left
    _edge(D, RIGHT,  R, BOTTOM, False),  # down._edge_right = right._edge_bottom
    _edge(D, BOTTOM, B, BOTTOM, False),  # down._edge_bottom = back._edge_bottom
    _edge(R, RIGHT,  B, LEFT,   True),   # right._edge_right = back._edge_left
    _edge(L, LEFT,   B, RIGHT,  True),   # left._edge_left = back._edge_right
    _edge(U, TOP,    B, TOP,    False),  # up._edge_top = back._edge_top
    _edge(U, RIGHT,  R, TOP,    True),   # up._edge_right = right._edge_top
]}

# The 8 corner wiring assignments from Cube._reset.
# Face order matches the CornerName letter order (e.g., FLU → F first, L second, U third).
#
# DUPLICATION NOTE: This is the same truth expressed in Cube._reset as:
#   front._corner_top_left = left._corner_top_right = up._corner_bottom_left = _create_corner(...)
_SCHEMATIC_CORNERS: dict[CornerName, SchematicCorner] = {c.name: c for c in [
    _corner((F, TL), (L, TR), (U, BL)),   # FLU
    _corner((F, TR), (R, TL), (U, BR)),   # FRU
    _corner((F, BL), (L, BR), (D, TL)),   # FLD
    _corner((F, BR), (R, BL), (D, TR)),   # FRD
    _corner((B, TL), (R, TR), (U, TR)),   # BRU
    _corner((B, TR), (L, TL), (U, TL)),   # BLU
    _corner((B, BL), (R, BR), (D, BR)),   # BRD
    _corner((B, BR), (L, BL), (D, BL)),   # BLD
]}

_SCHEMATIC_FACES: dict[FaceName, SchematicFace] = {fn: SchematicFace(fn) for fn in FaceName}


# ============================================================================
# Derived facts
# ============================================================================

def _derive_face_neighbors_cw() -> dict[FaceName, list[FaceName]]:
    """Derive CW neighbors for all faces from the schematic edges.

    Each edge tells us: face_a's <position> neighbor is face_b.
    We collect [top, right, bottom, left] for each face, giving CW order.
    """
    # Build: face -> {position -> neighbor_face}
    pos_to_neighbor: dict[FaceName, dict[EdgePosition, FaceName]] = {
        fn: {} for fn in FaceName
    }
    for edge in _SCHEMATIC_EDGES.values():
        pos_to_neighbor[edge.f1][edge.pos_on_f1] = edge.f2
        pos_to_neighbor[edge.f2][edge.pos_on_f2] = edge.f1

    # CW order: [TOP, RIGHT, BOTTOM, LEFT]
    cw_order = [TOP, RIGHT, BOTTOM, LEFT]
    result: dict[FaceName, list[FaceName]] = {}
    for fn in FaceName:
        result[fn] = [pos_to_neighbor[fn][pos] for pos in cw_order]
    return result


_FACE_NEIGHBORS_CW: dict[FaceName, list[FaceName]] = _derive_face_neighbors_cw()

_ADJACENT: dict[FaceName, tuple[FaceName, ...]] = {
    face: tuple(fn for fn in FaceName if fn != face and fn != _ALL_OPPOSITE[face])
    for face in FaceName
}

# CW index: follows from the CW ordering convention (top=0, right=1, bottom=2, left=3)
_CW_INDEX: dict[EdgePosition, int] = {
    pos: i for i, pos in enumerate([TOP, RIGHT, BOTTOM, LEFT])
}


class SchematicCube:
    """Singleton holding the fixed face-topology facts of a Rubik's cube.

    Works ONLY with FaceName/EdgeName/CornerName — never accepts or returns
    physical parts like Face or Edge.
    """

    _instance: SchematicCube | None = None

    def __init__(self) -> None:
        if SchematicCube._instance is not None:
            raise RuntimeError(
                "SchematicCube is a singleton — use SchematicCube.inst()"
            )

    @staticmethod
    def inst() -> SchematicCube:
        inst = SchematicCube._instance
        if inst is None:
            inst = SchematicCube()
            SchematicCube._instance = inst
        return inst

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def opposite(self, fn: FaceName) -> FaceName:
        """Get the face opposite to the given face."""
        return _ALL_OPPOSITE[fn]

    def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool:
        """Check if two faces are adjacent (share an edge)."""
        return face2 in _ADJACENT[face1]

    def get_adjacent_faces(self, face: FaceName) -> tuple[FaceName, ...]:
        """Get all 4 faces adjacent to the given face."""
        return _ADJACENT[face]

    def get_face_neighbors_cw_names(self, face_name: FaceName) -> list[FaceName]:
        """Get the four neighboring face names in clockwise rotation order.

        Returns [top, right, bottom, left] neighbors when looking at
        the face from outside the cube.
        """
        return list(_FACE_NEIGHBORS_CW[face_name])

    def get_face_neighbor(self, face_name: FaceName, position: EdgePosition) -> FaceName:
        """Get the neighboring face at a specific edge position."""
        return _FACE_NEIGHBORS_CW[face_name][_CW_INDEX[position]]

    def edge_faces(self) -> dict[EdgeName, SchematicEdge]:
        """Get mapping from EdgeName to SchematicEdge with full wiring info."""
        return dict(_SCHEMATIC_EDGES)

    def corner_faces(self) -> dict[CornerName, SchematicCorner]:
        """Get mapping from CornerName to SchematicCorner with full wiring info."""
        return dict(_SCHEMATIC_CORNERS)

    def get_edge(self, name: EdgeName) -> SchematicEdge:
        """Get a SchematicEdge by name."""
        return _SCHEMATIC_EDGES[name]

    def get_corner(self, name: CornerName) -> SchematicCorner:
        """Get a SchematicCorner by name."""
        return _SCHEMATIC_CORNERS[name]

    def get_face(self, name: FaceName) -> SchematicFace:
        """Get a SchematicFace by name."""
        return _SCHEMATIC_FACES[name]
