"""Solver protocols - interfaces for dependency inversion."""

from .OperatorProtocol import OperatorProtocol
from .AnnotationProtocol import AnnotationProtocol, SupportsAnnotation

__all__ = [
    'OperatorProtocol',
    'AnnotationProtocol',
    'SupportsAnnotation',
]
