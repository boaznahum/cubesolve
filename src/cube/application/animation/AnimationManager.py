from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, TypeAlias

from cube.application.protocols import AnimatableViewer, EventLoop
from cube.application.state import ApplicationAndViewState
from cube.domain import algs
from cube.domain.algs import SimpleAlg

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

OpProtocol: TypeAlias = Callable[[algs.Alg, bool], None]


class Animation:

    def __init__(self) -> None:
        super().__init__()
        self.done: bool = False
        self._animation_update_only: Callable[[], bool] | None = None
        self._animation_draw_only: Callable[[], None] | None = None
        self._animation_cleanup: Callable[[], None] | None = None
        self.delay = 1 / 20.

    def update_gui_elements(self) -> bool:
        if self._animation_update_only:
            return self._animation_update_only()
        else:
            return False

    def draw(self):
        if self._animation_draw_only:
            self._animation_draw_only()

    def cleanup(self):
        if self._animation_cleanup:
            self._animation_cleanup()


class AnimationWindow:
    """A window that accepts animation operations."""

    @property
    @abstractmethod
    def viewer(self) -> AnimatableViewer | None:
        """Get the viewer for animation.

        Returns:
            AnimatableViewer if available, None for backends without GUI.
        """
        pass

    @abstractmethod
    def update_gui_elements(self) -> None:
        """Update GUI elements after state changes."""
        pass


class AnimationManager(ABC):
    __slots__ = ["_window", "_current_animation", "_vs", "_event_loop"]

    def __init__(self,
                 vs: ApplicationAndViewState,
                 event_loop: EventLoop | None = None):
        self._vs = vs
        self._window: AnimationWindow | None = None
        self._current_animation: Animation | None = None
        self._event_loop: EventLoop | None = event_loop

    def set_window(self, window: AnimationWindow):
        """
        PATCH PATCH PATCH
        :param window:
        :return:
        """
        self._window = window

    def set_event_loop(self, event_loop: EventLoop):
        """Set the event loop for animation scheduling."""
        self._event_loop = event_loop

    # noinspection PyMethodMayBeStatic
    def run_animation(self, cube: Cube, op: OpProtocol, alg: SimpleAlg):
        assert self._window
        if self._event_loop is None:
            raise RuntimeError("EventLoop is required for animation. Call set_event_loop() first.")

        # Check if viewer is available (backends without GUI support won't have one)
        try:
            viewer = self._window.viewer
        except RuntimeError:
            # Viewer not initialized - skip animation, execute directly
            op(alg, False)
            return

        # Skip animation if no viewer at all (headless or console backends)
        # Note: ModernGLCubeViewer is NOT None, so it will proceed with animation
        if viewer is None:
            op(alg, False)
            return

        _op_and_play_animation(self._window,
                               cube,
                               self._set_animation,
                               viewer,
                               self._vs,
                               self._event_loop,
                               op, False, alg)

    def animation_running(self) -> Animation | None:
        """
        Indicate that the animation hook start and animation _set_animation_was called
        todo: why run_animation is not enough ?
        Usually it is enough to check if Operator:is_animation_running
        because it invokes the animation hook that invokes the windows
        :return:
        """

        return self._current_animation

    def update_gui_elements(self):
        an = self._current_animation
        if an:
            an.update_gui_elements()

    def draw(self):
        an = self._current_animation
        if an:
            an.draw()

    def _set_animation(self, animation: Animation | None):

        if animation:
            assert not self._current_animation

        self._current_animation = animation


def _op_and_play_animation(
    window: AnimationWindow,
    cube: "Cube",
    animation_sink: Callable[[Animation | None], None],
    viewer: AnimatableViewer,
    vs: ApplicationAndViewState,
    event_loop: EventLoop,
    operator: OpProtocol,
    inv: bool,
    alg: algs.SimpleAlg,
) -> None:
    """Run animation for an algorithm.

    This is called by AnimationManager to animate a cube operation.
    The viewer creates the animation (polymorphically - it knows how to
    render its geometry), and this function handles scheduling and timing.

    Args:
        window: The window for GUI updates
        cube: The cube model
        animation_sink: Callback to set/clear current animation
        viewer: The viewer (implements AnimatableViewer protocol)
        vs: Application view state
        event_loop: Event loop for scheduling
        operator: The operator function to execute the alg
        inv: Whether to invert the algorithm
        alg: The algorithm to animate
    """
    if event_loop.has_exit:
        return  # maybe long alg is still running

    if isinstance(alg, algs.AnnotationAlg):
        operator(alg, inv)
        window.update_gui_elements()
        event_loop.notify()
        return

    if inv:
        _alg = alg.inv().simplify()
        assert isinstance(_alg, algs.SimpleAlg)
        alg = _alg

    if not isinstance(alg, algs.AnimationAbleAlg):
        vs.debug(True, f"{alg} is not animation-able")
        operator(alg, False)
        return

    # Single step mode handling
    if vs.single_step_mode:
        vs.paused_on_single_step_mode = alg

        def _update_gui(_: float) -> None:
            window.update_gui_elements()

        try:
            event_loop.schedule_once(_update_gui, 0)

            vs.single_step_mode_stop_pressed = False
            while (not event_loop.has_exit and (vs.paused_on_single_step_mode and vs.single_step_mode)
                   and not vs.single_step_mode_stop_pressed):
                timeout = event_loop.idle()
                event_loop.step(timeout)
        finally:
            vs.paused_on_single_step_mode = None

        if vs.single_step_mode_stop_pressed:
            return

    # Skip animation for zero rotation
    if alg.n % 4 == 0:
        vs.debug(True, f"{alg} is zero rotating, can't animate")
        operator(alg, False)
        return

    # Create animation using the AnimatableViewer protocol
    # The viewer decides HOW to animate (display lists, VBOs, etc.)
    animation: Animation = viewer.create_animation(alg, vs)
    delay: float = animation.delay

    # animation.draw() is called from window.on_draw
    animation_sink(animation)

    def _update(_):
        # Advance to next animation step
        animation.update_gui_elements()
        #     vs.skip_next_on_draw = "animation update no change"  # display flicks

    try:
        # If you read event loop, only handled events cause to redraw so after _update, window_on_draw will draw the
        # animation if any other model state is changed, it will update during keyboard handling,
        # and animation.update_gui_elements() will be re-called (is it a problem?) and then redraw again
        # window.on_redraw
        event_loop.schedule_interval(_update, delay)

        # copied from EventLoop#run
        while not event_loop.has_exit and not animation.done:
            timeout = event_loop.idle()  # this will trigger on_draw
            event_loop.step(timeout)

        if event_loop.has_exit:
            return

        event_loop.unschedule(_update)

        # while not animation.done:
        #     window.on_draw()
        #     time.sleep(delay)

        animation.cleanup()
        #     if animation.done:
        #         break  # don't sleep !!!
        #     window.flip()

    finally:
        animation_sink(None)

    operator(alg, False)

    # most important !!! otherwise animation jumps
    # not clear why
    window.update_gui_elements()
