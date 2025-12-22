from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@dataclass(frozen=True)
class SolverMeta:
    """
    Metadata for a solver, including test configuration.

    Reasons are checked in priority order (top to bottom).
    None = supported, string = skip reason.

    0. implemented - if False, solver is not available (app or tests)
    1. not_testable - if set, skip all tests (but solver may work in app)
    2. only_3x3 - if set, skip non-3x3 tests
    3. skip_3x3 - if set, skip 3x3 tests
    4. skip_even - if set, skip even-sized cube tests (4x4, 6x6, ...)
    5. skip_odd - if set, skip odd-sized cube tests (5x5, 7x7, ...)
    """
    display_name: str
    implemented: bool = True  # If False, solver not available anywhere
    not_testable: str | None = None
    only_3x3: str | None = None
    skip_3x3: str | None = None
    skip_even: str | None = None
    skip_odd: str | None = None

    def get_skip_reason(self, cube_size: int) -> str | None:
        """
        Check if solver should be skipped for given cube size.

        Returns skip reason string if should skip, None if supported.
        """
        if not self.implemented:
            return "Not implemented"
        if self.not_testable:
            return self.not_testable
        if self.only_3x3 and cube_size != 3:
            return self.only_3x3
        if self.skip_3x3 and cube_size == 3:
            return self.skip_3x3
        if self.skip_even and cube_size != 3 and cube_size % 2 == 0:
            return self.skip_even
        if self.skip_odd and cube_size != 3 and cube_size % 2 == 1:
            return self.skip_odd
        return None


@unique
class SolverName(Enum):
    """
    Available solver names.

    IMPORTANT: When modifying this enum (adding/removing solvers), you MUST also update:
    - src/cube/application/_config.py: Update the DEFAULT_SOLVER comment with available names
    - src/cube/domain/solver/Solvers.py: Update the by_name() match statement

    Each enum value contains SolverMeta with test skip reasons (None = supported).
    """
    LBL = SolverMeta("LBL")
    CFOP = SolverMeta("CFOP")#, only_3x3="CFOP use same reducer as LBL")
    KOCIEMBA = SolverMeta("Kociemba")
    CAGE = SolverMeta("Cage")  # Cage method: edges first, then corners, then centers

    @property
    def display_name(self) -> str:
        """Return the display name of the solver."""
        return self.value.display_name

    @property
    def meta(self) -> SolverMeta:
        """Return the solver metadata."""
        return self.value

    def __str__(self) -> str:
        """Return string representation of the solver name."""
        return self.display_name

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
            if solver.display_name.lower() == name_lower:
                return solver

        # Try prefix match
        matches: list[SolverName] = []
        for solver in cls:
            if solver.display_name.lower().startswith(name_lower):
                matches.append(solver)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            match_names = ", ".join(s.display_name for s in matches)
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
        return ", ".join(s.display_name for s in cls)
