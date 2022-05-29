from algs import Algs
from cube import Cube


def test1():

    #Faild on [5:5]B
    #[{good} [3:3]R [3:4]D S [2:2]L]

    cube = Cube(6)

    alg = Algs.R[3:3] + Algs.D[3:4] + Algs.S + Algs.L[2:2]
    print(alg)
    alg.play(cube)

    alg = Algs.B[5:5]
    print(alg)
    alg.play(cube)

def test2():

    #Faild on [5:5]B
    #[{good} [3:3]R [3:4]D S [2:2]L]

    cube = Cube(7)

    alg = Algs.R[3:3]
    print(alg)
    alg.play(cube)



if __name__ == '__main__':
    test2()