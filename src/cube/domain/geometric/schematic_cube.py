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
  2. The 8 corner wiring assignments — which face's corner_top_left/etc.
     connects to which other faces' corners.

Derived from the corners:
  3. The 12 edge wiring assignments — which face's edge_top/right/bottom/left
     connects to which other face's edge, plus the same_direction flag.
     (See _derive_edges_from_corners for the algorithm and diagrams.)
"""

from __future__ import annotations

from cube.domain.model.FaceName import FaceName
from cube.domain.model.part_names import (
    CornerName,
    CornerPosition,
    EdgeName,
    EdgePosition,
    faces_to_corner_name,
    faces_to_edge_name,
)

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


def _corner(fp1: tuple[FaceName, CornerPosition],
            fp2: tuple[FaceName, CornerPosition],
            fp3: tuple[FaceName, CornerPosition]) -> SchematicCorner:
    """Create a SchematicCorner, deriving the CornerName from the three faces."""
    name = faces_to_corner_name((fp1[0], fp2[0], fp3[0]))
    return SchematicCorner(name, {fp1[0]: fp1[1], fp2[0]: fp2[1], fp3[0]: fp3[1]})


# The 8 corner wiring assignments — the single source of truth.
# Face order matches the CornerName letter order (e.g., FLU → F first, L second, U third).
# The 12 edges are derived from these corners (see _derive_edges_from_corners below).
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


# ============================================================================
# Edge derivation from corners
# ============================================================================
#
# Each edge is shared by two faces. Each face traverses the edge in its own
# LTR direction. If both faces start from the same physical corner, the
# slice indices align (same_direction = True). If they start from different
# corners, one face's index 0 maps to the other's index N-1 (opposite
# direction). The code doesn't need to pick which face is "reversed" —
# it always converts between face-LTR and edge-index via the same_direction
# flag. See sections [A]–[E] below for the full derivation.

# [A] THE LTR COORDINATE SYSTEM
#
#   Every face has the same layout (looking from outside the cube):
#
#                ← X-axis (left to right) →
#
#           edge_top                            ↑
#       TL ─────────── TR                       │
#        │              │                    Y-axis
#    edge_left      edge_right            (bottom to top)
#        │              │                       │
#       BL ─────────── BR                       │
#          edge_bottom
#
#   This is identical on ALL 6 faces — it IS the LTR system.
#   The corner names (TL, TR, BL, BR) encode the LTR direction:
#
#     Horizontal edges: TL→TR (top), BL→BR (bottom)    [left to right]
#     Vertical edges:   BL→TL (left), BR→TR (right)    [bottom to top]
#
#
# [B] CORNER TABLE LOOKUP
#
#   The corner table maps each physical corner to its position on each face.
#   For example, corner FLU:
#
#       _corner((F, TL), (L, TR), (U, BL))
#
#   tells us: the FLU corner sits at F's TL, L's TR, and U's BL.
#   So when we write "U.BL = FLU", that's a direct table lookup.
#
#
# [C] DEDUCTION 1 — EDGE POSITION
#
#   Two adjacent faces share exactly 2 corners. The positions of those
#   corners on a face tell us which edge they border.
#
#   Example — F and U share corners FLU and FRU:
#     On Face F: FLU is at TL, FRU is at TR → {TL, TR} → TOP edge
#     On Face U: FLU is at BL, FRU is at BR → {BL, BR} → BOTTOM edge
#     Therefore: F.TOP connects to U.BOTTOM
#
#   The lookup: {TL,TR}→TOP, {BL,BR}→BOTTOM, {BL,TL}→LEFT, {BR,TR}→RIGHT
#   (This is _CORNER_PAIR_TO_EDGE_POS in the code.)
#
#
# [D] DEDUCTION 2 — same_direction
#
#   Each face sees the shared edge as a sequence of slices in its own
#   LTR direction (see [A]). The "start" corner is the first in LTR
#   order (see _EDGE_NATURAL_ORDER). If both faces start at the SAME
#   physical corner → same_direction = True.
#
#   Example — F.TOP / U.BOTTOM (same_direction = True):
#
#     From [A]:  TOP starts at TL,  BOTTOM starts at BL
#     From [B]:  F.TL = FLU,        U.BL = FLU
#     Same physical corner (FLU) → True
#
#   Example — U.LEFT / L.TOP (same_direction = False):
#
#     From [A]:  LEFT starts at BL,  TOP starts at TL
#     From [B]:  U.BL = FLU,         L.TL = BLU
#     Different physical corners (FLU ≠ BLU) → False
#
#
# [E] f1/f2 ORDERING
#
#   Arbitrary — we pick FaceName enum order. Edge internally uses
#   face-to-LTR conversion methods that handle either orientation.

# LTR natural order per edge position — see [A] above.
_EDGE_NATURAL_ORDER: dict[EdgePosition, tuple[CornerPosition, CornerPosition]] = {
    TOP:    (TL, TR),
    BOTTOM: (BL, BR),
    LEFT:   (BL, TL),
    RIGHT:  (BR, TR),
}

# Reverse lookup: {corner_pair} → edge position — see [C] above.
_CORNER_PAIR_TO_EDGE_POS: dict[frozenset[CornerPosition], EdgePosition] = {
    frozenset(v): k for k, v in _EDGE_NATURAL_ORDER.items()
}


def _derive_edges_from_corners() -> dict[EdgeName, SchematicEdge]:
    """Derive the 12 edges from the 8 corners.

    See the docstring above for the full algorithm with diagrams [A]-[E].
    Code comments reference those sections.
    """
    from collections import defaultdict

    # Collect shared corners per face-pair.
    # Each corner has 3 faces → 3 face-pairs. Two adjacent faces share exactly 2 corners.
    pair_corners: dict[frozenset[FaceName], list[dict[FaceName, CornerPosition]]] = defaultdict(list)

    for sc in _SCHEMATIC_CORNERS.values():
        faces = list(sc.positions.keys())
        for i in range(3):
            for j in range(i + 1, 3):
                pair = frozenset([faces[i], faces[j]])
                pair_corners[pair].append(sc.positions)

    face_order = list(FaceName)
    edges: dict[EdgeName, SchematicEdge] = {}

    for pair, corners in pair_corners.items():
        # [E] Deterministic f1/f2 by enum order (arbitrary)
        fa, fb = sorted(pair, key=lambda fn: face_order.index(fn))

        # [C] Edge position: look up the two shared corners' positions on each face
        pos_on_fa: EdgePosition = _CORNER_PAIR_TO_EDGE_POS[frozenset([corners[0][fa], corners[1][fa]])]
        pos_on_fb: EdgePosition = _CORNER_PAIR_TO_EDGE_POS[frozenset([corners[0][fb], corners[1][fb]])]

        # [D] same_direction: find which physical corner is at fa's "start" position,
        #     then check if that same corner is also at fb's "start" position.
        start_on_fa: CornerPosition = _EDGE_NATURAL_ORDER[pos_on_fa][0]   # [A] LTR start
        start_on_fb: CornerPosition = _EDGE_NATURAL_ORDER[pos_on_fb][0]   # [A] LTR start
        # [B] Find which shared corner sits at fa's start — then check its position on fb
        start_corner_pos_on_fb: CornerPosition = corners[0][fb] if corners[0][fa] == start_on_fa else corners[1][fb]
        same_dir = (start_corner_pos_on_fb == start_on_fb)

        name = faces_to_edge_name([fa, fb])
        edges[name] = SchematicEdge(name, fa, pos_on_fa, fb, pos_on_fb, same_dir)

    return edges


# The 12 edges — derived from the 8 corners above.
_SCHEMATIC_EDGES: dict[EdgeName, SchematicEdge] = _derive_edges_from_corners()

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
