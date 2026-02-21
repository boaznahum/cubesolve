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
# Lookup Tables — the fixed geometric facts
# ============================================================================

# Opposite face pairs (canonical direction)
_OPPOSITE: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.B,
    FaceName.U: FaceName.D,
    FaceName.L: FaceName.R,
}

# Reverse mapping
_REV_OPPOSITE: dict[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}

# Bidirectional opposite mapping
_ALL_OPPOSITE: dict[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}

# Adjacent faces (all faces except self and opposite)
_ADJACENT: dict[FaceName, tuple[FaceName, ...]] = {
    face: tuple(f for f in FaceName if f != face and f != _ALL_OPPOSITE[face])
    for face in FaceName
}

# CW neighbor ordering: [top, right, bottom, left] when looking at face from outside.
# Derived from the edge assignments in Cube.__init__ — each face's
# edge_top/edge_right/edge_bottom/edge_left connects to a specific neighbor.
# Edge-to-faces mapping: which two faces each edge connects.
# Derived from the edge assignments in Cube.__init__.
_EDGE_FACES: dict[EdgeName, tuple[FaceName, FaceName]] = {
    EdgeName.FU: (FaceName.F, FaceName.U),
    EdgeName.FL: (FaceName.F, FaceName.L),
    EdgeName.FR: (FaceName.F, FaceName.R),
    EdgeName.FD: (FaceName.F, FaceName.D),
    EdgeName.BU: (FaceName.B, FaceName.U),
    EdgeName.BL: (FaceName.B, FaceName.L),
    EdgeName.BR: (FaceName.B, FaceName.R),
    EdgeName.BD: (FaceName.B, FaceName.D),
    EdgeName.UR: (FaceName.U, FaceName.R),
    EdgeName.RD: (FaceName.R, FaceName.D),
    EdgeName.DL: (FaceName.D, FaceName.L),
    EdgeName.LU: (FaceName.L, FaceName.U),
}

# Corner-to-faces mapping: which three faces each corner connects.
# Derived from the corner assignments in Cube.__init__.
_CORNER_FACES: dict[CornerName, tuple[FaceName, FaceName, FaceName]] = {
    CornerName.FLU: (FaceName.F, FaceName.L, FaceName.U),
    CornerName.FRU: (FaceName.F, FaceName.R, FaceName.U),
    CornerName.FRD: (FaceName.F, FaceName.R, FaceName.D),
    CornerName.FLD: (FaceName.F, FaceName.L, FaceName.D),
    CornerName.BLU: (FaceName.B, FaceName.L, FaceName.U),
    CornerName.BRU: (FaceName.B, FaceName.R, FaceName.U),
    CornerName.BRD: (FaceName.B, FaceName.R, FaceName.D),
    CornerName.BLD: (FaceName.B, FaceName.L, FaceName.D),
}

# CW neighbor ordering: [top, right, bottom, left] when looking at face from outside.
# Derived from the edge assignments in Cube.__init__ — each face's
# edge_top/edge_right/edge_bottom/edge_left connects to a specific neighbor.
_FACE_NEIGHBORS_CW: dict[FaceName, list[FaceName]] = {
    FaceName.F: [FaceName.U, FaceName.R, FaceName.D, FaceName.L],
    FaceName.B: [FaceName.U, FaceName.L, FaceName.D, FaceName.R],
    FaceName.U: [FaceName.B, FaceName.R, FaceName.F, FaceName.L],
    FaceName.D: [FaceName.F, FaceName.R, FaceName.B, FaceName.L],
    FaceName.L: [FaceName.U, FaceName.F, FaceName.D, FaceName.B],
    FaceName.R: [FaceName.U, FaceName.B, FaceName.D, FaceName.F],
}


# Map EdgePosition to CW neighbor index: [0]=TOP, [1]=RIGHT, [2]=BOTTOM, [3]=LEFT
_EDGE_POSITION_TO_CW_INDEX: dict[EdgePosition, int] = {
    EdgePosition.TOP: 0,
    EdgePosition.RIGHT: 1,
    EdgePosition.BOTTOM: 2,
    EdgePosition.LEFT: 3,
}


class CubeFacesScheme:
    """Singleton holding the fixed face-topology facts of a Rubik's cube.

    Works ONLY with FaceName — never accepts or returns physical parts
    like Face or Edge.
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
        """Get the neighboring face at a specific edge position.

        Args:
            face_name: The face to get the neighbor for.
            position: Which edge position (TOP, RIGHT, BOTTOM, LEFT).

        Returns:
            The FaceName of the neighboring face at that position.
        """
        idx = _EDGE_POSITION_TO_CW_INDEX[position]
        return _FACE_NEIGHBORS_CW[face_name][idx]

    def edge_faces(self) -> dict[EdgeName, tuple[FaceName, FaceName]]:
        """Get mapping from EdgeName to the two adjacent faces it connects.

        Example:
            scheme.edge_faces()[EdgeName.FU] == (FaceName.F, FaceName.U)
        """
        return dict(_EDGE_FACES)

    def corner_faces(self) -> dict[CornerName, tuple[FaceName, FaceName, FaceName]]:
        """Get mapping from CornerName to the three faces it connects.

        Example:
            scheme.corner_faces()[CornerName.FRU] == (FaceName.F, FaceName.R, FaceName.U)
        """
        return dict(_CORNER_FACES)
