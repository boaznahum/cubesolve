# Trying to make solver work with simple f5 tracer

src/cube/config/face_tracer_config.py:21

use_simple_f5_tracker=True

SOLVER_SANITY_CHECK_IS_A_BOY = True # NON-DEFAULT

# focus on beginner 

## Currently

The cube messed up, missing faces
size 4x4
Scramble 2
Solve

Running scramble, cube size=4 key=2, type(scramble_key)=<class 'int'>, n=None, alg={scrmbl2/428[428]}
-[Or]-
-[Gr]-
[L ❌❌][Re][R ❌❌]
-[Bl]-


Traceback (most recent call last):
  File "D:\dev\code\python\cubesolve3\src\cube\presentation\gui\backends\pyglet2\PygletAppWindow.py", line 650, in inject_command
    result = command.execute(ctx)
  File "D:\dev\code\python\cubesolve3\src\cube\presentation\gui\commands\concrete.py", line 123, in execute
    ctx.slv.solve(animation=False)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\AbstractSolver.py", line 90, in solve
    result = self._solve_impl(what)
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\NxNSolverOrchestrator.py", line 123, in _solve_impl
    return self._solve(what)
           ~~~~~~~~~~~^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\NxNSolverOrchestrator.py", line 188, in _solve
    reduction_results = self._reducer.reduce(debug)
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\reducers\beginner\BeginnerReducer.py", line 85, in reduce
    self.solve_centers()
    ~~~~~~~~~~~~~~~~~~^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\reducers\beginner\BeginnerReducer.py", line 97, in solve_centers
    centers.solve(holder)
    ~~~~~~~~~~~~~^^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\big_cube\NxNCenters.py", line 202, in solve
    self._solve(holder)
    ~~~~~~~~~~~^^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\big_cube\NxNCenters.py", line 278, in _solve
    if not self._do_faces(faces, False, False):
           ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\big_cube\NxNCenters.py", line 300, in _do_faces
    self._asserts_is_boy(faces)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\big_cube\NxNCenters.py", line 328, in _asserts_is_boy
    assert is_boy
           ^^^^^^
AssertionError