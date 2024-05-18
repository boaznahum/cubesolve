from collections.abc import Collection
from typing import Callable

from cube import config

Test = Callable[[], None]
Tests = Collection[Test]


def run_tests(tests: Tests):
    # module = tests.__module__
    # print(f"=============== Running tests from {module} ===============")
    for test in tests:
        # If the test doesn't set it, then the least make is known and repeatable
        config.CHECK_CUBE_SANITY = False
        test()
    # print(f"=============== Finish running tests from {module} ===============")


def run_all_tests(all_tests: Collection[Tests]):
    for tests in all_tests:
        run_tests(tests)
