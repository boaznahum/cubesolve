"""
Event loop protocol definition.

This protocol defines the interface for the main application event loop.
"""

from typing import Protocol, Callable, runtime_checkable


@runtime_checkable
class EventLoop(Protocol):
    """Protocol for the main event loop.

    Backends implement this to provide event processing and scheduling.
    The event loop handles window events, timers, and callbacks.
    """

    @property
    def running(self) -> bool:
        """Whether the event loop is currently running."""
        ...

    def run(self) -> None:
        """Start the event loop (blocking).

        Processes events until stop() is called or all windows are closed.
        """
        ...

    def stop(self) -> None:
        """Request the event loop to stop.

        The loop will exit after processing current events.
        """
        ...

    def step(self, timeout: float = 0.0) -> bool:
        """Process pending events without blocking.

        Args:
            timeout: Maximum time to wait for events in seconds (0 = non-blocking)

        Returns:
            True if events were processed, False if idle
        """
        ...

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run once after delay.

        Args:
            callback: Function receiving elapsed time since scheduling
            delay: Delay in seconds before calling
        """
        ...

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a callback to run repeatedly at interval.

        Args:
            callback: Function receiving time since last call
            interval: Interval in seconds between calls
        """
        ...

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Remove a scheduled callback.

        Args:
            callback: Previously scheduled function to remove
        """
        ...

    def call_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a callback to run as soon as possible.

        The callback runs on the next iteration of the event loop.

        Args:
            callback: Function to call (no arguments)
        """
        ...

    def get_time(self) -> float:
        """Get current time in seconds.

        Returns:
            Time in seconds (monotonic, suitable for measuring intervals)
        """
        ...
