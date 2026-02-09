size 6x6
Scramble 0
Solve L1

D:\dev\code\python\cubesolve3\.venv\Scripts\python.exe D:\dev\code\python\cubesolve3\src\cube\main_pyglet2.py 
Running scramble, cube size=6 key=0, type(scramble_key)=<class 'int'>, n=None, alg={random-scrm597[597]}
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [YELLOW@F, RED@L, WHITE@U, BLUE@R, BLUE@D, YELLOW@B]
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [RED@L, WHITE@U, BLUE@R, BLUE@D]
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [YELLOW@F, RED@L, WHITE@U, BLUE@R, BLUE@D, YELLOW@B]
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [RED@L, WHITE@U, BLUE@R, BLUE@D]
DEBUG: Big-LBL: Solving Layer 1 centers (WHITE face only)
DEBUG: Big-LBL:NxNCenters: _do_faces: WHITE@WHITE@U
DEBUG: Big-LBL:NxNCenters: Need to work on WHITE@U
DEBUG: Big-LBL:NxNCenters: Working on face WHITE@U
DEBUG: Big-LBL:NxNCenters:CommonOp: Need to bring  WHITE@U to F
DEBUG: Big-LBL:NxNCenters: Need to bring ORANGE@L to up
DEBUG: Big-LBL:NxNCenters:   No blocks found for WHITE on U
DEBUG: Big-LBL:NxNCenters: Need to bring WHITE@L to up
DEBUG: Big-LBL:NxNCenters:   Found 8 blocks on U, 0 larger than 1x1
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from UPoint(row=0, col=1)->Point(row=0, col=1) to F (rotation=2)
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from UPoint(row=1, col=2)->Point(row=1, col=2) to F (rotation=0)
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from UPoint(row=1, col=2)->Point(row=1, col=2) to F (rotation=1)
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from UPoint(row=3, col=0)->Point(row=3, col=0) to F (rotation=0)
DEBUG: Big-LBL:NxNCenters: Need to bring GREEN@L to up
DEBUG: Big-LBL:NxNCenters:   Found 6 blocks on U, 1 larger than 1x1
DEBUG: Big-LBL:NxNCenters:     ✓ Block 2x1 (2 pieces) from UPoint(row=2, col=3)->Point(row=3, col=3) to F (rotation=0)
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from UPoint(row=1, col=0)->Point(row=1, col=0) to F (rotation=0)
DEBUG: Big-LBL:NxNCenters: After working on WHITE@F work_done=True, solved=False
DEBUG: Big-LBL:NxNCenters: _do_faces: WHITE@WHITE@F
DEBUG: Big-LBL:NxNCenters: For face WHITE@F, No color WHITE available on  BLUE@L, ORANGE@U, RED@R, ORANGE@D}
DEBUG: Big-LBL:NxNCenters: _do_faces: WHITE@WHITE@F
DEBUG: Big-LBL:NxNCenters: Need to work on WHITE@F
DEBUG: Big-LBL:NxNCenters: Working on face WHITE@F
DEBUG: Big-LBL:NxNCenters:   Found 4 blocks on B, 0 larger than 1x1
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from BPoint(row=0, col=0)->Point(row=0, col=0) to F (rotation=2)
DEBUG: Big-LBL:NxNCenters:     ✓ Block 1x1 (1 pieces) from BPoint(row=0, col=2)->Point(row=0, col=2) to F (rotation=2)
DEBUG: Big-LBL:NxNCenters: After working on WHITE@F work_done=True, solved=True
DEBUG: Big-LBL: Solving Layer 1 edges (WHITE face only)
DEBUG: Big-LBL:NxNEdges: ── Doing face WHITE edges ──
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [WHITE@F, BLUE@L, ORANGE@U, RED@R, ORANGE@D, GREEN@B]
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [BLUE@L, ORANGE@U, RED@R, ORANGE@D]
Traceback (most recent call last):
  File "D:\dev\code\python\cubesolve3\src\cube\presentation\gui\backends\pyglet2\PygletAppWindow.py", line 650, in inject_command
    result = command.execute(ctx)
  File "D:\dev\code\python\cubesolve3\src\cube\presentation\gui\commands\concrete.py", line 133, in execute
    ctx.slv.solve(what=self.step, animation=False)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\AbstractSolver.py", line 90, in solve
    result = self._solve_impl(what)
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\direct\lbl\LayerByLayerNxNSolver.py", line 265, in _solve_impl
    return self._solve_impl2(what)
           ~~~~~~~~~~~~~~~~~^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\direct\lbl\LayerByLayerNxNSolver.py", line 308, in _solve_impl2
    self._solve_layer1_edges(th)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\direct\lbl\LayerByLayerNxNSolver.py", line 561, in _solve_layer1_edges
    self._nxn_edges.solve_face_edges(l1_tracker)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "D:\dev\code\python\cubesolve3\src\cube\domain\solver\common\big_cube\NxNEdges.py", line 91, in solve_face_edges
    assert len(target_edges_by_color) == 4, \
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Expected 4 edges with WHITE, found 5 ['FD [BLUE, WHITE]', 'BD [WHITE, GREEN]', 'BR [WHITE, GREEN]', 'BL [ORANGE, WHITE]', 'BU [ORANGE, WHITE]']
is boy=True {<FaceName.R: 'R'>: RED, <FaceName.L: 'L'>: ORANGE, <FaceName.F: 'F'>: WHITE, <FaceName.B: 'B'>: YELLOW, <FaceName.D: 'D'>: GREEN, <FaceName.U: 'U'>: BLUE}
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [WHITE@F, BLUE@L, ORANGE@U, RED@R, ORANGE@D, GREEN@B]
DEBUG: Big-LBL:NxNCentersFaceTrackers: _find_face_with_max_colors: [BLUE@L, ORANGE@U, RED@R, ORANGE@D]
