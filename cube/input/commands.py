"""
Base command classes and command results.

Commands encapsulate actions that can be triggered by keyboard input, mouse input,
or automated tests. They operate on an AppContext and return a CommandResult.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.model.cube import Cube
    from cube.operator.cube_operator import Operator
    from cube.app.app_state import ApplicationAndViewState
    from cube.solver.solver import Solver


class AppContext(Protocol):
    """
    Application context that commands operate on.

    This protocol defines what dependencies commands need access to.
    It matches the interface of AbstractApp and AbstractWindow.
    """

    @property
    def cube(self) -> 'Cube':
        """The cube model"""
        ...

    @property
    def op(self) -> 'Operator':
        """The operator that executes algorithms"""
        ...

    @property
    def vs(self) -> 'ApplicationAndViewState':
        """Application and view state"""
        ...

    @property
    def slv(self) -> 'Solver':
        """The solver"""
        ...

    # Window-specific properties (may be None in tests)
    @property
    def window(self) -> 'AbstractWindow | None':
        """The window (None in headless tests)"""
        ...


@dataclass
class CommandResult:
    """
    Result of executing a command.

    Attributes:
        needs_redraw: Whether the GUI needs to be redrawn
        needs_viewer_reset: Whether the viewer needs to be reset (cube size changed)
        error: Error message if command failed, None if successful
        should_quit: Whether the application should quit
    """
    needs_redraw: bool = True
    needs_viewer_reset: bool = False
    error: str | None = None
    should_quit: bool = False

    @staticmethod
    def success(needs_redraw: bool = True) -> 'CommandResult':
        """Create a successful result"""
        return CommandResult(needs_redraw=needs_redraw)

    @staticmethod
    def no_op() -> 'CommandResult':
        """Create a no-op result (no redraw needed)"""
        return CommandResult(needs_redraw=False)

    @staticmethod
    def error(message: str) -> 'CommandResult':
        """Create an error result"""
        return CommandResult(error=message, needs_redraw=False)

    @staticmethod
    def quit() -> 'CommandResult':
        """Create a quit result"""
        return CommandResult(should_quit=True, needs_redraw=False)


class Command(ABC):
    """
    Base class for all commands.

    Commands encapsulate actions that can be executed on the application context.
    They are the unit of work for both interactive GUI and automated testing.
    """

    @abstractmethod
    def execute(self, ctx: AppContext) -> CommandResult:
        """
        Execute this command on the given context.

        Args:
            ctx: The application context to operate on

        Returns:
            CommandResult indicating what happened and what needs updating

        Raises:
            May raise AppExit or other exceptions for flow control
        """
        pass

    def can_execute_during_animation(self) -> bool:
        """
        Whether this command can execute while animation is running.

        Most commands cannot execute during animation. Exceptions include:
        - View adjustments (rotation, zoom, pan)
        - Animation control (pause, resume, abort)
        - Quit

        Returns:
            True if this command can run during animation, False otherwise
        """
        return False

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"{self.__class__.__name__}()"
