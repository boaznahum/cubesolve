"""Solvers2x2 factory - creates 2x2 solver instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver.Solver2x2Name import Solver2x2Name
from cube.domain.solver.solver import Solver

if TYPE_CHECKING:
    from cube.domain.solver.protocols import OperatorProtocol
    from cube.utils.logger_protocol import ILogger


class Solvers2x2:
    """
    Factory for 2x2 cube solvers.

    Usage:
        solver = Solvers2x2.beginner(op, parent_logger)
        solver = Solvers2x2.ida(op, parent_logger)
        solver = Solvers2x2.by_name(Solver2x2Name.IDA, op, parent_logger)
    """

    @staticmethod
    def beginner(op: "OperatorProtocol", parent_logger: "ILogger") -> Solver:
        """Get the beginner layer-by-layer 2x2 solver."""
        from ._2x2_beginner.Solver2x2Beginner import Solver2x2Beginner
        return Solver2x2Beginner(op, parent_logger)

    @staticmethod
    def ida(op: "OperatorProtocol", parent_logger: "ILogger") -> Solver:
        """Get the IDA* optimal 2x2 solver."""
        from ._2x2_ida_optimal.Solver2x2IDA import Solver2x2IDA
        return Solver2x2IDA(op, parent_logger)

    @classmethod
    def by_name(cls, name: Solver2x2Name, op: "OperatorProtocol", parent_logger: "ILogger") -> Solver:
        """Get a 2x2 solver by its name.

        Args:
            name: Solver2x2Name enum value
            op: Operator for cube manipulation
            parent_logger: Parent logger
        """
        match name:
            case Solver2x2Name.BEGINNER:
                return cls.beginner(op, parent_logger)
            case Solver2x2Name.IDA:
                return cls.ida(op, parent_logger)
            case _:
                raise ValueError(f"Unknown 2x2 solver: {name}")
