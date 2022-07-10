from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import Generic

from cube.model.cube import Cube, CubeSupplier
from cube.model.cube_queries import CubeQueries
from cube.model import PartColorsID
from cube.model import TPartType, Edge, Corner


class PartTracker(Generic[TPartType]):
    """
    Track a part color id, even if algorithm change its location, this
    will return the required location(where it should be located on cube) and it's actual location
    """
    __slots__ = ["_color_id", "_actual",
                 "_required",
                 "_cube"]

    def __init__(self, cube: CubeSupplier, color_id: PartColorsID) -> None:
        super().__init__()
        self._color_id = color_id
        self._actual: TPartType | None = None
        self._required: TPartType | None = None
        self._cube: Cube = cube.cube

    @property
    def position(self) -> TPartType:
        """
        The position where this part should be located.
        Given the color it in ctr, locate the part where this color should be
        Position can be changed if faces are changed, Whole and slice rotations
        :return:
        """

        if not self._required or self._required.colors_id_by_pos != self._color_id:
            self._required = CubeQueries.find_part_by_position(self._search_in(), self._color_id)

        return self._required

    @property
    def actual(self) -> TPartType:
        """
        The current location, where part with the given color is located
        :return:
        """

        if not self._actual or self._actual.colors_id_by_color != self._color_id:
            self._actual = CubeQueries.find_part_by_color(self._search_in(), self._color_id)

        return self._actual

    @property
    def match(self) -> bool:
        """
        Edge is in required position and correctly oriented
        :return:
        """
        return self.position.match_faces

    @property
    def in_position(self):
        """
        :return: true if part in position(ignoring orientation), position id same as color id, actual == required
        """
        return self.position.in_position

    @abstractmethod
    def _search_in(self) -> Iterable[TPartType]:
        ...

    def __str__(self):
        if self.match:
            s = "+"
        else:
            s = "!"
        return s + " " + str(self.actual) + "-->" + str(self.position)

    def __repr__(self):
        return self.__str__()


class EdgeTracker(PartTracker[Edge]):

    def _search_in(self) -> Iterable[Edge]:
        return self._cube.edges

    def __init__(self, cube: CubeSupplier, color_id: PartColorsID) -> None:
        super().__init__(cube, color_id)

    @staticmethod
    def of_position(edge: Edge) -> "EdgeTracker":
        """
        Given an edge, tracks its position id
        :param edge:
        :return:
        """
        return EdgeTracker(edge.cube, edge.position_id)

    @staticmethod
    def of_color(cube: CubeSupplier, color_id: PartColorsID):
        """
        Given a color_id ID, locate the part. position or actual
        :param color_id:
        :param cube:
        :return:
        """
        return EdgeTracker(cube, color_id)

    @staticmethod
    def of_many_by_position(edges: Iterable[Edge]) -> Sequence["EdgeTracker"]:
        return [EdgeTracker.of_position(e) for e in edges]


class CornerTracker(PartTracker[Corner]):

    def __init__(self, cube: Cube, color_id: PartColorsID) -> None:
        super().__init__(cube, color_id)

    @staticmethod
    def of_position(corner: Corner) -> "CornerTracker":
        """
        Given a corner, tracks its position(not actual) id
        Create a tracker from position id
        :param corner:
        :return:
        """
        return CornerTracker(corner.cube, corner.colors_id_by_pos)

    @staticmethod
    def of_many_by_position(corners: Iterable[Corner]) -> Sequence["CornerTracker"]:
        return [CornerTracker.of_position(c) for c in corners]

    def _search_in(self) -> Iterable[Corner]:
        return self._cube.corners
