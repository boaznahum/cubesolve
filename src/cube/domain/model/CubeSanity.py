"""Cube sanity validation - ensures cube state is physically valid.

This module provides validation that catches invalid cube states that would be
impossible on a real Rubik's cube. These checks are essential for detecting
bugs in rotation algorithms or color assignment.

HOW TO USE
==========

Force sanity check (ignoring config):
    cube.is_sanity(force_check=True)  # Returns bool, doesn't raise
    cube.sanity(force_check=True)     # Raises InternalSWError if invalid

Automatic validation:
    cube.set_3x3_colors(colors)  # Always runs is_sanity(force_check=True)

WHAT GETS VALIDATED
===================

1. CORNERS (all cube sizes):
   - All 8 corners must exist with valid color combinations
     (derived from layout: each corner is 3 mutually adjacent faces)
   - Raises if any corner has impossible colors (e.g., opposite colors on same corner)

2. CENTER DISTRIBUTION (NxN cubes):
   - Each color must have exactly n_slices² center pieces
   - Each "orbit" (set of 4 equivalent positions) must have exactly 4 pieces
   - Exception: odd cubes have 1 fixed center piece (not 4)

3. EDGE DISTRIBUTION (NxN cubes):
   - Each edge color-pair must have exactly n_slices pieces
   - Each "orbit" (set of 2 equivalent positions) must have exactly 2 pieces
   - Exception: odd cubes have 1 middle edge slice (not 2)

4. 3x3-SPECIFIC (only when cube.is3x3 is True):
   - All 6 centers exist with valid colors
   - All 12 edges exist with valid color combinations

WHY THIS MATTERS FOR EVEN CUBES
===============================

On even cubes (4x4, 6x6), there is no fixed center. The center "color" is
determined by the majority of center pieces on that face. If an algorithm
corrupts the color distribution (e.g., moves a red center to blue face
without corresponding swap), sanity check will catch it.

Example corruption: After a bug, blue face has 5 blue + 11 red centers.
- _check_nxn_centers will detect: blue has only 5 pieces (should be 16)
- Raises: "CENTER pieces: Invalid count for color BLUE. Expected 16, found 5. Distribution by orbit: {...}"
"""

import sys
from typing import Hashable, Mapping, Sequence

from cube.domain.exceptions import InternalSWError

from ._elements import CHelper, PartColorsID
from .Cube import Cube
from cube.domain.model.Color import Color
from ..geometric.cube_color_scheme import CubeColorScheme


class CubeSanity:
    """Validates cube state for physical correctness.

    All methods are static - this is a utility class with no state.

    See module docstring for detailed documentation of what gets checked.
    """

    @staticmethod
    def do_sanity(cube: Cube) -> None:
        """Validate cube state, raise InternalSWError if invalid.

        This is the main entry point. Called by Cube.sanity() when validation
        is enabled (either via config or force_check=True).

        Args:
            cube: The cube to validate.

        Raises:
            InternalSWError: If any validation fails. Message describes the issue.

        Note:
            For is_sanity() behavior (return bool instead of raise), use:
            cube.is_sanity(force_check=True)
        """
        # Step 1: Validate all 8 corners exist with valid color combinations
        # Derived from the cube's layout: each corner is 3 adjacent faces
        layout = cube.layout
        cs: CubeColorScheme = cube.layout.colors_schema()
        for _, (f1, f2, f3) in layout.corner_faces().items():
            corner = (cs[f1], cs[f2], cs[f3])
            cube.find_corner_by_colors(CHelper.colors_id(corner))

        # Step 2: Validate center piece distribution (expensive but catches corruption)
        CubeSanity._check_nxn_centers(cube)

        # Step 3: Validate edge piece distribution
        CubeSanity._check_nxn_edges(cube)

        # Step 4: For reduced 3x3 cubes, also validate centers and edges exist
        if not cube.is3x3:
            return

        # Validate all 6 center colors exist
        for c in cs.colors():
            cube.find_part_by_colors(frozenset([c]))

        # Validate all 12 edges exist with valid color pairs
        # Derived from layout: each edge is 2 adjacent faces
        for _, (f1, f2) in layout.edge_faces().items():
            cube.find_part_by_colors(frozenset([cs[f1], cs[f2]]))

    @staticmethod
    def _check_nxn_centers(cube: Cube) -> None:
        """Validate center piece distribution across all faces.

        For each color, checks:
        1. Total count = n_slices² (e.g., 4 for 4x4, 9 for 5x5)
        2. Each orbit has exactly 4 pieces (or 1 for odd cube fixed center)

        An "orbit" is a set of 4 equivalent center positions that map to each
        other under face rotation. On a valid cube, each orbit has exactly
        one piece of each of the 4 colors that appear on the 4 faces around it.

        Raises:
            InternalSWError: If distribution is invalid.
        """
        n_slices = cube.n_slices
        dist: Mapping[Color, Mapping[Hashable, Sequence[tuple[int, int]]]] = cube.cqr.get_centers_dist()
        for clr in cube.layout.colors():
            clr_dist = dist[clr]

            def _print_clr():
                for _k, _v in clr_dist.items():
                    if len(_v) != 4:
                        m = "!!!"
                    else:
                        m = "+++"
                    print(clr, _k, f"{m}{len(_v)}{m}", v, file=sys.stderr)

            clr_n = sum(len(s) for s in clr_dist.values())

            if clr_n != n_slices * n_slices:
                expected = n_slices * n_slices
                orbit_info = {f"positions {k}": f"{len(v)} pieces at {list(v)}"
                              for k, v in clr_dist.items()}
                s = (f"CENTER pieces: Invalid count for color {clr}. "
                     f"Expected {expected}, found {clr_n}. "
                     f"Distribution by orbit (position groups that rotate together): {orbit_info}")
                _print_clr()
                print(s, file=sys.stderr)
                raise InternalSWError(s)
            for k, v in clr_dist.items():
                if len(v) != 4:
                    if n_slices % 2 and k == frozenset(
                            [*cube.cqr.get_four_center_points(n_slices // 2, n_slices // 2)]):
                        if len(v) != 1:
                            s = (f"CENTER pieces: Wrong middle center orbit count for color {clr}. "
                                 f"Orbit at positions {k}: expected 1 (fixed center), found {len(v)} pieces at {list(v)}")
                            _print_clr()
                            print(s, file=sys.stderr)
                            raise InternalSWError(s)

                    else:
                        s = (f"CENTER pieces: Invalid orbit count for color {clr}. "
                             f"Orbit at positions {k}: expected 4 pieces (one per rotation), found {len(v)} pieces at {list(v)}")
                        _print_clr()
                        print(s, file=sys.stderr)
                        raise InternalSWError(s)

    @staticmethod
    def _check_nxn_edges(cube: Cube) -> None:
        """Validate edge piece distribution for all edge color-pairs.

        For each of the 12 edge color-pairs (e.g., White-Blue, Red-Green):
        1. Total count = n_slices pieces (e.g., 2 for 4x4, 3 for 5x5)
        2. Each orbit has exactly 2 pieces (or 1 for odd cube middle slice)

        An edge "orbit" is a set of 2 equivalent positions on an edge that
        map to each other under edge flip. On a valid cube, each orbit has
        exactly one piece from each of the 2 wings.

        Raises:
            InternalSWError: If distribution is invalid.
        """
        n_slices = cube.n_slices
        from .CubeQueries2 import CubeQueries2

        cqr: CubeQueries2 = cube.cqr

        dist: Mapping[frozenset[Color], Mapping[Hashable, Sequence[int]]] = cqr.get_edges_dist()
        clr: PartColorsID
        for clr in cube.original_scheme.edge_colors():
            clr_dist = dist[clr]

            def _print_clr():
                for _k, _v in clr_dist.items():
                    if len(_v) != 2:
                        m = "!!!"
                    else:
                        m = "+++"
                    print(clr, _k, f"{m}{len(_v)}{m}", v, file=sys.stderr)

            clr_n = sum(len(s) for s in clr_dist.values())

            if clr_n != n_slices:
                orbit_info = {f"slices {k}": f"{len(v)} pieces at slices {list(v)}"
                              for k, v in clr_dist.items()}
                s = (f"EDGE pieces: Invalid count for color-pair {clr}. "
                     f"Expected {n_slices}, found {clr_n}. "
                     f"Distribution by orbit (slice groups that flip together): {orbit_info}")
                _print_clr()
                print(s, file=sys.stderr)
                raise InternalSWError(s)
            for k, v in clr_dist.items():
                if len(v) != 2:
                    if n_slices % 2 and k == frozenset([*cqr.get_two_edge_slice_points(n_slices//2)]):
                        if len(v) != 1:
                            s = (f"EDGE pieces: Wrong middle edge orbit count for color-pair {clr}. "
                                 f"Orbit at slices {k}: expected 1 (fixed middle slice), found {len(v)} pieces at slices {list(v)}")
                            _print_clr()
                            print(s, file=sys.stderr)
                            raise InternalSWError(s)

                    else:
                        s = (f"EDGE pieces: Invalid orbit count for color-pair {clr}. "
                             f"Orbit at slices {k}: expected 2 pieces (one per flip), found {len(v)} pieces at slices {list(v)}")
                        _print_clr()
                        print(s, file=sys.stderr)
                        raise InternalSWError(s)
