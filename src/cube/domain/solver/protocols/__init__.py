"""Solver protocols - interfaces for dependency inversion."""

from .OperatorProtocol import OperatorProtocol
from .AnnotationProtocol import AnnotationProtocol, SupportsAnnotation
from .ReducerProtocol import ReducerProtocol, ReductionResults
from .Solver3x3Protocol import Solver3x3Protocol

__all__ = [
    'OperatorProtocol',
    'AnnotationProtocol',
    'SupportsAnnotation',
    'ReducerProtocol',
    'ReductionResults',
    'Solver3x3Protocol',
]
