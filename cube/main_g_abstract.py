from abc import abstractmethod
from typing import Callable

import pyglet  # type: ignore

from .app_state import ApplicationAndViewState
from .model.cube import Cube
from .operator.cube_operator import Operator
from .solver import Solver
from .viewer.viewer_g import GCubeViewer


class AbstractApp:
    def __init__(self):
        pass

    @property
    @abstractmethod
    def op(self) -> Operator:
        raise NotImplementedError

    @property
    @abstractmethod
    def vs(self) -> ApplicationAndViewState:
        raise NotImplementedError

    @property
    @abstractmethod
    def slv(self) -> Solver:
        raise NotImplementedError

    @property
    @abstractmethod
    def cube(self) -> Cube:
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError


class AbstractWindow(pyglet.window.Window):
    #
    # @abstractmethod
    # def set_animation(self, an: Animation | None):
    #     pass

    # @property
    # @abstractmethod
    # def animation_running(self):
    #     """
    #     Indicate that the animation hook start and animation
    #     Usually it is enough to check if Operator:is_animation_running
    #     because it invokes the animation hook that invokes the windows
    #     :return:
    #     """
    #     pass

    @abstractmethod
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
