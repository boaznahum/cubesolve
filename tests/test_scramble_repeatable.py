#
# Check that random scramble is repeatable
#
from algs import Algs
from app_state import ApplicationAndViewState
from cube_operator import Operator
from model.cube import Cube
from model.cube_queries import CubeQueries
from solver import Solver


def main():
    size = 6

    cube = Cube(size=size)

    vs = ApplicationAndViewState()
    op: Operator = Operator(cube, vs)
    solver: Solver = Solver(op)

    alg1 = Algs.scramble(cube.size, 4)
    alg2 = Algs.scramble(cube.size, 4)

    print(f"{alg1.simplify().count()}")
    print(f"{alg2.simplify().count()}")

    alg1.play(cube)
    st1 = CubeQueries.get_sate(cube)
    cube.reset()
    alg2.play(cube)

    assert CubeQueries.compare_state(cube, st1)
    print("Cube same state after alg1/alg2")

    op.reset()
    alg1.play(cube)
    solver.solve(debug=False)
    s1 = op.count

    op.reset()
    alg2.play(cube)
    solver.solve(debug=False)
    s2 = op.count

    print(f"Solve 1 count: {s1}, Solve 2 count {s2}")


if __name__ == '__main__':
    main()

