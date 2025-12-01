from enum import unique, Enum


@unique
class SolverName(Enum):
    LBL="LBL"
    CFOP = "CFOP"
