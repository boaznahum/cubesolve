"""
Tests for AnimationBackend protocol implementation.

These tests verify that backend animation implementations correctly
implement the AnimationBackend protocol.
"""

import pytest

from cube.gui.protocols import AnimationBackend
from cube.gui.factory import BackendRegistry


class TestAnimationBackendProtocol:
    """Tests for the AnimationBackend protocol."""

    def test_animation_supported_property(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend must indicate if animation is supported."""
        if animation is None:
            # Backend doesn't support animation - that's valid
            assert not BackendRegistry.supports_animation(backend_name)
        else:
            assert hasattr(animation, 'supported')
            assert isinstance(animation.supported, bool)

    def test_animation_running_property(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend must have running property."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        assert hasattr(animation, 'running')
        assert isinstance(animation.running, bool)

    def test_animation_not_running_initially(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend should not be running initially."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        assert not animation.running

    def test_animation_speed_property(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend must have speed property."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        assert hasattr(animation, 'speed')
        assert isinstance(animation.speed, (int, float))
        assert animation.speed > 0

    def test_animation_speed_setter(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend.speed should be settable."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        original = animation.speed
        animation.speed = 2.0
        assert animation.speed == 2.0
        animation.speed = original

    def test_cancel_when_not_running(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend.cancel() should be safe when not running."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        # Should not raise
        animation.cancel()

    def test_pause_resume_when_not_running(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend.pause()/resume() should be safe when not running."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        # Should not raise
        animation.pause()
        animation.resume()

    def test_skip_when_not_running(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend.skip() should be safe when not running."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        # Should not raise
        animation.skip()


class TestAnimationBackendWithCube:
    """Tests for AnimationBackend with actual cube operations.

    These tests require animation support and are marked accordingly.
    """

    @pytest.fixture
    def cube(self):
        """Create a cube for animation testing."""
        from cube.model.cube import Cube
        return Cube(3)

    @pytest.mark.requires_animation
    def test_run_animation_method_exists(self, animation: AnimationBackend | None, backend_name: str):
        """AnimationBackend must have run_animation method."""
        if animation is None:
            pytest.skip("Backend doesn't support animation")

        assert hasattr(animation, 'run_animation')
        assert callable(animation.run_animation)

    # Note: Full animation tests require integration with event loop
    # and are more complex. These basic protocol tests just verify
    # the interface exists and is callable.
