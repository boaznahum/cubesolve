from enum import unique, Enum


@unique
class SolverName(Enum):
    LBL = "LBL"
    CFOP = "CFOP"
    KOCIEMBA = "Kociemba"  # Near-optimal solver (18-22 moves)
    CAGE = "Cage"  # Cage method: edges+corners first, centers last (parity-free)
