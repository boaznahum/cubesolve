# answer all the geometric questions of the cube
# see issue #55 https://github.com/boaznahum/cubesolve/issues/55#issue-3765157931
#
# NOTE: This module intentionally avoids importing from submodules at the top level
# to prevent circular imports. Import directly from the specific modules:
#
#   from cube.domain.geometric.cube_layout import CubeLayout, opposite, is_adjacent
#   from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator
#   etc.
#
# The create_layout() function is provided as a convenience factory.

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from cube.domain.geometric.cube_layout import CubeLayout
    from cube.domain.model.Color import Color
    from cube.domain.model.FaceName import FaceName
    from cube.utils.service_provider import IServiceProvider


def create_layout(
    read_only: bool,
    faces: Mapping[FaceName, Color],
    sp: IServiceProvider
) -> CubeLayout:
    """Create a CubeLayout from face-color mapping.

    .. deprecated::
        Use CubeLayout.create_layout() instead. This function is kept for
        backward compatibility and will be removed in a future version.

    Factory function to create layout instances without exposing
    the private implementation class.

    Args:
        read_only: If True, layout cannot be modified (used for singletons).
        faces: Mapping of each face to its color.
        sp: Service provider for configuration access.

    Returns:
        CubeLayout instance with the given configuration.
    """
    from cube.domain.geometric.cube_layout import CubeLayout
    return CubeLayout.create_layout(read_only, faces, sp)


__all__ = [
    'create_layout',
]
