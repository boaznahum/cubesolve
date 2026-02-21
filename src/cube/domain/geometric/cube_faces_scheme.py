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
"""

from __future__ import annotations

from cube.domain.model.FaceName import FaceName
from cube.domain.model._elements import EdgePosition
from cube.domain.model._part import CornerName, EdgeName

# ============================================================================
# Fundamental facts — cannot be derived, define the cube orientation
# ============================================================================

# Opposite face pairs (canonical direction)
_OPPOSITE: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.B,
    FaceName.U: FaceName.D,
    FaceName.L: FaceName.R,
}

# CW neighbor ordering: [top, right, bottom, left] when looking at face
# from outside the cube. This defines the orientation of each face.
_FACE_NEIGHBORS_CW: dict[FaceName, list[FaceName]] = {
    FaceName.F: [FaceName.U, FaceName.R, FaceName.D, FaceName.L],
    FaceName.B: [FaceName.U, FaceName.L, FaceName.D, FaceName.R],
    FaceName.U: [FaceName.B, FaceName.R, FaceName.F, FaceName.L],
    FaceName.D: [FaceName.F, FaceName.R, FaceName.B, FaceName.L],
    FaceName.L: [FaceName.U, FaceName.F, FaceName.D, FaceName.B],
    FaceName.R: [FaceName.U, FaceName.B, FaceName.D, FaceName.F],
}

# ============================================================================
# Derived facts — computed from the fundamentals above
# ============================================================================

_REV_OPPOSITE: dict[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}
_ALL_OPPOSITE: dict[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}

_ADJACENT: dict[FaceName, tuple[FaceName, ...]] = {
    face: tuple(f for f in FaceName if f != face and f != _ALL_OPPOSITE[face])
    for face in FaceName
}


def _derive_edge_faces() -> dict[EdgeName, tuple[FaceName, FaceName]]:
    """Derive edge-to-faces mapping from CW neighbors.

    Each edge connects a face to one of its CW neighbors.
    EdgeName encodes the two faces (e.g. FU = Front-Up).
    """
    result: dict[EdgeName, tuple[FaceName, FaceName]] = {}
    for face, neighbors in _FACE_NEIGHBORS_CW.items():
        for neighbor in neighbors:
            # EdgeName is named by the two face letters
            name_str = face.value + neighbor.value
            try:
                edge_name = EdgeName(name_str)
            except ValueError:
                # Try reversed order
                name_str = neighbor.value + face.value
                try:
                    edge_name = EdgeName(name_str)
                except ValueError:
                    continue
            if edge_name not in result:
                result[edge_name] = (FaceName(name_str[0]), FaceName(name_str[1]))
    return result


def _derive_corner_faces() -> dict[CornerName, tuple[FaceName, FaceName, FaceName]]:
    """Derive corner-to-faces mapping from CW neighbors.

    Each corner is where three mutually adjacent faces meet. A corner
    of face F is at the intersection of two consecutive CW neighbors.
    """
    from itertools import permutations

    result: dict[CornerName, tuple[FaceName, FaceName, FaceName]] = {}
    for face, neighbors in _FACE_NEIGHBORS_CW.items():
        for i in range(4):
            n1 = neighbors[i]
            n2 = neighbors[(i + 1) % 4]
            # CornerName is 3 face letters; try all permutations
            for perm in permutations((face, n1, n2)):
                name_str = perm[0].value + perm[1].value + perm[2].value
                try:
                    corner_name = CornerName(name_str)
                    if corner_name not in result:
                        result[corner_name] = (
                            FaceName(corner_name.value[0]),
                            FaceName(corner_name.value[1]),
                            FaceName(corner_name.value[2]),
                        )
                    break
                except ValueError:
                    continue
    return result


_EDGE_FACES: dict[EdgeName, tuple[FaceName, FaceName]] = _derive_edge_faces()
_CORNER_FACES: dict[CornerName, tuple[FaceName, FaceName, FaceName]] = _derive_corner_faces()

# EdgePosition → CW index: TOP=0, RIGHT=1, BOTTOM=2, LEFT=3
# This follows directly from _FACE_NEIGHBORS_CW definition order.
_CW_INDEX: dict[EdgePosition, int] = {
    pos: i for i, pos in enumerate([
        EdgePosition.TOP, EdgePosition.RIGHT, EdgePosition.BOTTOM, EdgePosition.LEFT
    ])
}


class CubeFacesScheme:
    """Singleton holding the fixed face-topology facts of a Rubik's cube.

    Works ONLY with FaceName/EdgeName/CornerName — never accepts or returns
    physical parts like Face or Edge.
    """

    _instance: CubeFacesScheme | None = None

    def __init__(self) -> None:
        if CubeFacesScheme._instance is not None:
            raise RuntimeError(
                "CubeFacesScheme is a singleton — use CubeFacesScheme.inst()"
            )

    @staticmethod
    def inst() -> CubeFacesScheme:
        inst = CubeFacesScheme._instance
        if inst is None:
            inst = CubeFacesScheme()
            CubeFacesScheme._instance = inst
        return inst

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def opposite(self, fn: FaceName) -> FaceName:
        """Get the face opposite to the given face.

        F<->B, U<->D, L<->R.
        """
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
