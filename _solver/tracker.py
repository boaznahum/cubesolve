from collections.abc import Iterable, Sequence
from typing import TypeVar, Generic

from cube import Cube
from elements import Part, Edge

T = TypeVar("T", bound=Part)


class PartTracker(Generic[T]):
    """
    Track a part olor id, even if algorithm change its location, this
    will return the required location(where it should be located on cube) and it's actual location
    """
    __slots__ = ["_color_id", "_actual",
                 "_required",
                 "_cube"]

    def __init__(self, part: T) -> None:
        super().__init__()
        self._color_id = part.colors_id_by_pos
        self._actual: T | None = None
        self._required: T = part
        self._cube: Cube = part.cube

    @property
    def required(self) -> T:
        """
        The position where this part should be located
        :return:
        """

        if not self._required or self._required.colors_id_by_pos != self._color_id:
            self._required = self._cube.find_corner_by_pos_colors(self._color_id)
        return self._required

    @property
    def actual(self) -> T:
        """
        The current location, where part with the given color is located
        :return:
        """

        if not self._actual or self._actual.colors_id_by_color != self._color_id:
            self._actual = self._cube.find_part_by_colors(self._color_id)
        return self._actual

    @property
    def match(self) -> bool:
        """
        Edge is in required match faces
        :return:
        """
        return self.required.match_faces

    def __str__(self):
        if self.match:
            s = "+"
        else:
            s = "!"
        return s + " " + str(self.actual) + "-->" + str(self.required)

    def __repr__(self):
        return self.__str__()


class EdgeTracker(PartTracker[Edge]):

    def __init__(self, edge: Edge) -> None:
        super().__init__(edge)

    @staticmethod
    def of(edge: Edge) -> "EdgeTracker":
        """
        Given a edge, tracks its position(not actual) id
        :param edge:
        :return:
        """
        return EdgeTracker(edge)

    @staticmethod
    def of_many(edges: Iterable[Edge]) -> Sequence["EdgeTracker"]:
        return [EdgeTracker.of(e) for e in edges]
