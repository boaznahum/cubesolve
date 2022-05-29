from algs import Algs
from cube import Cube


def test():

    #Faild on [5:5]B
    #[{good} [3:3]R [3:4]D S [2:2]L]

    alg = alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]  + Algs.B[5:5]

    print(alg)

    cube = Cube(6)

    alg.play(cube)


if __name__ == '__main__':
    test()