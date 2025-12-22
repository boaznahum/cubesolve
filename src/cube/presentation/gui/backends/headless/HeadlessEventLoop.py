"""
Headless event loop implementation.

Provides a minimal event loop for testing that can be stepped manually
or run with scheduled callbacks.
"""

import time
from dataclasses import dataclass, field
from typing import Callable

from cube.presentation.gui.protocols import EventLoop


@dataclass
class _ScheduledCallback:
    """Internal class for tracking scheduled callbacks."""

    callback: Callable[[float], None]
    next_time: float
    interval: float | None = None  # None for one-shot, value for repeating


@dataclass
class HeadlessEventLoop(EventLoop):
    """Minimal event loop for headless testing.

    Features:
    - Manual stepping for deterministic testing
    - Scheduled callbacks (one-shot and interval)
    - Simulated time for testing time-dependent code

    Usage:
        loop = HeadlessEventLoop()

        # Schedule a callback
        loop.schedule_once(lambda dt: print(f"Called after {dt}s"), 1.0)

        # Step through events
        loop.step(timeout=0.1)

        # Or run until stopped
        loop.run()  # Call loop.stop() from a callback to exit
    """

    _running: bool = field(default=False, init=False)
    _should_stop: bool = field(default=False, init=False)
    _callbacks: list[_ScheduledCallback] = field(default_factory=list, init=False)
    _immediate_callbacks: list[Callable[[], None]] = field(default_factory=list, init=False)
    _start_time: float = field(default_factory=time.monotonic, init=False)
    _simulated_time: float | None = field(default=None, init=False)

    @property
    def running(self) -> bool:
        """Whether the event loop is running."""
        return self._running

    @property
    def has_exit(self) -> bool:
        """Whether the event loop has been signaled to exit."""
        return self._should_stop

    def run(self) -> None:
        """Run the event loop until stop() is called.

        Processes scheduled callbacks and immediate callbacks.
        """
        self._running = True
        self._should_stop = False

        while not self._should_stop:
            # Process immediate callbacks
            while self._immediate_callbacks:
                callback = self._immediate_callbacks.pop(0)
                callback()

            # Process scheduled callbacks
            current_time = self.get_time()
            processed = False

            for scheduled in self._callbacks[:]:  # Copy to allow modification
                if scheduled.next_time <= current_time:
                    dt = current_time - (scheduled.next_time - (scheduled.interval or 0))
                    scheduled.callback(dt)
                    processed = True

                    if scheduled.interval is not None:
                        # Repeating callback - schedule next
                        scheduled.next_time = current_time + scheduled.interval
                    else:
                        # One-shot - remove
                        self._callbacks.remove(scheduled)

            # If nothing to do, sleep briefly to prevent busy-waiting
            if not processed and not self._immediate_callbacks:
                time.sleep(0.001)

        self._running = False

    def stop(self) -> None:
        """Request the event loop to stop."""
        self._should_stop = True

    def step(self, timeout: float = 0.0) -> bool:
        """Process pending events without blocking indefinitely.

        Args:
            timeout: Maximum time to wait (0 = non-blocking)

        Returns:
            True if any callbacks were executed
        """
        processed = False
        current_time = self.get_time()

        # Process immediate callbacks
        while self._immediate_callbacks:
            callback = self._immediate_callbacks.pop(0)
            callback()
            processed = True

        # Process due scheduled callbacks
        for scheduled in self._callbacks[:]:
            if scheduled.next_time <= current_time:
                dt = current_time - (scheduled.next_time - (scheduled.interval or 0))
                scheduled.callback(dt)
                processed = True

                if scheduled.interval is not None:
                    scheduled.next_time = current_time + scheduled.interval
                else:
                    self._callbacks.remove(scheduled)

        # If timeout > 0 and nothing processed, wait
        if timeout > 0 and not processed:
            # Find next scheduled callback
            if self._callbacks:
                next_time = min(s.next_time for s in self._callbacks)
                wait_time = min(next_time - current_time, timeout)
                if wait_time > 0:
                    time.sleep(wait_time)
                    return self.step(0)  # Process after waiting

        return processed

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run once after delay.

        Args:
            callback: Function(dt) where dt is elapsed time
            delay: Delay in seconds
        """
        self._callbacks.append(
            _ScheduledCallback(
                callback=callback,
                next_time=self.get_time() + delay,
                interval=None,
            )
        )

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a callback to run repeatedly.

        Args:
            callback: Function(dt) where dt is time since last call
            interval: Interval in seconds
        """
        self._callbacks.append(
            _ScheduledCallback(
                callback=callback,
                next_time=self.get_time() + interval,
                interval=interval,
            )
        )

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Remove a scheduled callback.

        Args:
            callback: The callback function to remove
        """
        self._callbacks = [s for s in self._callbacks if s.callback is not callback]

    def call_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a callback to run immediately on next step.

        Args:
            callback: Function to call (no arguments)
        """
        self._immediate_callbacks.append(callback)

    def get_time(self) -> float:
        """Get current time in seconds.

        Returns simulated time if set, otherwise real monotonic time.
        """
        if self._simulated_time is not None:
            return self._simulated_time
        return time.monotonic() - self._start_time

    # Testing helpers

    def set_simulated_time(self, t: float | None) -> None:
        """Set simulated time for deterministic testing.

        Args:
            t: Simulated time in seconds, or None to use real time
        """
        self._simulated_time = t

    def advance_time(self, dt: float) -> None:
        """Advance simulated time by dt seconds.

        Only works when simulated time is enabled.

        Args:
            dt: Time to advance in seconds
        """
        if self._simulated_time is not None:
            self._simulated_time += dt

    def clear_callbacks(self) -> None:
        """Remove all scheduled callbacks (for testing cleanup)."""
        self._callbacks.clear()
        self._immediate_callbacks.clear()

    def idle(self) -> float:
        """Process any pending scheduled callbacks and return timeout until next.

        Returns:
            Timeout in seconds until next scheduled callback (0 if immediate)
        """
        # Process immediate callbacks first
        while self._immediate_callbacks:
            callback = self._immediate_callbacks.pop(0)
            callback()

        current_time = self.get_time()

        # Process due scheduled callbacks
        for scheduled in self._callbacks[:]:
            if scheduled.next_time <= current_time:
                dt = current_time - (scheduled.next_time - (scheduled.interval or 0))
                scheduled.callback(dt)

                if scheduled.interval is not None:
                    scheduled.next_time = current_time + scheduled.interval
                else:
                    self._callbacks.remove(scheduled)

        # Return timeout until next callback
        if self._callbacks:
            next_time = min(s.next_time for s in self._callbacks)
            return max(0.0, next_time - self.get_time())
        return 0.0

    def notify(self) -> None:
        """Wake up the event loop if it's waiting.

        In the headless implementation, this is a no-op since
        there's no blocking wait to interrupt.
        """
        pass  # No-op for headless - no blocking wait to interrupt

    @property
    def pending_callback_count(self) -> int:
        """Number of pending callbacks (for testing)."""
        return len(self._callbacks) + len(self._immediate_callbacks)
