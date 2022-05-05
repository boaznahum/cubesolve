from abc import ABC, abstractmethod
from _solver.isolver import ISolver
from cube import Cube
from cube_operator import Operator





class SolverElement:
    __slots__ = ["_solver"]

    _solver: ISolver

    def __init__(self, solver: ISolver) -> None:
        self._solver = solver

    def debug(self, *args):
        self._solver.debug(args)

    @property
    def cube(self) -> Cube:
        return self._solver.cube

    @property
    def op(self) -> Operator:
        return self._solver.op

    @property
    def cmn(self):
        return self._solver.cmn


