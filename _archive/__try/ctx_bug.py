import sys
from contextlib import contextmanager, nullcontext


class MyException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@contextmanager
def annotate():
    try:
        yield None
    finally:
        return

#    yield from base(enable)

def annotate2():
    return nullcontext()


def main():
    try:
        with annotate():
            raise MyException()

    except MyException:
        print("Good, Caught exception")
        sys.exit(0)

    print("How did I get here ???")
    sys.exit(1)


if __name__ == '__main__':
    main()
