from collections.abc import Iterable
from enum import Enum, unique
from typing import TYPE_CHECKING, TypeAlias

from cube.domain.model.cube_boy import FaceName

if TYPE_CHECKING:
    from .Cube import Cube
    from .Face import Face

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore


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


_faces_to_edges: dict[frozenset[FaceName], EdgeName] = {}


def _faces_2_edge_name(faces: Iterable[FaceName]) -> EdgeName:
    global _faces_to_corners

    if not _faces_to_edges:
        def _a(f1, f2, cn: EdgeName):
            _faces_to_edges[frozenset([f1, f2])] = cn

        _a(FaceName.F, FaceName.L, EdgeName.FL)
        _a(FaceName.F, FaceName.U, EdgeName.FU)
        _a(FaceName.F, FaceName.R, EdgeName.FR)
        _a(FaceName.F, FaceName.D, EdgeName.FD)
        _a(FaceName.B, FaceName.L, EdgeName.BL)
        _a(FaceName.B, FaceName.U, EdgeName.BU)
        _a(FaceName.B, FaceName.R, EdgeName.BR)
        _a(FaceName.B, FaceName.D, EdgeName.BD)

        _a(FaceName.U, FaceName.R, EdgeName.UR)
        _a(FaceName.R, FaceName.D, EdgeName.RD)
        _a(FaceName.D, FaceName.L, EdgeName.DL)
        _a(FaceName.L, FaceName.U, EdgeName.LU)

    return _faces_to_edges[frozenset(faces)]


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


_faces_to_corners: dict[frozenset[FaceName], CornerName] = {}


def _faces_2_corner_name(faces: Iterable[FaceName]):
    global _faces_to_corners

    if not _faces_to_corners:
        def _a(f1, f2, f3, cn: CornerName):
            _faces_to_corners[frozenset([f1, f2, f3])] = cn

        _a(FaceName.F, FaceName.L, FaceName.U, CornerName.FLU)
        _a(FaceName.F, FaceName.R, FaceName.U, CornerName.FRU)
        _a(FaceName.F, FaceName.R, FaceName.D, CornerName.FRD)
        _a(FaceName.F, FaceName.L, FaceName.D, CornerName.FLD)
        _a(FaceName.B, FaceName.L, FaceName.U, CornerName.BLU)
        _a(FaceName.B, FaceName.R, FaceName.U, CornerName.BRU)
        _a(FaceName.B, FaceName.R, FaceName.D, CornerName.BRD)
        _a(FaceName.B, FaceName.L, FaceName.D, CornerName.BLD)

    return _faces_to_corners[frozenset(faces)]
















