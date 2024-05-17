from cube.algs import Algs
from cube.app.abstract_ap import AbstractApp
from cube import config


def main() -> None:

    for sanity in [True, False]:
        config.CHECK_CUBE_SANITY = sanity
        print("Sanity:", sanity)
        test_for_size(3)
        test_for_size(5)

    config.CHECK_CUBE_SANITY = True

    print("All tests passed.")


def test_for_size(n):
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


if __name__ == '__main__':
    main()
