from dataclasses import dataclass


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
