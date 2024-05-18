from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube import config
from cube.tests.test_utils import Tests


def _test_for_size(n):
    app = AbstractApp.create_non_default(n, animation=False)
    cube = app.cube
    alg2 = Algs.scramble(cube.size, 4)
    alg2.play(cube)
    rs = app.slv.solve()
    assert cube.solved
    print("** corner swap:", rs.was_corner_swap)
    print("** even edge parity:", rs.was_even_edge_parity)
    print("** partial edge parity:", rs.was_partial_edge_parity)
    print("** count:", app.op.count)


def test1():
    for sanity in [True, False]:
        config.CHECK_CUBE_SANITY = sanity
        print("Sanity:", sanity)
        _test_for_size(3)
        _test_for_size(5)

    print("All tests passed.")


tests: Tests = [test1]

def main() -> None:
    test1()




if __name__ == '__main__':
    main()
