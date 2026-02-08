I wna to start a new task, very diffuclt one

The problem - big lbl cube solver for even cube
in even cube there are no fixed centers, the color is according some middle piece 
in the center of the cube, becuase this is even cibe, it is not pyshiclly fixed and it can be moved
it can also moved in odd cube, but becuase it alwasy exist this piece we can see that this is the center of the cube
why we caanot assign this task to a piece if eve n cube, becuase it might that the required center has no piece if the face color

(actually we need to prove tat there is such a case, for now assume that there)
So our solution is based on Face trackers and cheating the cube,

why cube solve face,  because for example when cube edge ask itslef to which face color i belong,
it asked this arbitary piece, and maybe there are two faces with same color and this is an impossib;e state
so solver falls

lets start from cheating the cube,
lets add a protocl to model FacesColorsProvider that given face name give its color
now cube has a method with_faces_color_provider(cp: FacesColorsProvider) which is a context manager
the cube gooes to all its faces and call set_face_provider, which is also a context manager
thew face context manger set the new provider rememebr the previouse or none, it call a method that reset
things after face color changes because from now the logic fo face color is changed
now the method of face color check this provider , if not none it call it to provide the face color

FacesTrackerHolder implements this protocol
so when we start to solve a cube in big lbl solver, after we set up FacesTrackerHolder then we also
start this context manager, maybe we can do it in same method, please check

so this work along as we dont move pieces of centers, becuase we might move piece that contains 
the face tracker marker, the marker that tells the tracker that this is the piece it track,

when we move pieces ?
1. when solving centers, using communicator
2. when optimize before solvig rows trying to check if the face center can be moved to to optimze solver, doing a slice rotationg
3. smae optimization when trying to optimzie a single row

so what we need to do, we eed to tell the faces taracke using again ac ontext manager that we might move
a pice that contains the marker, 
we assume that in this context we dont itend to realyy change the face color, and it if happens is accident, it is not that we do a whole 
cube rotating in which we realy mean also to chnagemove the face

so what does contect does ?
it remeber on whicg pysical face it track
and when context finshed it chak if the mark moved to other face, if yes, then it choose other piece on the face
it supposed to track ad MOVE the marker to it

this and the face color charting suppose to solve th evevn cube case

I want you to think hard !!! plan, make sure the problem is clear and start to implement
then run lbl solver tests for even cube , see tests/solvers/wip/big_lbl, you can learn how solvers tests are implemented in
tests/solvers

