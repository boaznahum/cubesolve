"""
Command system - type-safe command pattern using frozen dataclasses.

Each command is a frozen dataclass that is:
- Hashable (can be used as dict key, in sets)
- Immutable (safe to share)
- Type-safe (pyright can verify all attribute access)

Usage:
    from cube.presentation.gui.commands import Command, Commands, CommandContext

    # Execute single command
    ctx = CommandContext.from_window(window)
    Commands.SCRAMBLE_1.execute(ctx)

    # Build command sequences with + and *
    seq = Commands.SPEED_UP * 5 + Commands.SCRAMBLE_1 + Commands.SOLVE_ALL + Commands.QUIT
    seq.execute_all(ctx)
"""
from .base import Command, CommandContext, CommandResult, CommandSequence
from .registry import Commands

__all__ = [
    "Command",
    "CommandContext",
    "CommandResult",
    "CommandSequence",
    "Commands",
]
