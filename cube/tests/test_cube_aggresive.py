from typing import Any

from cube import config
from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube.operator.cube_operator import Operator


def _scramble(op: Operator, _scramble_key: Any, _n=None):
    op.reset()

    _alg = Algs.scramble(op.cube.size, _scramble_key, _n)

    print(f"Running scramble, key={_scramble_key}, n={_n}, alg={_alg}")

    op.play(_alg, False)


def main():

    app = AbstractApp.create_non_default(config.CUBE_SIZE)

    debug = False

    for size in [app.cube.size, app.cube.size + 1]:

        app.reset(cube_size=size)

        app.run_tests(config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START,
                      config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS // 2,
                      debug=debug)


if __name__ == '__main__':
    main()
