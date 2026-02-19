from dataclasses import dataclass
from typing import Tuple


@dataclass
class FaceTrackerConfig:
    """Configuration for face tracker visual annotations and validation.

    Access via ConfigProtocol.face_tracker property.
    """
    # Add visual markers (dots) on tracked center slices for debugging
    annotate: bool

    # Validate trackers on cache rebuild (no duplicates, valid BOY layout, before after)
    validate: bool

    # When cleaning up trackers, leave the last visual annotation on screen
    leave_last_annotation: bool

    # Use SimpleFaceTracker with BOY predicate for face 5 (self-healing).
    # When False, use MarkedFaceTracker on face 5 (like faces 1-4).
    use_simple_f5_tracker: bool

    enable_track_piece_caching: bool


@dataclass
class TrackerIndicatorConfig:
    """Configuration for tracker indicator visuals on center slices.

    Controls the small colored circle drawn on tracked center slices
    showing which color "owns" the piece (even cubes only).

    Access via ConfigProtocol.tracker_indicator property.
    """
    # Radius as fraction of cell size (0.0-1.0)
    radius_factor: float = 0.35

    # Height offset above surface as fraction of cell size
    height_offset: float = 0.10

    # Black outline width as fraction of radius (0.0-1.0)
    outline_width_factor: float = 0.30

    # Outline color (RGB 0.0-1.0)
    outline_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Minimum absolute radius in world units — ensures visibility on big cubes (14+)
    # On 18x18: cell_size~5.56, so min_radius=3.5 makes indicator ~63% of cell
    min_radius: float = 3.5

    # Minimum absolute outline width in world units
    min_outline_width: float = 0.5
