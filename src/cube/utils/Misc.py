import sys


def _is_module_imported(module_name):


    return module_name in sys.modules


class Misc:

    @staticmethod
    def assert_pyglet_not_imported():
        assert not _is_module_imported('pyglet'), 'Pyglet imported'
