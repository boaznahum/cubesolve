"""Name and position enums for cube parts, and face→name lookups.

Pure value enums (no domain logic):
  - EdgeName: the 12 edges (FU, FL, FR, ...)
  - CornerName: the 8 corners (FLU, FRU, ...)
  - EdgePosition: edge slot on a face (TOP, RIGHT, BOTTOM, LEFT)
  - CornerPosition: corner slot on a face (TOP_LEFT, TOP_RIGHT, ...)

Lookup functions (derived from enum values, no hardcoded tables):
  - faces_to_edge_name: frozenset of 2 FaceNames → EdgeName
  - faces_to_corner_name: frozenset of 3 FaceNames → CornerName
"""

from collections.abc import Iterable
from enum import Enum, unique

from cube.domain.model.FaceName import FaceName


class EdgeName(Enum):
    FL = "FL"
    FU = "FU"
    FR = "FR"
    FD = "FD"
    BL = "BL"
    BU = "BU"
    BR = "BR"
    BD = "BD"
    UR = "UR"
    RD = "RD"
    DL = "DL"
    LU = "LU"

    def __str__(self) -> str:
        return str(self.value)


@unique
class CornerName(Enum):
    FLU = "FLU"
    FRU = "FRU"
    FRD = "FRD"
    FLD = "FLD"
    BLU = "BLU"
    BRU = "BRU"
    BRD = "BRD"
    BLD = "BLD"

    def __str__(self) -> str:
        return str(self.value)


@unique
class EdgePosition(Enum):
    """Position of an edge relative to a face (when viewing the face from outside the cube).

    Used to get the edge at a specific position on a face via Face.get_edge().
    """
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


@unique
class CornerPosition(Enum):
    """Position of a corner relative to a face (viewing from outside the cube)."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


# ============================================================================
# Face → Name lookups (lazy-init, derived from enum values)
# ============================================================================

_faces_to_edge: dict[frozenset[FaceName], EdgeName] = {}


def faces_to_edge_name(faces: Iterable[FaceName]) -> EdgeName:
    """Look up the EdgeName for a pair of adjacent faces.

    Builds the lookup dict lazily from EdgeName enum values (e.g. "FL" → {F, L}).
    """
    if not _faces_to_edge:
        _char_to_face: dict[str, FaceName] = {fn.value: fn for fn in FaceName}
        for en in EdgeName:
            face_set = frozenset(_char_to_face[c] for c in en.value)
            _faces_to_edge[face_set] = en
    return _faces_to_edge[frozenset(faces)]


_faces_to_corner: dict[frozenset[FaceName], CornerName] = {}


def faces_to_corner_name(faces: Iterable[FaceName]) -> CornerName:
    """Look up the CornerName for a trio of faces meeting at a corner.

    Builds the lookup dict lazily from CornerName enum values (e.g. "FLU" → {F, L, U}).
    """
    if not _faces_to_corner:
        _char_to_face: dict[str, FaceName] = {fn.value: fn for fn in FaceName}
        for cn in CornerName:
            face_set = frozenset(_char_to_face[c] for c in cn.value)
            _faces_to_corner[face_set] = cn
    return _faces_to_corner[frozenset(faces)]
