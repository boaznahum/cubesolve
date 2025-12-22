"""Solver protocols - interfaces for dependency inversion."""

from .AnnotationProtocol import AnnotationProtocol, SupportsAnnotation
from .OperatorProtocol import OperatorProtocol
from .ReducerProtocol import ReducerProtocol, ReductionResults
from .Solver3x3Protocol import Solver3x3Protocol
from .SolverElementsProvider import SolverElementsProvider

__all__ = [
    'OperatorProtocol',
    'AnnotationProtocol',
    'SupportsAnnotation',
    'ReducerProtocol',
    'ReductionResults',
    'Solver3x3Protocol',
    'SolverElementsProvider',
]
