from typing import Iterable

from cube.domain.model.Color import Color


class ModelHelper:

    @staticmethod
    def color_id_to_name(color_id: Iterable[Color]) -> str:
        """

        :param color_id:
        :return: COLOR1/COLO2
        """

        s_colors = ""

        for e in color_id:
            s_colors += str(e.long) + "/"

        # remove last /
        s_colors = s_colors[0:-1]

        return s_colors
