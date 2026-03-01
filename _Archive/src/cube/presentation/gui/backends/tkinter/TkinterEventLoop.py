"""
Tkinter event loop implementation.

Wraps tk.Tk.mainloop() to implement the EventLoop protocol.
"""

import time
from dataclasses import dataclass
from typing import Callable

from cube.presentation.gui.protocols import EventLoop


@dataclass
class _ScheduledCallback:
    """Internal class for tracking scheduled callbacks."""
    callback: Callable[[float], None]
    next_time: float
    interval: float | None = None  # None for one-shot, value for repeating
    after_id: str | None = None  # Tkinter after() ID for cancellation


class TkinterEventLoop(EventLoop):
    """Event loop using Tkinter's mainloop().

    Uses tk.after() for scheduling callbacks and tk.mainloop() for
    the main event loop.
    """

    def __init__(self) -> None:
        self._running = False
        self._should_stop = False
        self._root = None  # Set by set_root()
        self._callbacks: list[_ScheduledCallback] = []
        self._immediate_callbacks: list[Callable[[], None]] = []
        self._start_time = time.monotonic()

    def set_root(self, root) -> None:
        """Set the Tk root window for scheduling.

        Args:
            root: The tk.Tk root window
        """
        self._root = root

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

        Uses tk.mainloop() as the main event loop.
        """
        if not self._root:
            raise RuntimeError("Event loop root not set. Call set_root() first.")

        self._running = True
        self._should_stop = False

        # Process any immediate callbacks before starting
        self._process_immediate()

        # Run Tkinter mainloop
        try:
            self._root.mainloop()
        except Exception:
            pass  # Window may have been destroyed

        self._running = False

    def stop(self) -> None:
        """Request the event loop to stop."""
        self._should_stop = True
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass  # Window may already be destroyed

    def step(self, timeout: float = 0.0) -> bool:
        """Process pending events without blocking indefinitely.

        Args:
            timeout: Maximum time to wait (0 = non-blocking)

        Returns:
            True if any callbacks were executed
        """
        if not self._root:
            return False

        processed = False

        # Process immediate callbacks
        if self._immediate_callbacks:
            self._process_immediate()
            processed = True

        # Update Tkinter (process pending events)
        try:
            self._root.update()
            processed = True
        except Exception:
            pass

        # Process scheduled callbacks that are due
        current_time = self.get_time()
        for scheduled in self._callbacks[:]:
            if scheduled.next_time <= current_time:
                dt = current_time - (scheduled.next_time - (scheduled.interval or 0))
                try:
                    scheduled.callback(dt)
                except Exception:
                    pass
                processed = True

                if scheduled.interval is not None:
                    scheduled.next_time = current_time + scheduled.interval
                else:
                    self._callbacks.remove(scheduled)

        return processed

    def _process_immediate(self) -> None:
        """Process all immediate callbacks."""
        while self._immediate_callbacks:
            callback = self._immediate_callbacks.pop(0)
            try:
                callback()
            except Exception:
                pass

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run once after delay.

        Args:
            callback: Function(dt) where dt is elapsed time
            delay: Delay in seconds
        """
        scheduled = _ScheduledCallback(
            callback=callback,
            next_time=self.get_time() + delay,
            interval=None,
        )
        self._callbacks.append(scheduled)

        # Also schedule with Tkinter for accurate timing
        if self._root:
            def _wrapper():
                if scheduled in self._callbacks:
                    self._callbacks.remove(scheduled)
                    try:
                        callback(delay)
                    except Exception:
                        pass

            scheduled.after_id = self._root.after(int(delay * 1000), _wrapper)

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a callback to run repeatedly.

        Args:
            callback: Function(dt) where dt is time since last call
            interval: Interval in seconds
        """
        scheduled = _ScheduledCallback(
            callback=callback,
            next_time=self.get_time() + interval,
            interval=interval,
        )
        self._callbacks.append(scheduled)

        # Set up repeating Tkinter callback
        if self._root:
            root = self._root  # Capture non-None root for closure

            def _wrapper() -> None:
                if scheduled in self._callbacks:
                    try:
                        callback(interval)
                    except Exception:
                        pass
                    # Reschedule
                    scheduled.after_id = root.after(int(interval * 1000), _wrapper)
                    scheduled.next_time = self.get_time() + interval

            scheduled.after_id = root.after(int(interval * 1000), _wrapper)

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Remove a scheduled callback.

        Args:
            callback: The callback function to remove
        """
        for scheduled in self._callbacks[:]:
            if scheduled.callback is callback:
                if scheduled.after_id and self._root:
                    try:
                        self._root.after_cancel(scheduled.after_id)
                    except Exception:
                        pass
                self._callbacks.remove(scheduled)

    def call_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a callback to run immediately on next step.

        Args:
            callback: Function to call (no arguments)
        """
        self._immediate_callbacks.append(callback)

        # Also schedule with Tkinter
        if self._root:
            self._root.after_idle(lambda: None)  # Trigger update

    def get_time(self) -> float:
        """Get current time in seconds since event loop creation."""
        return time.monotonic() - self._start_time

    def idle(self) -> float:
        """Process any pending scheduled callbacks and return timeout until next.

        Returns:
            Timeout in seconds until next scheduled callback (0 if immediate)
        """
        # Process immediate callbacks
        self._process_immediate()

        current_time = self.get_time()

        # Process due scheduled callbacks
        for scheduled in self._callbacks[:]:
            if scheduled.next_time <= current_time:
                dt = current_time - (scheduled.next_time - (scheduled.interval or 0))
                try:
                    scheduled.callback(dt)
                except Exception:
                    pass

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

        Triggers a Tkinter update to process pending events.
        """
        if self._root:
            try:
                self._root.after_idle(lambda: None)
            except Exception:
                pass

    def clear_callbacks(self) -> None:
        """Remove all scheduled callbacks."""
        for scheduled in self._callbacks:
            if scheduled.after_id and self._root:
                try:
                    self._root.after_cancel(scheduled.after_id)
                except Exception:
                    pass
        self._callbacks.clear()
        self._immediate_callbacks.clear()
