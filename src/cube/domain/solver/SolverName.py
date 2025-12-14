from enum import unique, Enum


@unique
class SolverName(Enum):
    """
    Available solver names.

    IMPORTANT: When modifying this enum (adding/removing solvers), you MUST also update:
    - src/cube/application/_config.py: Update the DEFAULT_SOLVER comment with available names
    - src/cube/domain/solver/Solvers.py: Update the by_name() match statement
    """
    LBL = "LBL"
    CFOP = "CFOP"
    KOCIEMBA = "Kociemba"  # Near-optimal solver (18-22 moves)
    CAGE = "Cage"  # Cage method: edges+corners first, centers last (parity-free)

    @classmethod
    def lookup(cls, name: str) -> "SolverName":
        """
        Look up a solver by name with case-insensitive and prefix matching.

        Args:
            name: Solver name (case-insensitive), can be a prefix if unambiguous

        Returns:
            Matching SolverName enum value

        Raises:
            ValueError: If name doesn't match any solver or matches multiple solvers

        Examples:
            SolverName.lookup("lbl") -> SolverName.LBL
            SolverName.lookup("ca") -> SolverName.CAGE
            SolverName.lookup("c") -> ValueError (ambiguous: CFOP, CAGE)
        """
        name_lower = name.lower()

        # Try exact match first (case-insensitive)
        for solver in cls:
            if solver.value.lower() == name_lower:
                return solver

        # Try prefix match
        matches: list[SolverName] = []
        for solver in cls:
            if solver.value.lower().startswith(name_lower):
                matches.append(solver)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            match_names = ", ".join(s.value for s in matches)
            raise ValueError(
                f"Ambiguous solver name '{name}' matches: {match_names}. "
                f"Available: {cls.available_names()}"
            )
        else:
            raise ValueError(
                f"Unknown solver '{name}'. Available: {cls.available_names()}"
            )

    @classmethod
    def available_names(cls) -> str:
        """Return comma-separated list of available solver names."""
        return ", ".join(s.value for s in cls)
