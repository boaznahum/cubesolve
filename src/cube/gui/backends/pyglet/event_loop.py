"""
Pyglet event loop implementation.

Wraps pyglet.app event loop to implement the EventLoop protocol.
"""

from typing import Callable

try:
    import pyglet
except ImportError as e:
    raise ImportError("pyglet is required for PygletEventLoop: pip install pyglet") from e

from cube.gui.protocols.event_loop import EventLoop


class PygletEventLoop(EventLoop):
    """Pyglet event loop implementing EventLoop protocol.

    Wraps pyglet's event loop and clock for scheduling.
    """

    def __init__(self) -> None:
        self._running = False
        self._should_stop = False
        self._event_loop = pyglet.app.event_loop
        self._platform_loop = pyglet.app.platform_event_loop
        self._clock = pyglet.clock.get_default()
        self._scheduled_callbacks: list[Callable[[float], None]] = []

    @property
    def running(self) -> bool:
        """Whether the event loop is running."""
        return self._running

    @property
    def has_exit(self) -> bool:
        """Whether the event loop has been signaled to exit."""
        return self._event_loop.has_exit or self._should_stop

    def run(self) -> None:
        """Run the event loop until stop() is called.

        This starts the pyglet main loop.
        """
        self._running = True
        self._should_stop = False

        try:
            # Use pyglet's standard run() which properly handles window events
            pyglet.app.run()
        finally:
            self._running = False

    def stop(self) -> None:
        """Request the event loop to stop."""
        self._should_stop = True
        self._event_loop.exit()

    def step(self, timeout: float = 0.0) -> bool:
        """Process pending events without blocking indefinitely.

        Args:
            timeout: Maximum time to wait (0 = non-blocking)

        Returns:
            True if any events were processed
        """
        # Tick the clock to process scheduled callbacks
        self._clock.tick()

        # Step platform event loop
        self._platform_loop.step(timeout)

        return True  # Pyglet doesn't report if events were processed

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run once after delay.

        Args:
            callback: Function(dt) where dt is elapsed time
            delay: Delay in seconds
        """
        pyglet.clock.schedule_once(callback, delay)

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a callback to run repeatedly.

        Args:
            callback: Function(dt) where dt is time since last call
            interval: Interval in seconds
        """
        pyglet.clock.schedule_interval(callback, interval)
        self._scheduled_callbacks.append(callback)

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Remove a scheduled callback.

        Args:
            callback: The callback function to remove
        """
        pyglet.clock.unschedule(callback)
        if callback in self._scheduled_callbacks:
            self._scheduled_callbacks.remove(callback)

    def call_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a callback to run immediately on next step.

        Args:
            callback: Function to call (no arguments)
        """
        # Wrap to match schedule_once signature
        def wrapper(dt: float) -> None:
            callback()

        pyglet.clock.schedule_once(wrapper, 0)

    def get_time(self) -> float:
        """Get current time in seconds.

        Returns monotonic time since event loop was created.
        """
        return pyglet.clock.get_default().time()

    def clear_callbacks(self) -> None:
        """Remove all scheduled callbacks (for cleanup)."""
        for callback in self._scheduled_callbacks[:]:
            pyglet.clock.unschedule(callback)
        self._scheduled_callbacks.clear()

    def idle(self) -> float:
        """Process any pending scheduled callbacks and return timeout until next.

        Returns:
            Timeout in seconds until next scheduled callback (0 if immediate)
        """
        return self._event_loop.idle()

    def notify(self) -> None:
        """Wake up the event loop if it's waiting.

        Used to signal that there's work to do, for example after
        changing state that should trigger a redraw.
        """
        self._platform_loop.notify()
