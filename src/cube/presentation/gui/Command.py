"""
DEPRECATED: This module is deprecated. Use cube.presentation.gui.commands instead.

This module exists only for backward compatibility with archived code.
All new code should import from cube.presentation.gui.commands.

Example:
    # Old (deprecated):
    from cube.presentation.gui.Command import Command, CommandContext

    # New (preferred):
    from cube.presentation.gui.commands import Command, CommandContext, Commands
"""
from cube.presentation.gui.commands import (
    Command,
    CommandContext,
    CommandResult,
    Commands,
    CommandSequence,
)

__all__ = [
    "Command",
    "CommandContext",
    "CommandResult",
    "CommandSequence",
    "Commands",
]
