# On this branch - redo

L1 Edges aggressive test passed

# in ahead commits
All L1 tests fail
tests_wip/big_lbl_2/test_lbl_big_cube_full_solver.py

fails:
    cube_size = 6, scramble_name = 'rnd_137658025', scramble_seed = 137658025
    cube_size = 4, scramble_name = 'rnd_1794630359', scramble_seed = 1794630359
    cube_size = 6, scramble_name = 'rnd_1838264046', scramble_seed = 1838264046

reproduced when we hardcoded the seeds

L1 solver: passed
L2: Solver: fails