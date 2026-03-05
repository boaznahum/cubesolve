"""Layer 1 solver for 2x2 beginner method.

Solves all 4 first-layer corners so that:
- Each corner is in its correct position
- Each corner is correctly oriented

Since a 2x2 cube has no centers, faces have no inherent color.
This solver:
1. Chooses a face to start with (_find_best_l1)
2. Assigns colors to all faces via a FacesColorsProvider
3. Delegates to the existing L1Corners solver from the 3x3 beginner package

The face_colors mapping is stored so L3 solvers can reuse it.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Mapping

from cube.domain.geometric.cube_face_colors import CubeFaceColors
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model.Face import Face
from cube.domain.model.FacesColorsProvider import FacesColorsProvider
from cube.domain.model.Part import Part
from cube.domain.solver._2x2_beginner._2x2L1Corners import _2x2L1Corners
from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class _SimpleFacesColorsProvider:
    """FacesColorsProvider backed by a static mapping."""

    __slots__ = ["_mapping"]

    def __init__(self, mapping: Mapping[FaceName, Color]) -> None:
        self._mapping = mapping

    def get_face_color(self, face_name: FaceName) -> Color:
        return self._mapping[face_name]


class L1(StepSolver):
    """First layer corner solver for 2x2.

    Stateless — ``find_best_l1()`` computes fresh each time.
    The parent solver calls it once per solve and shares the
    mapping with L3 solvers.
    """

    __slots__: list[str] = []

    _CACHE_KEY = "L1._find_best_l1"

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L1")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 first-layer corners are correctly placed and oriented."""
        _, face_colors = self.find_best_l1()
        with self.apply_provider(face_colors):
            wf: Face = self.white_face
            return Part.all_match_faces(wf.corners)

    def solve(self) -> None:
        """Solve the first layer (4 corners)."""
        if self.is_solved:
            return

        l1_face, face_colors = self.find_best_l1()

        # Bring L1 face to UP (L1Corners hardcodes self.cube.up as white face).
        #self.cmn.bring_face_up(l1_face)

        # After rotation, stickers moved but original_color is fixed.
        # Compute the rotated mapping so that start_color sits on UP.
        start_color: Color = self.cmn.white
        scheme = self.cube.original_scheme
        rotated: CubeFaceColors = scheme.bring_color_to_face(
            CubeFaceColors(face_colors), start_color, FaceName.U,
        )

        with self.apply_provider(rotated.mapping):
            l1_corners = _2x2L1Corners(self)
            l1_corners.solve() # claude fix this call solve !!!

    def find_best_l1(self) -> tuple[Face, Mapping[FaceName, Color]]:
        """Choose which face to solve as L1 and assign colors to all faces.

        Result is cached in ``cube.mutation_cache`` — automatically
        invalidated when the cube is modified (rotation, scramble, reset).

        This caching is important because ``is_solved`` and ``status``
        are called frequently without cube modifications in between
        (e.g., GUI status bar refreshes, animation frame updates).
        Without the cache, ``_compute_best_l1`` would run on every call.

        Simple implementation: use the cube's original color scheme.

        Returns:
            (l1_face, face_colors) — the face to start with and
            a mapping of all face names to their assigned colors.
        """
        cache = self.cube.mutation_cache.get(L1._CACHE_KEY, tuple)  # type: ignore[arg-type]
        return cache.compute(self._compute_best_l1)

    def _compute_best_l1(self) -> tuple[Face, dict[FaceName, Color]]:
        """Compute best L1 face and color mapping (uncached)."""
        cube = self.cube
        mapping: dict[FaceName, Color] = {
            f.name: f.original_color for f in cube.faces
        }
        # Pick the face whose original_color matches config's first_face_color
        start_color: Color = self.cmn.white
        l1_face: Face = next(
            f for f in cube.faces if f.original_color == start_color
        )
        return l1_face, mapping

    @contextmanager
    def apply_provider(self, face_colors: Mapping[FaceName, Color]) -> Generator[None, None, None]:
        """Activate a FacesColorsProvider on the cube."""
        provider: FacesColorsProvider = _SimpleFacesColorsProvider(face_colors)
        with self.cube.with_faces_color_provider(provider):
            yield
