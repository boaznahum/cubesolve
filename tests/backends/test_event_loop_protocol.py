"""
Tests for EventLoop protocol implementation.

These tests verify that backend event loops correctly implement
the EventLoop protocol.
"""

import pytest
import time

from cube.presentation.gui.protocols import EventLoop


class TestEventLoopProtocol:
    """Tests for the EventLoop protocol."""

    def test_event_loop_running_property(self, event_loop: EventLoop, backend_name: str):
        """EventLoop must have running property."""
        assert hasattr(event_loop, 'running')
        assert isinstance(event_loop.running, bool)

    def test_event_loop_not_running_initially(self, event_loop: EventLoop, backend_name: str):
        """EventLoop should not be running initially."""
        assert not event_loop.running

    def test_get_time(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.get_time() should return a float."""
        t = event_loop.get_time()
        assert isinstance(t, float)
        assert t >= 0

    def test_get_time_increases(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.get_time() should increase over time."""
        t1 = event_loop.get_time()
        time.sleep(0.01)  # Small delay
        t2 = event_loop.get_time()
        assert t2 >= t1

    def test_step_returns_bool(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.step() should return a boolean."""
        result = event_loop.step(timeout=0)
        assert isinstance(result, bool)


class TestEventLoopScheduling:
    """Tests for EventLoop scheduling methods."""

    def test_schedule_once(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.schedule_once() should schedule a callback."""
        called = []
        event_loop.schedule_once(lambda dt: called.append(dt), delay=0)
        event_loop.step(timeout=0.1)
        assert len(called) == 1

    def test_schedule_once_with_delay(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.schedule_once() should respect delay."""
        called = []
        event_loop.schedule_once(lambda dt: called.append('a'), delay=0.05)

        # Should not be called immediately
        event_loop.step(timeout=0)
        assert called == []

        # Should be called after delay
        time.sleep(0.06)
        event_loop.step(timeout=0)
        assert called == ['a']

    def test_schedule_interval(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.schedule_interval() should schedule repeating callback."""
        called = []
        callback = lambda dt: called.append(len(called))
        event_loop.schedule_interval(callback, interval=0.02)

        # Step multiple times
        for _ in range(5):
            time.sleep(0.025)
            event_loop.step(timeout=0)

        # Should have been called multiple times
        assert len(called) >= 2

        # Clean up
        event_loop.unschedule(callback)

    def test_unschedule(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.unschedule() should remove callback."""
        called = []
        callback = lambda dt: called.append(True)
        event_loop.schedule_interval(callback, interval=0.01)

        # Let it run once
        time.sleep(0.015)
        event_loop.step(timeout=0)
        initial_count = len(called)
        assert initial_count >= 1

        # Unschedule
        event_loop.unschedule(callback)

        # Should not be called again
        time.sleep(0.03)
        event_loop.step(timeout=0)
        assert len(called) == initial_count

    def test_call_soon(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.call_soon() should call callback on next step."""
        called = []
        event_loop.call_soon(lambda: called.append('immediate'))
        event_loop.step(timeout=0)
        assert called == ['immediate']

    def test_multiple_call_soon(self, event_loop: EventLoop, backend_name: str):
        """Multiple call_soon() callbacks should be called in order."""
        called = []
        event_loop.call_soon(lambda: called.append('a'))
        event_loop.call_soon(lambda: called.append('b'))
        event_loop.call_soon(lambda: called.append('c'))
        event_loop.step(timeout=0)
        assert called == ['a', 'b', 'c']


class TestEventLoopRunStop:
    """Tests for EventLoop run/stop behavior."""

    def test_stop_from_callback(self, event_loop: EventLoop, backend_name: str):
        """EventLoop.run() should exit when stop() is called."""
        event_loop.call_soon(lambda: event_loop.stop())
        event_loop.run()
        assert not event_loop.running

    def test_stop_from_scheduled_callback(self, event_loop: EventLoop, backend_name: str):
        """EventLoop should stop from scheduled callback."""
        event_loop.schedule_once(lambda dt: event_loop.stop(), delay=0.01)
        event_loop.run()
        assert not event_loop.running


class TestHeadlessEventLoopSimulation:
    """Tests specific to headless event loop time simulation.

    These tests only run with the headless backend.
    """

    @pytest.fixture
    def headless_loop(self, event_loop: EventLoop, backend_name: str):
        """Get event loop only if headless backend."""
        if backend_name != "headless":
            pytest.skip("Time simulation only available in headless backend")
        return event_loop

    def test_simulated_time(self, headless_loop, backend_name: str):
        """Headless loop should support simulated time."""
        headless_loop.set_simulated_time(0.0)
        assert headless_loop.get_time() == 0.0

        headless_loop.set_simulated_time(10.0)
        assert headless_loop.get_time() == 10.0

    def test_advance_time(self, headless_loop, backend_name: str):
        """Headless loop should support advancing simulated time."""
        headless_loop.set_simulated_time(0.0)
        headless_loop.advance_time(5.0)
        assert headless_loop.get_time() == 5.0

    def test_scheduled_callback_with_simulated_time(self, headless_loop, backend_name: str):
        """Scheduled callbacks should work with simulated time."""
        headless_loop.set_simulated_time(0.0)
        called = []
        headless_loop.schedule_once(lambda dt: called.append('a'), delay=1.0)

        # Not called yet
        headless_loop.step(timeout=0)
        assert called == []

        # Advance past delay
        headless_loop.advance_time(1.5)
        headless_loop.step(timeout=0)
        assert called == ['a']

    def test_clear_callbacks(self, headless_loop, backend_name: str):
        """Headless loop should support clearing all callbacks."""
        headless_loop.schedule_once(lambda dt: None, delay=1.0)
        headless_loop.schedule_interval(lambda dt: None, interval=0.1)
        headless_loop.call_soon(lambda: None)

        assert headless_loop.pending_callback_count > 0
        headless_loop.clear_callbacks()
        assert headless_loop.pending_callback_count == 0
