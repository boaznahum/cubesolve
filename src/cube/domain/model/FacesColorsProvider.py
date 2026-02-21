"""Protocol for providing face colors on even cubes.

On even cubes (4x4, 6x6, etc.), Face.color reads from a center piece at
(n//2, n//2) which is unreliable during solving -- commutators move center
pieces, changing what face.color returns. This protocol allows overriding
Face.color with tracker-assigned colors.

See: docs/design/even-cube-plan.md
"""

from __future__ import annotations

from typing import Protocol

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName


class FacesColorsProvider(Protocol):
    """Provider of reliable face colors for even cubes.

    Implementations (e.g., FacesTrackerHolder) return the target color
    for each face based on tracker analysis, not center piece position.
    """

    def get_face_color(self, face_name: FaceName) -> Color:
        """Get the target color for a specific face.

        Args:
            face_name: The face to query.

        Returns:
            The target color for that face.
        """
        ...
