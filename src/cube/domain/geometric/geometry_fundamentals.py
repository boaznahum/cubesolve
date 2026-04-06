"""Geometry Fundamentals — axioms from which all geometry is derived.

Each constant here is a hand-defined convention that CANNOT be computed
from other facts. These are the foundational definitions of the cube's
geometric structure.

Derived facts belong in their respective modules (CubeLayout, SliceLayout,
etc.), not here.

See HARDCODED_ANALYSIS.md for the full classification of constants.
"""
from __future__ import annotations

from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from cube.domain.model._elements import AxisName

# ━━ Which face each slice rotates like (convention) ━━━━━━━━━━━━━━━━
#
#   M rotates like L  (middle layer between L and R)
#   E rotates like D  (middle layer between U and D)
#   S rotates like F  (middle layer between F and B)
#
SLICE_ROTATION_FACE: dict[SliceName, FaceName] = {
    SliceName.M: FaceName.L,
    SliceName.E: FaceName.D,
    SliceName.S: FaceName.F,
}

# ━━ Which face each whole-cube axis rotates like (convention) ━━━━━━
#
#   X rotates like R
#   Y rotates like U
#   Z rotates like F
#
AXIS_FACE: dict[AxisName, FaceName] = {
    AxisName.X: FaceName.R,
    AxisName.Y: FaceName.U,
    AxisName.Z: FaceName.F,
}

# ━━ Reverse lookups (derived from the above) ━━━━━━━━━━━━━━━━━━━━━━━
#
#   Given a face, find which slice or axis rotates like it.
#
FACE_TO_SLICE: dict[FaceName, SliceName] = {v: k for k, v in SLICE_ROTATION_FACE.items()}
FACE_TO_AXIS: dict[FaceName, AxisName] = {v: k for k, v in AXIS_FACE.items()}
