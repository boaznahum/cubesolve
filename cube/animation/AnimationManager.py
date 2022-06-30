from abc import ABC


class AnimationManager(ABC):

    def animation_running(self):
        """
        Indicate that manager start to run animation
        :return:
        """
        raise NotImplementedError



