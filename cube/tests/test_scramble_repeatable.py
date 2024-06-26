#
# Check that random scramble is repeatable
#
from cube.app.abstract_ap import AbstractApp
from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver, Solvers
from cube.tests.test_utils import Tests


def main() -> None:

    size = 6

    app = AbstractApp.create_non_default(cube_size=size)

    cube = Cube(size=size)

    vs = ApplicationAndViewState()
    op: Operator = Operator(cube, vs)
    solver: Solver = Solvers.default(op)

    scramble_key = 203
    alg1 = app.scramble(scramble_key, None, False, True)
    alg2 = app.scramble(scramble_key, None, False, True)


    print(f"{alg1.simplify().count()}")
    print(f"{alg2.simplify().count()}")

    alg1.play(cube)
    st1 = cube.cqr.get_sate()
    cube.reset()
    alg2.play(cube)

    assert cube.cqr.compare_state(st1)
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

    assert  s1 == s2


tests: Tests = [main]


if __name__ == '__main__':
    main()

