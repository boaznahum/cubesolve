from cube.tests import test_simplify, bug_sanity_on, test_boy, test_cube, test_cube_aggresive, test_indexes_slices, \
    test_scramble_repeatable
from cube.tests.test_utils import run_all_tests


def main():
    run_all_tests([
        test_simplify.tests,
        bug_sanity_on.tests,
        test_boy.tests,
        test_cube.tests,
        test_indexes_slices.tests,
        test_scramble_repeatable.tests,

        # last one
        test_cube_aggresive.tests,

    ])

    print("=============================================")
    print("All tests passed.")


if __name__ == '__main__':
    main()
