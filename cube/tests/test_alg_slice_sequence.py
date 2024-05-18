"""
Test that R[1, 2, 3]  is supported.
This test was written due to pyright warning that only slice object is uspported
"""
from cube.algs import Algs


def main():

    R = Algs.R

    Rx = R[1, 2, 3]

    # first, it should be failed in str
    print(Rx)


if __name__ == '__main__':
    main()