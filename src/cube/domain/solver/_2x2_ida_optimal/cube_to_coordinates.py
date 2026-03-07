"""Bridge between domain Cube and IDA* coordinate system.

Maps the 8 physical corners of a 2x2 cube to the Kociemba-style
corner numbering used by the IDA* solver, and extracts the twist
and permutation coordinates.

Corner numbering:
    URF=0  UFL=1  ULB=2  UBR=3  DFR=4  DLF=5  DRB=6  DBL=7

Orientation convention:
    0 = U/D-colored sticker is on the U or D face (oriented)
    1 = U/D-colored sticker is one position clockwise
    2 = U/D-colored sticker is one position counter-clockwise

The 8th corner (DBL, index 7) is always fixed in place by the solver
(we only use U, R, F moves). Its permutation index and orientation
are derived from the other corners.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver._2x2_ida_optimal.ida_star_tables import (
    perm_from_cp,
    twist_from_co,
)

if TYPE_CHECKING:
    from cube.domain.model.Corner import Corner
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


def cube_to_coords(cube: Cube) -> tuple[int, int]:
    """Extract (permutation, twist) coordinates from a 2x2 Cube.

    Returns:
        (perm, twist) where perm is in 0..5039 and twist is in 0..728.
    """
    # The 8 corner slots in Kociemba order.
    # Each entry is the Corner object currently at that slot.
    corners: list[Corner] = [
        cube.fru,   # URF = 0
        cube.flu,   # UFL = 1
        cube.blu,   # ULB = 2
        cube.bru,   # UBR = 3
        cube.frd,   # DFR = 4
        cube.fld,   # DLF = 5
        cube.brd,   # DRB = 6
        cube.bld,   # DBL = 7 (fixed)
    ]

    up: Face = cube.up
    down: Face = cube.down

    # Build a mapping: for each corner, determine which Kociemba index
    # it *belongs* to (its home slot) based on its colors.
    # We identify corners by the set of face colors their stickers show.

    # The 8 "home" color sets, in Kociemba index order.
    # For a solved cube, corner at slot i has these face colors.
    home_colors: list[frozenset[object]] = []
    for c in corners:
        # On a solved cube, each sticker color matches its face color.
        # So the "home" colors = the face colors of this slot.
        edges = c._slice.edges
        home_colors.append(frozenset(e.face.original_color for e in edges))

    # Now, for the actual (possibly scrambled) cube, determine where each
    # corner *belongs* — i.e., which home slot has matching colors.
    # Also determine orientation.

    # First pass: identify corners by their actual sticker colors
    # and find their home index.
    cp: list[int] = [0] * 8  # cp[slot] = home index of the piece at slot
    co: list[int] = [0] * 8  # co[slot] = orientation of the piece at slot

    for slot_idx, corner in enumerate(corners):
        # Actual sticker colors of this corner piece
        edges = corner._slice.edges
        piece_colors: frozenset[object] = frozenset(e.color for e in edges)

        # Find which home slot this piece belongs to
        home_idx: int = -1
        for hi, hc in enumerate(home_colors):
            if hc == piece_colors:
                home_idx = hi
                break
        assert home_idx >= 0, f"Corner at slot {slot_idx} has unknown colors {piece_colors}"
        cp[slot_idx] = home_idx

        # Determine orientation:
        # Find the U/D color on this piece and check which face it's on.
        up_color = up.original_color
        down_color = down.original_color

        # Which of the 3 stickers has the U or D color?
        ud_sticker_face: Face | None = None
        for e in edges:
            if e.color == up_color or e.color == down_color:
                ud_sticker_face = e.face
                break
        assert ud_sticker_face is not None, "Corner has no U/D color"

        if ud_sticker_face is up or ud_sticker_face is down:
            co[slot_idx] = 0  # oriented
        else:
            # Need to determine CW vs CCW twist.
            # Convention: looking at the corner from outside the cube,
            # the 3 stickers go in a specific order.
            # For U-layer corners (slots 0-3): reference face is U
            # For D-layer corners (slots 4-7): reference face is D
            #
            # Orientation 1 = U/D sticker moved one position CW
            # Orientation 2 = U/D sticker moved one position CCW
            #
            # The canonical sticker order for each slot:
            # URF(0): U, R, F  →  if U-color on R → twist=1, on F → twist=2
            # UFL(1): U, F, L  →  if U-color on F → twist=1, on L → twist=2
            # ULB(2): U, L, B  →  if U-color on L → twist=1, on B → twist=2
            # UBR(3): U, B, R  →  if U-color on B → twist=1, on R → twist=2
            # DFR(4): D, F, R  →  if D-color on F → twist=1, on R → twist=2
            # DLF(5): D, L, F  →  if D-color on L → twist=1, on F → twist=2
            # DRB(6): D, R, B  →  if D-color on R → twist=1, on B → twist=2
            # DBL(7): D, B, L  →  if D-color on B → twist=1, on L → twist=2
            _TWIST_FACES: list[tuple[Face, Face]] = [
                (cube.right, cube.front),   # URF: twist1=R, twist2=F
                (cube.front, cube.left),    # UFL: twist1=F, twist2=L
                (cube.left, cube.back),     # ULB: twist1=L, twist2=B
                (cube.back, cube.right),    # UBR: twist1=B, twist2=R
                (cube.front, cube.right),   # DFR: twist1=F, twist2=R
                (cube.left, cube.front),    # DLF: twist1=L, twist2=F
                (cube.right, cube.back),    # DRB: twist1=R, twist2=B
                (cube.back, cube.left),     # DBL: twist1=B, twist2=L
            ]
            twist1_face, twist2_face = _TWIST_FACES[slot_idx]
            if ud_sticker_face is twist1_face:
                co[slot_idx] = 1
            elif ud_sticker_face is twist2_face:
                co[slot_idx] = 2
            else:
                raise ValueError(
                    f"Corner at slot {slot_idx}: U/D sticker on unexpected face "
                    f"{ud_sticker_face}"
                )

    return perm_from_cp(cp), twist_from_co(co)
