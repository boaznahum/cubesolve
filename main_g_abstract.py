from abc import abstractmethod
from typing import Callable

import pyglet  # type: ignore

from app_state import ApplicationAndViewState
from cube_operator import Operator
from main_g_app import AbstractApp
from model.cube import Cube
from solver import Solver
from viewer.viewer_g import GCubeViewer


class Animation:

    def __init__(self) -> None:
        super().__init__()
        self.done: bool = False
        self._animation_update_only: Callable[[], None] | None = None
        self._animation_draw_only: Callable[[], None] | None = None
        self._animation_cleanup: Callable[[], None] | None = None
        self.delay = 1 / 20.

    def update_gui_elements(self):
        if self._animation_update_only:
            self._animation_update_only()

    def draw(self):
        if self._animation_draw_only:
            self._animation_draw_only()

    def cleanup(self):
        if self._animation_cleanup:
            self._animation_cleanup()


class AbstractWindow(pyglet.window.Window):

    @abstractmethod
    def set_animation(self, an: Animation | None):
        pass

    def set_annotation_text(self, text1: str | None, text2: str | None):
        pass

    @abstractmethod
    def update_gui_elements(self):
        pass

    @property
    @abstractmethod
    def app(self) -> AbstractApp:
        pass

    @property
    @abstractmethod
    def viewer(self) -> GCubeViewer:
        pass
