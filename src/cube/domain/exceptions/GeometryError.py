"""Geometry-related errors with error codes.

Raised when geometry operations detect invalid configurations.
Uses error codes to distinguish different error types without
creating many exception classes.
"""

from enum import Enum, auto


class GeometryErrorCode(Enum):
    """Error codes for geometry operations."""

    SAME_FACE = auto()       # source and target are the same face
    OPPOSITE_FACES = auto()  # faces are opposite (don't share an edge)
    INVALID_FACE = auto()    # unknown or invalid face
    INVALID_PRESERVE_ROTATION = auto()  # can't reach target while preserving face
    FACE_NOT_PARALLEL_TO_SLICE = auto()  # face must be parallel to slice (e.g., L/R for M slice)
    FACE_IS_PARALLEL_TO_SLICE = auto()   # face must be cut by slice, not parallel to it


class GeometryError(Exception):
    """Geometry-related error with an error code.

    Attributes:
        code: The specific error code identifying the error type.
    """

    def __init__(self, code: GeometryErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.name}: {message}")
