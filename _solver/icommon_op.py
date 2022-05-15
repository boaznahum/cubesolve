from abc import ABC, abstractmethod

from cube_face import Face


class ICommon(ABC):

    @property
    @abstractmethod
    def white_face(self) -> Face:
        """
        when ever we say 'white' we mean color of start color
        """
