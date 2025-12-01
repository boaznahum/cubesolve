from abc import ABC, abstractmethod
from typing import Tuple, Collection

from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.model.Cube import Cube, FaceName, PartSlice


class AnimationAbleAlg(NSimpleAlg, ABC):

    @abstractmethod
    def get_animation_objects(self, cube: Cube) -> Tuple[FaceName, Collection[PartSlice]]:
        """

        :param cube:
        :return: The face for rotation Axis and all cube elements involved in this animation
        """
        pass
