from typing import Iterable

from .cube_boy import color2long, Color


class ModelHelper:

    @staticmethod
    def color_id_to_name(id: Iterable[Color]) -> str:
        """

        :param id:
        :return: COLOR1/COLO2
        """

        s_colors = ""

        for e in id:
            s_colors += str(color2long(e).value) + "/"

        s_colors = s_colors[0:-1]

        return s_colors
