import sys
from typing import Mapping, Hashable, Sequence

from cube.application.exceptions.app_exceptions import InternalSWError
from .Cube import Cube
from .cube_boy import Color
from ._elements import CHelper, PartColorsID


class CubeSanity:

    @staticmethod
    def do_sanity(cube: Cube):

        # find all corners , NxN still have simple corners

        corners = [
            (Color.YELLOW, Color.ORANGE, Color.BLUE),
            (Color.YELLOW, Color.RED, Color.BLUE),
            (Color.YELLOW, Color.ORANGE, Color.GREEN),
            (Color.YELLOW, Color.RED, Color.GREEN),
            (Color.WHITE, Color.ORANGE, Color.BLUE),
            (Color.WHITE, Color.RED, Color.BLUE),
            (Color.WHITE, Color.ORANGE, Color.GREEN),
            (Color.WHITE, Color.RED, Color.GREEN),
        ]

        for corner in corners:
            cube.find_corner_by_colors(CHelper.colors_id(corner))

        # very expansive, but there is a corruption
        CubeSanity._check_nxn_centers(cube)
        CubeSanity._check_nxn_edges(cube)

        if not cube.is3x3:
            return

        for c in Color:
            cube.find_part_by_colors(frozenset([c]))

        for c1, c2 in [
            (Color.WHITE, Color.ORANGE),
            (Color.WHITE, Color.BLUE),
            (Color.WHITE, Color.GREEN),
            (Color.WHITE, Color.RED),
            (Color.YELLOW, Color.ORANGE),
            (Color.YELLOW, Color.BLUE),
            (Color.YELLOW, Color.GREEN),
            (Color.YELLOW, Color.RED),

            (Color.ORANGE, Color.BLUE),
            (Color.BLUE, Color.RED),
            (Color.RED, Color.GREEN),
            (Color.GREEN, Color.ORANGE),
        ]:
            cube.find_part_by_colors(frozenset([c1, c2]))

    @staticmethod
    def _check_nxn_centers(cube) -> None:
        n_slices = cube.n_slices
        dist: Mapping[Color, Mapping[Hashable, Sequence[tuple[int, int]]]] = cube.cqr.get_centers_dist()
        for clr in Color:
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
                s = f"Too few entries for color {clr}"
                _print_clr()
                print(s, file=sys.stderr)
                raise InternalSWError(s)
            for k, v in clr_dist.items():
                if len(v) != 4:
                    if n_slices % 2 and k == frozenset(
                            [*cube.cqr.get_four_center_points(n_slices // 2, n_slices // 2)]):
                        if len(v) != 1:
                            s = f"Wrong middle center {k} entries for color {clr}"
                            _print_clr()
                            print(s, file=sys.stderr)
                            raise InternalSWError(s)

                    else:
                        s = f"Too few point {k} entries for color {clr}"
                        _print_clr()
                        print(s, file=sys.stderr)
                        raise InternalSWError(s)

    @staticmethod
    def _check_nxn_edges(cube) -> None:
        n_slices = cube.n_slices
        from .CubeQueries2 import CubeQueries2

        cqr: CubeQueries2 = cube.cqr

        dist: Mapping[frozenset[Color], Mapping[Hashable, Sequence[int]]] = cqr.get_edges_dist()
        clr: PartColorsID
        for clr in cube.original_layout.edge_colors():
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
                s = f"Too few entries for color {clr}"
                _print_clr()
                print(s, file=sys.stderr)
                raise InternalSWError(s)
            for k, v in clr_dist.items():
                if len(v) != 2:
                    if n_slices % 2 and k == frozenset([*cqr.get_two_edge_slice_points(n_slices//2)]):
                        if len(v) != 1:
                            s = f"Wrong middle center {k} entries for color {clr}"
                            _print_clr()
                            print(s, file=sys.stderr)
                            raise InternalSWError(s)

                    else:
                        s = f"Too few point {k} entries for color {clr}"
                        _print_clr()
                        print(s, file=sys.stderr)
                        raise InternalSWError(s)
