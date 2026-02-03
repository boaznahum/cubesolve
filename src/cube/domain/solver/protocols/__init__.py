"""Solver protocols - interfaces for dependency inversion."""

from .AnnotationProtocol import AdditionalMarker, AnnotationProtocol, SupportsAnnotation
from .OperatorProtocol import OperatorProtocol
from .ReducerProtocol import ReducerProtocol, ReductionResults
from .Solver3x3Protocol import Solver3x3Protocol
from .SolverElementsProvider import SolverElementsProvider

__all__ = [
    'AdditionalMarker',
    'AnnotationProtocol',
    'OperatorProtocol',
    'ReducerProtocol',
    'ReductionResults',
    'Solver3x3Protocol',
    'SolverElementsProvider',
    'SupportsAnnotation',
]
