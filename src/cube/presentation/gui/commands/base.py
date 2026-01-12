"""
Base classes for the command system.

Command is an abstract frozen dataclass that all concrete commands inherit from.
Commands are hashable and singleton-like (identical commands return same instance).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.application.commands.Operator import Operator
    from cube.application.protocols.AnimatableViewer import AnimatableViewer
    from cube.application.state import ApplicationAndViewState
    from cube.domain.model.Cube import Cube
    from cube.domain.solver import Solver
    from cube.presentation.gui.protocols.AppWindow import AppWindow


# =============================================================================
# COMMAND CONTEXT
# =============================================================================

@dataclass
class CommandContext:
    """Execution context for commands.

    Provides access to all application components needed by command handlers.
    All properties have explicit return types - no duck typing.
    """
    window: "AppWindow"

    @property
    def app(self) -> "AbstractApp":
        return self.window.app

    @property
    def op(self) -> "Operator":
        return self.app.op

    @property
    def vs(self) -> "ApplicationAndViewState":
        return self.app.vs

    @property
    def slv(self) -> "Solver":
        return self.app.slv

    @property
    def cube(self) -> "Cube":
        return self.app.cube

    @property
    def viewer(self) -> "AnimatableViewer":
        return self.window.viewer

    @classmethod
    def from_window(cls, window: "AppWindow") -> "CommandContext":
        """Create context from a window."""
        return cls(window=window)


# =============================================================================
# RESULT TYPE
# =============================================================================

@dataclass
class CommandResult:
    """Result of command execution."""
    handled: bool = True
    no_gui_update: bool = False  # True if GUI doesn't need updating
    delay_next_command: float = 0.0  # Delay before executing next command (seconds)


# =============================================================================
# COMMAND BASE CLASS
# =============================================================================

@dataclass(frozen=True)
class Command(ABC):
    """Abstract base class for all commands.

    Each concrete command type is a frozen dataclass, making it:
    - Hashable (can be used as dict key, in sets)
    - Immutable (safe to share across threads)
    - Type-safe (pyright can verify attribute access)

    Instance interning ensures that identical commands return the same object.
    """

    # Class-level cache for instance interning
    _instance_cache: ClassVar[dict[tuple, "Command"]] = {}

    def __new__(cls, *args, **kwargs):
        """
        Intern instances to ensure singleton-like behavior.

        This ensures that identical commands (same class and args) return
        the same instance, making commands suitable for dict keys and sets.
        """
        # Build cache key from class and all arguments
        key = (cls, args, tuple(sorted(kwargs.items())))

        if key in Command._instance_cache:
            return Command._instance_cache[key]

        # Create new instance
        instance = object.__new__(cls)
        Command._instance_cache[key] = instance
        return instance

    @abstractmethod
    def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute this command with the given context."""
        ...

    @property
    def name(self) -> str:
        """Get command name for display/debugging."""
        return self.__class__.__name__

    def __add__(self, other: "Command | CommandSequence") -> "CommandSequence":
        """Concatenate with another command or sequence.

        Example:
            seq = Commands.SCRAMBLE_1 + Commands.SOLVE_ALL + Commands.QUIT
        """
        if isinstance(other, CommandSequence):
            return CommandSequence([self] + other._commands)
        else:
            return CommandSequence([self, other])

    def __mul__(self, n: int) -> "CommandSequence":
        """Repeat this command n times.

        Example:
            seq = Commands.SPEED_UP * 5  # 5 speed-ups
        """
        return CommandSequence([self] * n)

    def __rmul__(self, n: int) -> "CommandSequence":
        """Support n * Command syntax."""
        return self.__mul__(n)


# =============================================================================
# COMMAND SEQUENCE
# =============================================================================

class CommandSequence:
    """A sequence of commands that can be executed together.

    Supports + and * operators for building sequences:
        seq = Commands.SPEED_UP * 3 + Commands.SCRAMBLE_1 + Commands.SOLVE_ALL

    Usage:
        seq.execute_all(ctx)  # Execute all commands in sequence
    """

    def __init__(self, commands: Sequence[Command] | None = None):
        """Initialize with optional list of commands."""
        self._commands: list[Command] = list(commands) if commands else []

    @property
    def commands(self) -> list[Command]:
        """Get the list of commands."""
        return self._commands

    def __add__(self, other: "Command | CommandSequence") -> "CommandSequence":
        """Concatenate with another command or sequence."""
        if isinstance(other, CommandSequence):
            return CommandSequence(self._commands + other._commands)
        else:
            # other is a Command
            return CommandSequence(self._commands + [other])

    def __radd__(self, other: Command) -> "CommandSequence":
        """Support Command + CommandSequence."""
        return CommandSequence([other] + self._commands)

    def __mul__(self, n: int) -> "CommandSequence":
        """Repeat the sequence n times."""
        return CommandSequence(self._commands * n)

    def __rmul__(self, n: int) -> "CommandSequence":
        """Support n * sequence."""
        return self.__mul__(n)

    def __len__(self) -> int:
        """Number of commands in sequence."""
        return len(self._commands)

    def __iter__(self):
        """Iterate over commands."""
        return iter(self._commands)

    def __repr__(self) -> str:
        """String representation."""
        cmd_names = [cmd.name for cmd in self._commands]
        return f"CommandSequence([{', '.join(cmd_names)}])"

    def execute_all(self, ctx: CommandContext) -> list[CommandResult]:
        """Execute all commands in sequence.

        Args:
            ctx: CommandContext providing access to app components

        Returns:
            List of CommandResult from each command
        """
        results = []
        for cmd in self._commands:
            results.append(cmd.execute(ctx))
        return results
