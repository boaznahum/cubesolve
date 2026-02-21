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
     connects to which other face's edge_top/right/bottom/left.
     (Duplicated from Cube._reset, see comment there.)
"""

from __future__ import annotations

from itertools import permutations

from cube.domain.model.FaceName import FaceName
from cube.domain.model._elements import EdgePosition
from cube.domain.model._part import CornerName, EdgeName

F, L, U, R, D, B = FaceName.F, FaceName.L, FaceName.U, FaceName.R, FaceName.D, FaceName.B
TOP, RIGHT, BOTTOM, LEFT = EdgePosition.TOP, EdgePosition.RIGHT, EdgePosition.BOTTOM, EdgePosition.LEFT

# ============================================================================
# Fundamental facts — only these, everything else is derived
# ============================================================================

# Opposite face pairs
_OPPOSITE: dict[FaceName, FaceName] = {F: B, U: D, L: R}

# The 12 edge wiring assignments from Cube._reset.
# Each entry: (face_a, position_on_a, face_b, position_on_b)
# Meaning: face_a's edge at position_on_a is shared with face_b's edge at position_on_b.
#
# DUPLICATION NOTE: This is the same truth expressed in Cube._reset as:
#   f._edge_top = u._edge_bottom = _create_edge(...)
# See Cube._reset for the authoritative source.
_EDGE_WIRING: list[tuple[FaceName, EdgePosition, FaceName, EdgePosition]] = [
    (F, TOP, U, BOTTOM),
    (F, LEFT, L, RIGHT),
    (F, RIGHT, R, LEFT),
    (F, BOTTOM, D, TOP),
    (L, TOP, U, LEFT),
    (L, BOTTOM, D, LEFT),
    (D, RIGHT, R, BOTTOM),
    (D, BOTTOM, B, BOTTOM),
    (R, RIGHT, B, LEFT),
    (L, LEFT, B, RIGHT),
    (U, TOP, B, TOP),
    (U, RIGHT, R, TOP),
]

# ============================================================================
# Derived facts
# ============================================================================

_REV_OPPOSITE: dict[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}
_ALL_OPPOSITE: dict[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}


def _derive_face_neighbors_cw() -> dict[FaceName, list[FaceName]]:
    """Derive CW neighbors for all faces from the edge wiring.

    Each wiring entry tells us: face_a's <position> neighbor is face_b.
    We collect [top, right, bottom, left] for each face, giving CW order.
    """
    # Build: face -> {position -> neighbor_face}
    pos_to_neighbor: dict[FaceName, dict[EdgePosition, FaceName]] = {
        fn: {} for fn in FaceName
    }
    for face_a, pos_a, face_b, _pos_b in _EDGE_WIRING:
        pos_to_neighbor[face_a][pos_a] = face_b
        pos_to_neighbor[face_b][_pos_b] = face_a

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


def _derive_edge_faces() -> dict[EdgeName, tuple[FaceName, FaceName]]:
    """Derive edge-to-faces mapping from CW neighbors.

    Each edge connects a face to one of its CW neighbors.
    """
    result: dict[EdgeName, tuple[FaceName, FaceName]] = {}
    for face, neighbors in _FACE_NEIGHBORS_CW.items():
        for neighbor in neighbors:
            for name_str in (face.value + neighbor.value, neighbor.value + face.value):
                try:
                    edge_name = EdgeName(name_str)
                    if edge_name not in result:
                        result[edge_name] = (FaceName(name_str[0]), FaceName(name_str[1]))
                    break
                except ValueError:
                    continue
    return result


def _derive_corner_faces() -> dict[CornerName, tuple[FaceName, FaceName, FaceName]]:
    """Derive corner-to-faces mapping from CW neighbors.

    Each corner is where three mutually adjacent faces meet — a face
    and two consecutive CW neighbors.
    """
    result: dict[CornerName, tuple[FaceName, FaceName, FaceName]] = {}
    for face, neighbors in _FACE_NEIGHBORS_CW.items():
        for i in range(4):
            triple = (face, neighbors[i], neighbors[(i + 1) % 4])
            for perm in permutations(triple):
                name_str = perm[0].value + perm[1].value + perm[2].value
                try:
                    corner_name = CornerName(name_str)
                    if corner_name not in result:
                        result[corner_name] = (
                            FaceName(name_str[0]),
                            FaceName(name_str[1]),
                            FaceName(name_str[2]),
                        )
                    break
                except ValueError:
                    continue
    return result


_EDGE_FACES: dict[EdgeName, tuple[FaceName, FaceName]] = _derive_edge_faces()
_CORNER_FACES: dict[CornerName, tuple[FaceName, FaceName, FaceName]] = _derive_corner_faces()

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

    def edge_faces(self) -> dict[EdgeName, tuple[FaceName, FaceName]]:
        """Get mapping from EdgeName to the two adjacent faces it connects."""
        return dict(_EDGE_FACES)

    def corner_faces(self) -> dict[CornerName, tuple[FaceName, FaceName, FaceName]]:
        """Get mapping from CornerName to the three faces it connects."""
        return dict(_CORNER_FACES)
