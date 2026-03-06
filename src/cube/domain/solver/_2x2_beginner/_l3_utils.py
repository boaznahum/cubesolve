"""Shared utilities for 2x2 L3 solvers.

Provides face-color-independent helpers for finding yellow color
and positioning the cube with white on DOWN / yellow on UP.
"""

from __future__ import annotations



from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverHelper import SolverHelper


def find_yellow_color(cube: Cube, white_color: Color) -> Color:
    """Find the yellow color (opposite of white) without using face colors.

    Yellow is the only color that never shares a corner with white.
    On a standard cube there are 6 colors; 4 corners contain white,
    covering white + 4 side colors. The 6th color is yellow.


    """

    scheme = cube.original_scheme

    return scheme.opposite_color(white_color)

    # why so complicated ?!!!

    # colors_with_white: set[Color] = set()
    # all_colors: set[Color] = set()
    # for corner in cube.corners:
    #     cid = corner.colors_id
    #     all_colors |= cid
    #     if white_color in cid:
    #         colors_with_white |= cid
    #
    # yellow_candidates = all_colors - colors_with_white
    # assert len(yellow_candidates) == 1, (
    #     f"Expected 1 yellow candidate, got {yellow_candidates}"
    # )
    # return next(iter(yellow_candidates))


def find_white_face(cube: Cube, white_color: Color) -> Face | None:
    """Find which face has all 4 corners with white facing it (L1 solved face)."""
    for face in cube.faces:
        if all(c.face_color(face) == white_color for c in face.corners):
            return face
    return None


def bring_white_to_down(slv: SolverHelper, white_color: Color) -> None:
    """Bring the solved L1 face (white) to DOWN position.

    Steps:
    1. Find which face has all white corners facing it
    2. Bring that face to UP
    3. Flip to DOWN (so yellow is now UP)
    """
    cube = slv.cube

    white_face: Face | None = find_white_face(cube, white_color)
    if white_face is None:
        raise InternalSWError("L1 not solved — no face has all white corners")

    # Bring white to UP first, then to DOWN
    slv.cmn.bring_face_up(white_face)
    slv.cmn.bring_face_down(cube.up)
