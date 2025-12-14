"""Reducers factory - creates reducer instances for NxN to 3x3 reduction."""

from __future__ import annotations

from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import ReducerProtocol


class Reducers:
    """
    Factory for NxN to 3x3 cube reducers.

    Currently provides a single implementation (BeginnerReducer) with
    configurable parity algorithm. Future implementations can add
    faster or different reduction strategies.

    Usage:
        reducer = Reducers.default(op)
        reducer = Reducers.beginner(op, advanced_edge_parity=True)
    """

    @staticmethod
    def default(op: OperatorProtocol) -> ReducerProtocol:
        """
        Get the default reducer.

        Currently returns BeginnerReducer with basic edge parity.

        Args:
            op: Operator for cube manipulation

        Returns:
            Default reducer instance
        """
        return Reducers.beginner(op, advanced_edge_parity=False)

    @staticmethod
    def beginner(
        op: OperatorProtocol,
        advanced_edge_parity: bool = False
    ) -> ReducerProtocol:
        """
        Get beginner reducer with configurable parity algorithm.

        Args:
            op: Operator for cube manipulation
            advanced_edge_parity: If True, use advanced R/L-slice parity algorithm.
                                  If False, use simple M-slice parity algorithm.

        Returns:
            BeginnerReducer instance
        """
        from cube.domain.solver.reducers.BeginnerReducer import BeginnerReducer
        return BeginnerReducer(op, advanced_edge_parity)

    @staticmethod
    def advanced(op: OperatorProtocol) -> ReducerProtocol:
        """
        Get reducer with advanced edge parity algorithm.

        This is a convenience method equivalent to:
        Reducers.beginner(op, advanced_edge_parity=True)

        Args:
            op: Operator for cube manipulation

        Returns:
            BeginnerReducer with advanced parity
        """
        return Reducers.beginner(op, advanced_edge_parity=True)
