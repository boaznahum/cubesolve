# On this branch - redo

L1 Edges aggressive test passed
L1 Aggressive Passed
L2 from aggressive 4 fails:  
    cube_size = 6, scramble_name = 'rnd_1937644683', scramble_seed = 1937644683
    cube_size = 4, scramble_name = 'seed_124826159', scramble_seed = 124826159
    cube_size = 4, scramble_name = 'seed_1794630359', scramble_seed = 1794630359
    ube_size = 6, scramble_name = 'seed_1838264046', scramble_seed = 1838264046

Removed the code in cube.domain.solver.direct.lbl._LBLSlices._LBLSlices._find_best_pre_alignment
# this increase the number of failures

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